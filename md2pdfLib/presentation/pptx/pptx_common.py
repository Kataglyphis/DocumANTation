"""Shared helpers for OOXML deck post-processing, so a fix lands in one place."""

from __future__ import annotations

import json
import re
import sys
import zipfile
from collections.abc import Callable, Iterable
from pathlib import Path

MD2PDF_ROOT = Path(__file__).resolve().parents[2]
BRAND_TOKENS = MD2PDF_ROOT / "style" / "brand.tokens.json"

# Archive part names

SLIDE_RE = re.compile(r"ppt/slides/slide\d+\.xml")
MASTER_RE = re.compile(r"ppt/slideMasters/slideMaster\d+\.xml")
THEME_RE = re.compile(r"ppt/theme/theme\d+\.xml")
LAYOUT_RE = re.compile(r"ppt/slideLayouts/slideLayout\d+\.xml")
LAYOUT_RELS_RE = re.compile(r"ppt/slideLayouts/_rels/slideLayout\d+\.xml\.rels")

# XML fragments the styling modules share

SP_RE = re.compile(r"<p:sp>.*?</p:sp>", re.S)
TXBODY_RE = re.compile(r"(<p:txBody>)(.*?)(</p:txBody>)", re.S)
TEXT_RE = re.compile(r"<a:t>(.*?)</a:t>", re.S)
# Quoted run-property values may contain ``>``, so the class cannot stop at the first one.
RPR_RE = re.compile(r"<a:rPr\b((?:[^>\"]|\"[^\"]*\")*?)(/?)>")

# Pandoc writes a space before "/>", this repo's patchers do not.
XFRM_RE = re.compile(
    r'<a:off\s+x="(-?\d+)"\s+y="(-?\d+)"\s*/>\s*<a:ext\s+cx="(\d+)"\s+cy="(\d+)"\s*/>'
)
SPTREE_CLOSE = "</p:spTree>"

_CSLD_NAME_RE = re.compile(r'<p:cSld name="([^"]+)"')
_LAYOUT_TARGET_RE = re.compile(r'Target="\.\./slideLayouts/(slideLayout\d+\.xml)"')
_MEDIA_TARGET_RE = re.compile(r'Target="\.\./media/([^"]+)"')


def layout_name(layout_xml: str) -> str:
    """The ``<p:cSld name>`` pandoc selects a layout by, or ``""`` to match nothing."""
    match = _CSLD_NAME_RE.search(layout_xml)
    return match.group(1) if match else ""


def geometry_of(fragment: str) -> tuple[int, int, int, int] | None:
    """``(x, y, cx, cy)`` in EMU from the first ``<a:xfrm>``; None means inherit."""
    found = XFRM_RE.search(fragment)
    if found is None:
        return None
    x, y, cx, cy = (int(v) for v in found.groups())
    return x, y, cx, cy


def append_shapes(xml: str, shapes: Iterable[str]) -> str | None:
    """Append *shapes* to the shape tree, None without one; literal, as re.sub eats backslashes."""
    if SPTREE_CLOSE not in xml:
        return None
    return xml.replace(SPTREE_CLOSE, f"{''.join(shapes)}{SPTREE_CLOSE}", 1)


def brand_tokens() -> dict:
    """The brand tokens from md2pdfLib/style/, the only copy the build container mounts."""
    return json.loads(BRAND_TOKENS.read_text("utf-8"))


def master_style_size(master_xml: str, style_tag: str, default: int) -> int:
    """What an unsized run in *style_tag* renders at, in hundredths of a pt, else *default*."""
    pattern = re.compile(rf"<p:{style_tag}>.*?<a:lvl1pPr\b.*?<a:defRPr\b[^>]*\bsz=\"(\d+)\"", re.S)
    match = pattern.search(master_xml)
    return int(match.group(1)) if match else default


def sized_runs(fragment: str, size: int) -> str:
    """*fragment* with every unsized run pinned to *size*; runs pandoc sized keep theirs."""
    return RPR_RE.sub(
        lambda m: (
            f'<a:rPr{m.group(1)} sz="{size}"{m.group(2)}>'
            if " sz=" not in m.group(1)
            else m.group(0)
        ),
        fragment,
    )


# Writing shapes

# The one skeleton every added shape shares, so a schema fix lands once.
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
# Edge-to-edge and vertically centred, for a one-line label on a coloured block.
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
    """One positioned ``<p:sp>`` in EMU; keyword-only so two EMU values cannot swap silently."""
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
    """Rewrite *deck* in place with *updates* merged in; other parts keep their ZipInfo."""
    with zipfile.ZipFile(deck) as z:
        infos = {i.filename: i for i in z.infolist()}
        existing = {name: z.read(name) for name in infos}
    existing.update(updates)
    with zipfile.ZipFile(deck, "w", zipfile.ZIP_DEFLATED) as z:
        for name, payload in existing.items():
            z.writestr(infos.get(name, name), payload)


class DeckParts:
    """Cached read access to a deck's slides and the layouts and master they inherit."""

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
    """Apply *transform* (None leaves a slide alone) to every slide; return how many changed."""
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
    """``{layout rels part: media targets absent}``; pandoc keeps only media slides embed."""
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
    """Run *action* on the ``<deck.pptx>`` argument; listed *errors* exit 1, others traceback."""
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
