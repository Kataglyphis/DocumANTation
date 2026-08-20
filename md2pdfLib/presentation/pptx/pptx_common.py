"""Shared helpers for OOXML deck post-processing.

Every module in this package does the same three things: name the archive parts
it cares about, read a slide together with the layout and master it inherits
from, and write a subset of parts back. Each of them used to carry its own copy
of all three -- five near-identical read-modify-write loops, four copies of the
``ppt/slides/slideN.xml`` regex, two copies of the run-sizer and of the
dangling-media scan -- so a fix to one left the others behind.

The pieces live here instead:

- :data:`SLIDE_RE` and friends: the part-name patterns, written once.
- :class:`DeckParts`: cached read access to a slide's layout and master.
- :func:`edit_slides`: the read-modify-write loop, driven by a transform.
- :func:`rewrite_zip`: the archive write.
- :func:`run_cli`: the ``<deck.pptx>``-argument entry point every module has.
"""

from __future__ import annotations

import json
import re
import sys
import zipfile
from collections.abc import Callable, Iterable
from pathlib import Path

MD2PDF_ROOT = Path(__file__).resolve().parents[2]
BRAND_TOKENS = MD2PDF_ROOT / "style" / "brand.tokens.json"

# ── archive part names ───────────────────────────────────────────────────────

SLIDE_RE = re.compile(r"ppt/slides/slide\d+\.xml")
MASTER_RE = re.compile(r"ppt/slideMasters/slideMaster\d+\.xml")
THEME_RE = re.compile(r"ppt/theme/theme\d+\.xml")
LAYOUT_RE = re.compile(r"ppt/slideLayouts/slideLayout\d+\.xml")
LAYOUT_RELS_RE = re.compile(r"ppt/slideLayouts/_rels/slideLayout\d+\.xml\.rels")

# ── XML fragments the styling modules share ──────────────────────────────────

SP_RE = re.compile(r"<p:sp>.*?</p:sp>", re.S)
TXBODY_RE = re.compile(r"(<p:txBody>)(.*?)(</p:txBody>)", re.S)
TEXT_RE = re.compile(r"<a:t>(.*?)</a:t>", re.S)
# Attribute-tolerant: a run's properties may carry quoted values containing
# ``>``, so the character class cannot simply stop at the first one.
RPR_RE = re.compile(r"<a:rPr\b((?:[^>\"]|\"[^\"]*\")*?)(/?)>")

# Whitespace-tolerant: pandoc's reference deck writes `<a:off ... />` with a
# space before the slash, this repo's own patchers write it without.
XFRM_RE = re.compile(
    r'<a:off\s+x="(-?\d+)"\s+y="(-?\d+)"\s*/>\s*<a:ext\s+cx="(\d+)"\s+cy="(\d+)"\s*/>'
)
SPTREE_CLOSE = "</p:spTree>"

_CSLD_NAME_RE = re.compile(r'<p:cSld name="([^"]+)"')
_LAYOUT_TARGET_RE = re.compile(r'Target="\.\./slideLayouts/(slideLayout\d+\.xml)"')
_MEDIA_TARGET_RE = re.compile(r'Target="\.\./media/([^"]+)"')


def layout_name(layout_xml: str) -> str:
    """The ``<p:cSld name>`` of a layout part -- how pandoc selects a layout.

    Returns ``""`` when the part carries no name, which is how both callers want
    an unresolvable layout treated: not matching any name they look for.
    """
    match = _CSLD_NAME_RE.search(layout_xml)
    return match.group(1) if match else ""


def geometry_of(fragment: str) -> tuple[int, int, int, int] | None:
    """``(x, y, cx, cy)`` in EMU from the first ``<a:xfrm>`` in *fragment*.

    ``None`` when it carries none, which for a placeholder means "inherit" --
    pandoc emits ``<p:spPr/>``, so a slide's content box is positioned by its
    layout, which often defers in turn to the master.
    """
    found = XFRM_RE.search(fragment)
    if found is None:
        return None
    x, y, cx, cy = (int(v) for v in found.groups())
    return x, y, cx, cy


def append_shapes(xml: str, shapes: Iterable[str]) -> str | None:
    """Add *shapes* just inside the shape tree's close tag; None if there is none.

    Literal substitution, never :func:`re.sub`: these shapes carry document
    content -- a code block holding ``\\int_0^\\infty``, a footline label built
    from the deck title -- and in a replacement string a backslash is an escape,
    so a regex-based version corrupts or raises on exactly that content.

    Returns:
        The slide or layout with the shapes appended, or ``None`` when it has no
        ``</p:spTree>``. Callers raise their own error for that: a part whose
        shape tree does not match would otherwise lose the shapes silently while
        still being counted as patched.
    """
    if SPTREE_CLOSE not in xml:
        return None
    return xml.replace(SPTREE_CLOSE, f"{''.join(shapes)}{SPTREE_CLOSE}", 1)


def brand_tokens() -> dict:
    """The resolved brand tokens, generated from style/brand.json.

    Read from md2pdfLib/style/ rather than the repo's style/ directory: the
    build container mounts only md2pdfLib/ and data/, so this is the only copy
    a post-processing step can reach. generate_style.py writes and --check's
    both, so they cannot drift.
    """
    return json.loads(BRAND_TOKENS.read_text("utf-8"))


def master_style_size(master_xml: str, style_tag: str, default: int) -> int:
    """The ``sz`` of *style_tag*'s level-1 run properties, in hundredths of a pt.

    What an unsized run in that role renders at. Falls back to *default* when
    the master leaves the size out, which is what PowerPoint's own built-in
    default amounts to.

    Args:
        master_xml: A slide master part.
        style_tag: ``titleStyle`` or ``bodyStyle``.
        default: The size to assume when the master declares none.
    """
    pattern = re.compile(rf"<p:{style_tag}>.*?<a:lvl1pPr\b.*?<a:defRPr\b[^>]*\bsz=\"(\d+)\"", re.S)
    match = pattern.search(master_xml)
    return int(match.group(1)) if match else default


def sized_runs(fragment: str, size: int) -> str:
    """*fragment* with every run that has no explicit size pinned to *size*.

    A run that already carries ``sz`` keeps it: pandoc sizes the runs it means
    to, and overriding those would undo its own highlighting decisions.
    """
    return RPR_RE.sub(
        lambda m: (
            f'<a:rPr{m.group(1)} sz="{size}"{m.group(2)}>'
            if " sz=" not in m.group(1)
            else m.group(0)
        ),
        fragment,
    )


# ── writing shapes ───────────────────────────────────────────────────────────

# Every shape this package adds to a deck has the same skeleton and differs only
# in the slots below. Five builders across three modules each spelled it out
# again -- the brand rectangles and text labels in make_reference.py, the code
# box in style_code.py, the slide number in finalize_deck.py -- so a schema
# mistake could be fixed in one and left in the other four.
_SHAPE = (
    '<p:sp><p:nvSpPr><p:cNvPr id="{shape_id}" name="{name}"/>'
    "{cnv_sp_pr}{nv_pr}</p:nvSpPr>"
    '<p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
    "{geometry}{fill}{line}</p:spPr>"
    "<p:txBody>{body_pr}<a:lstStyle/>{body}</p:txBody></p:sp>"
)

RECT_GEOMETRY = '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
NO_FILL = "<a:noFill/>"
NO_LINE = "<a:ln><a:noFill/></a:ln>"
# A layout's own furniture, as opposed to a placeholder PowerPoint may reflow.
USER_DRAWN = '<p:nvPr userDrawn="1"/>'
# Fills the shape's text box edge to edge and centres it vertically -- what a
# one-line label on a coloured block needs.
FLUSH_CENTERED_BODY = '<a:bodyPr anchor="ctr" lIns="0" rIns="0" tIns="0" bIns="0"/>'


def shape(
    *,
    shape_id: int,
    name: str,
    x: int,
    y: int,
    cx: int,
    cy: int,
    geometry: str = RECT_GEOMETRY,
    fill: str = NO_FILL,
    line: str = NO_LINE,
    cnv_sp_pr: str = "<p:cNvSpPr/>",
    nv_pr: str = "<p:nvPr/>",
    body_pr: str = "<a:bodyPr/>",
    body: str = "<a:p/>",
) -> str:
    """One ``<p:sp>``: a positioned shape with a geometry, a fill and a text body.

    Keyword-only, because the five call sites pass different subsets and a
    positional (x, y, cx, cy, fill, ...) tail is exactly the kind of argument
    list that silently swaps two EMU values.

    Args:
        shape_id: ``cNvPr/@id``, unique within the slide part.
        name: Human-readable shape name, as the PowerPoint selection pane shows.
        x: Left edge in EMU.
        y: Top edge in EMU.
        cx: Width in EMU.
        cy: Height in EMU.
        geometry: A ``prstGeom`` or ``custGeom`` element.
        fill: A fill element (``solidFill``, ``blipFill``, ``noFill``).
        line: An ``<a:ln>`` element.
        cnv_sp_pr: ``<p:cNvSpPr/>``, or with ``txBox="1"`` for a text box.
        nv_pr: ``<p:nvPr/>``, or :data:`USER_DRAWN` for layout furniture.
        body_pr: The text body's ``<a:bodyPr>``.
        body: The paragraphs, already serialised.
    """
    return _SHAPE.format(
        shape_id=shape_id,
        name=name,
        x=x,
        y=y,
        cx=cx,
        cy=cy,
        geometry=geometry,
        fill=fill,
        line=line,
        cnv_sp_pr=cnv_sp_pr,
        nv_pr=nv_pr,
        body_pr=body_pr,
        body=body,
    )


def rewrite_zip(deck: Path, updates: dict[str, bytes]) -> None:
    """Rewrite *deck* with *updates* merged into its existing parts.

    Reads the full archive into memory, applies the updates dict, and writes
    the result back. Compression metadata (timestamps, extra fields) is
    preserved for unmodified parts by reading their ZipInfo objects.

    Args:
        deck: Path to the .pptx file to rewrite in-place.
        updates: Mapping of archive filenames to replacement payloads.
            Only listed parts are changed; everything else is copied verbatim.
    """
    with zipfile.ZipFile(deck) as z:
        infos = {i.filename: i for i in z.infolist()}
        existing = {name: z.read(name) for name in infos}
    existing.update(updates)
    with zipfile.ZipFile(deck, "w", zipfile.ZIP_DEFLATED) as z:
        for name, payload in existing.items():
            z.writestr(infos.get(name, name), payload)


class DeckParts:
    """Cached read access to a deck's slides and the parts they inherit from.

    Resolving a slide's layout means reading its rels part, finding the layout
    target, and decoding the layout -- work that is identical for every slide
    on the same layout. Each module used to redo it per slide, so a forty-slide
    deck on eleven layouts paid for it forty times, three passes per build.
    """

    def __init__(self, archive: zipfile.ZipFile) -> None:
        self._z = archive
        self._names = set(archive.namelist())
        self._layouts: dict[str, str] = {}
        self._master: str | None = None
        self.slides = [n for n in archive.namelist() if SLIDE_RE.fullmatch(n)]
        """The slide parts, in archive order."""

    def read(self, name: str) -> str:
        """The decoded XML of archive part *name*."""
        return self._z.read(name).decode()

    def master(self) -> str:
        """The first slide master's XML, or ``""`` when the deck has none."""
        if self._master is None:
            masters = sorted(n for n in self._names if MASTER_RE.fullmatch(n))
            self._master = self.read(masters[0]) if masters else ""
        return self._master

    def layout_part(self, slide: str) -> str:
        """Archive path of *slide*'s layout part, or ``""`` if unresolvable."""
        rels = f"ppt/slides/_rels/{slide.rsplit('/', 1)[-1]}.rels"
        if rels not in self._names:
            return ""
        target = _LAYOUT_TARGET_RE.search(self.read(rels))
        if target is None:
            return ""
        part = f"ppt/slideLayouts/{target.group(1)}"
        return part if part in self._names else ""

    def layout(self, slide: str) -> str:
        """The XML of *slide*'s layout part, or ``""`` if unresolvable."""
        part = self.layout_part(slide)
        if not part:
            return ""
        if part not in self._layouts:
            self._layouts[part] = self.read(part)
        return self._layouts[part]

    def layout_name(self, slide: str) -> str:
        """The ``<p:cSld name>`` of *slide*'s layout -- how pandoc selects one."""
        return layout_name(self.layout(slide))


SlideTransform = Callable[[DeckParts, str, str], "str | None"]


def edit_slides(deck: Path, transform: SlideTransform) -> int:
    """Apply *transform* to every slide of *deck*; return how many it changed.

    The archive is rewritten once, after the scan, and only when something
    changed -- rewriting it per slide would rebuild a multi-megabyte zip on
    every hit, and rewriting it for zero changes would churn the file's
    timestamps for nothing.

    Args:
        deck: The .pptx to edit in place.
        transform: Called as ``transform(parts, slide_name, slide_xml)`` for
            each slide. Return the replacement XML, or ``None`` to leave that
            slide untouched.
    """
    with zipfile.ZipFile(deck) as z:
        parts = DeckParts(z)
        updates: dict[str, bytes] = {}
        for name in parts.slides:
            new = transform(parts, name, parts.read(name))
            if new is not None:
                updates[name] = new.encode()
        if not updates:
            return 0
    rewrite_zip(deck, updates)
    return len(updates)


def dangling_layout_media(deck: Path) -> dict[str, set[str]]:
    """``{layout rels part: media targets absent from the archive}``.

    Pandoc rebuilds ppt/media/ from what the *slides* embed, so an image only a
    layout references (the brand title background) is left behind and its
    relationship dangles. finalize_deck.py puts the known ones back and
    verify_brand.py fails the build on anything still missing -- both from this
    one scan, which they used to carry a copy of each.
    """
    offenders: dict[str, set[str]] = {}
    with zipfile.ZipFile(deck) as z:
        names = set(z.namelist())
        for name in sorted(names):
            if not LAYOUT_RELS_RE.fullmatch(name):
                continue
            missing = {
                target
                for target in _MEDIA_TARGET_RE.findall(z.read(name).decode())
                if f"ppt/media/{target}" not in names
            }
            if missing:
                offenders[name] = missing
    return offenders


def run_cli(
    action: Callable[[Path], str],
    *,
    errors: tuple[type[Exception], ...] = (),
) -> None:
    """The ``<deck.pptx>`` entry point every module in this package needs.

    Validates the single path argument, runs *action*, and prints what it
    reports. Exit codes are the conventional ones: 2 for a usage error, 1 for a
    failure, 0 for success.

    Args:
        action: Called with the deck path; returns the line to print.
        errors: Exception types to report as ``Error: <message>`` and exit 1 on,
            rather than letting them traceback. Anything not listed is a bug in
            this package, and a traceback is the right output for a bug.
    """
    if len(sys.argv) != 2:
        print(f"Usage: {Path(sys.argv[0]).name} <deck.pptx>", file=sys.stderr)
        sys.exit(2)
    deck = Path(sys.argv[1])
    if not deck.is_file():
        print(f"Error: no such deck: {deck}", file=sys.stderr)
        sys.exit(1)
    try:
        print(action(deck))
    except errors as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
