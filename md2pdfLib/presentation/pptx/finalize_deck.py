"""Finish an emitted deck: layout media, slide numbers, code boxes.

Pandoc copies slide layouts and their relationship parts verbatim from the
reference deck, but rebuilds ppt/media/ only from what the *slides* embed --
media referenced solely by a layout (the brand title background) is silently
left behind, so the layout's image relationship dangles and the title slide
loses its background depending on the viewer's tolerance for broken refs.

Pandoc also never instantiates sldNum placeholders on slides, so the
footline's slide number -- styled and positioned by the layout -- would never
render. This step runs right after pandoc, writes the missing media back in,
and injects a sldNum instance into every content slide. It only knows the
media the reference build put there (make_reference.py's constants), so an
unexpected dangling reference still fails loudly in verify_brand.py's
integrity check rather than being papered over here.

Code blocks are finished here too (style_code.py): pandoc leaves them
unboxed and at body size, which overflows the slide. Everything in this
module is unconditional -- a deck that skipped it is a broken deck, not a
less strictly checked one.

Usage:
    python md2pdfLib/presentation/pptx/finalize_deck.py <deck.pptx>
"""

from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path

try:  # imported as a package module (tests)
    from md2pdfLib.presentation.pptx.fit_titles import fit_titles
    from md2pdfLib.presentation.pptx.make_reference import (
        FOOTLINE_ACCENT_CX,
        FOOTLINE_HEIGHT_EMU,
        SEPARATOR_LAYOUTS,
        SLIDE_CX,
        SLIDE_CY,
        TITLE_BG_IMAGE,
        TITLE_BG_MEDIA,
    )
    from md2pdfLib.presentation.pptx.pptx_common import rewrite_zip
    from md2pdfLib.presentation.pptx.style_code import style_code_blocks
except ImportError:  # run as a script from its own directory (the build)
    from fit_titles import fit_titles
    from make_reference import (
        FOOTLINE_ACCENT_CX,
        FOOTLINE_HEIGHT_EMU,
        SEPARATOR_LAYOUTS,
        SLIDE_CX,
        SLIDE_CY,
        TITLE_BG_IMAGE,
        TITLE_BG_MEDIA,
    )
    from pptx_common import rewrite_zip
    from style_code import style_code_blocks

# A fixed field GUID: any stable value is valid; viewers re-evaluate the field.
_SLDNUM_FLD_ID = "{93BE9E90-0A5C-4E0B-BA7A-1EDB98A1C7DE}"


def missing_layout_media(deck: Path) -> set[str]:
    """Media targets referenced from layout rels but absent from the archive."""
    missing: set[str] = set()
    with zipfile.ZipFile(deck) as z:
        names = set(z.namelist())
        for name in names:
            if not re.fullmatch(r"ppt/slideLayouts/_rels/slideLayout\d+\.xml\.rels", name):
                continue
            for target in re.findall(r'Target="\.\./media/([^"]+)"', z.read(name).decode()):
                if f"ppt/media/{target}" not in names:
                    missing.add(f"ppt/media/{target}")
    return missing


def _content_slides(z: zipfile.ZipFile) -> dict[str, str]:
    """{slide part: its layout part} for slides on footline-bearing layouts."""
    layout_names: dict[str, str] = {}  # layout basename -> cSld name
    for name in z.namelist():
        if re.fullmatch(r"ppt/slideLayouts/slideLayout\d+\.xml", name):
            m = re.search(r'<p:cSld name="([^"]+)"', z.read(name).decode())
            if m:
                layout_names[name.rsplit("/", 1)[-1]] = m.group(1)
    result: dict[str, str] = {}
    for name in z.namelist():
        m = re.fullmatch(r"ppt/slides/_rels/(slide\d+)\.xml\.rels", name)
        if not m:
            continue
        target = re.search(
            r'Target="\.\./slideLayouts/(slideLayout\d+\.xml)"', z.read(name).decode()
        )
        if target and layout_names.get(target.group(1)) in SEPARATOR_LAYOUTS:
            result[f"ppt/slides/{m.group(1)}.xml"] = f"ppt/slideLayouts/{target.group(1)}"
    return result


def _sldnum_shape(total: int) -> str:
    """A plain text shape on the footline accent block: "<n> / <total>".

    Deliberately NOT a sldNum placeholder: slide-level placeholder instances
    only display when the deck's header/footer machinery is switched on, and
    LibreOffice ignores them without it (verified by rendering). A normal
    shape with an explicit position and an embedded field renders everywhere,
    at the cost of carrying its own styling -- white, bold, centred, like the
    beamer footlineright ("Page 6 / 37"). The total is a static run: the deck
    is final when this runs, so the count cannot go stale.
    """
    white = '<a:solidFill><a:schemeClr val="lt1"/></a:solidFill>'
    return (
        '<p:sp><p:nvSpPr><p:cNvPr id="9500" name="Brand Slide Number"/>'
        "<p:cNvSpPr/><p:nvPr/></p:nvSpPr>"
        f'<p:spPr><a:xfrm><a:off x="{SLIDE_CX - FOOTLINE_ACCENT_CX}" '
        f'y="{SLIDE_CY - FOOTLINE_HEIGHT_EMU}"/>'
        f'<a:ext cx="{FOOTLINE_ACCENT_CX}" cy="{FOOTLINE_HEIGHT_EMU}"/></a:xfrm>'
        '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln>'
        "</p:spPr><p:txBody>"
        '<a:bodyPr anchor="ctr" lIns="0" rIns="0" tIns="0" bIns="0"/><a:lstStyle/>'
        '<a:p><a:pPr algn="ctr"/>'
        f'<a:fld id="{_SLDNUM_FLD_ID}" type="slidenum">'
        f'<a:rPr lang="en-US" sz="1000" b="1">{white}</a:rPr><a:t>0</a:t></a:fld>'
        f'<a:r><a:rPr lang="en-US" sz="1000" b="1">{white}</a:rPr>'
        f"<a:t> / {total}</a:t></a:r></a:p></p:txBody></p:sp>"
    )


def inject_slide_numbers(deck: Path) -> int:
    """Add slide-number shapes to content slides; return how many were added."""
    with zipfile.ZipFile(deck) as z:
        total = len([n for n in z.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)])
        targets = _content_slides(z)
        updates: dict[str, bytes] = {}
        for slide in targets:
            xml = z.read(slide).decode()
            if 'type="slidenum"' in xml:
                continue  # pandoc grew the feature; nothing to do
            new, count = re.subn(r"</p:spTree>", f"{_sldnum_shape(total)}</p:spTree>", xml, count=1)
            if count == 1:
                updates[slide] = new.encode()
        if not updates:
            return 0
    rewrite_zip(deck, updates)
    return len(updates)


_CNVPR_ID_RE = re.compile(r'(<p:cNvPr\b[^>]*?\bid=")(\d+)(")')


def _renumber_duplicate_ids(xml: str) -> str | None:
    """Give repeat ids in one slide part fresh ones; None when already unique.

    A module-level function rather than a closure in the loop below, so the
    per-slide state it mutates is its own locals.
    """
    ids = [int(i) for _, i, _ in _CNVPR_ID_RE.findall(xml)]
    if len(ids) == len(set(ids)):
        return None
    seen: set[int] = set()
    highest = max(ids)

    def _fresh(match: re.Match[str]) -> str:
        nonlocal highest
        current = int(match.group(2))
        if current not in seen:
            seen.add(current)
            return match.group(0)
        highest += 1
        seen.add(highest)
        return f"{match.group(1)}{highest}{match.group(3)}"

    return _CNVPR_ID_RE.sub(_fresh, xml)


def dedupe_shape_ids(deck: Path) -> int:
    """Make every shape id unique per slide; return how many slides changed.

    Pandoc reuses one id on at least one slide of this deck -- the shape
    tree's own non-visual id and a TextBox's both come out as 1 -- but
    ECMA-376 requires cNvPr/@id to be unique within the part, because that is
    what animations and selection target. PowerPoint renumbers it on load
    (verified in a deck it had round-tripped: the TextBox came back as 4), so
    the damage is invisible there and unknown everywhere else.

    The first shape to claim an id keeps it, which is the same choice
    PowerPoint made. Runs after unwrap_alternate_content, so there are no
    mc:Choice/mc:Fallback branches left -- inside those, two shapes sharing an
    id is legitimate, since only one branch ever renders.
    """
    with zipfile.ZipFile(deck) as z:
        updates: dict[str, bytes] = {}
        for name in z.namelist():
            if not re.fullmatch(r"ppt/slides/slide\d+\.xml", name):
                continue
            xml = z.read(name).decode()
            new = _renumber_duplicate_ids(xml)
            if new is not None:
                updates[name] = new.encode()
        if not updates:
            return 0
    rewrite_zip(deck, updates)
    return len(updates)


_ALTERNATE_RE = re.compile(r"<mc:AlternateContent([^>]*)>(.*?)</mc:AlternateContent>", re.S)
_CHOICE_RE = re.compile(r"<mc:Choice([^>]*)>(.*?)</mc:Choice>", re.S)
_XMLNS_RE = re.compile(r'\sxmlns:([A-Za-z_][\w.-]*)\s*=\s*"([^"]*)"')
_SLD_ROOT_RE = re.compile(r"(<p:sld\b)([^>]*)(>)")


def _rebind_namespaces(xml: str, carried: dict[str, str]) -> str:
    """Re-declare *carried* xmlns prefixes on the ``<p:sld>`` root.

    Args:
        xml: A slide part whose mc:AlternateContent wrappers were removed.
        carried: prefix -> URI collected from the dropped wrapper elements.

    Returns:
        The slide part with any prefix the root does not already declare added
        to it. Declaring a prefix the content happens not to use is harmless;
        leaving one unbound is not well-formed.
    """
    root = _SLD_ROOT_RE.search(xml)
    if root is None or not carried:
        return xml
    declared = dict(_XMLNS_RE.findall(root.group(2)))
    missing = {p: uri for p, uri in carried.items() if p not in declared}
    if not missing:
        return xml
    added = "".join(f' xmlns:{p}="{uri}"' for p, uri in sorted(missing.items()))
    return xml[: root.start(3)] + added + xml[root.start(3) :]


def unwrap_alternate_content(deck: Path) -> int:
    """Unwrap mc:AlternateContent on slides; return how many slides changed.

    Pandoc wraps content in an AlternateContent whose Choice requires the
    Microsoft a14 extension. Two cases occur: the --toc slide's content
    placeholder (EMPTY Fallback -- PowerPoint renders the Choice, every other
    viewer honours the fallback and shows a blank slide; LibreOffice renders
    literally nothing, verified), and every slide carrying inline or display
    math (Fallback holds a flattened rendering). Promote the Choice and drop
    the wrapper in both cases.

    The Choice carries the xmlns declarations its content needs (a14 for the
    math wrapper), so dropping it would orphan those prefixes and leave the
    part not well-formed -- PowerPoint then refuses to open the deck without a
    repair prompt. Re-declare anything the Choice bound on the <p:sld> root.
    """
    with zipfile.ZipFile(deck) as z:
        updates: dict[str, bytes] = {}
        for name in z.namelist():
            if not re.fullmatch(r"ppt/slides/slide\d+\.xml", name):
                continue
            xml = z.read(name).decode()
            if "<mc:AlternateContent" not in xml:
                continue

            carried: dict[str, str] = {}

            def _promote(m: re.Match[str], carried: dict[str, str] = carried) -> str:
                carried.update(_XMLNS_RE.findall(m.group(1)))
                promoted: list[str] = []
                for attrs, body in _CHOICE_RE.findall(m.group(2)):
                    carried.update(_XMLNS_RE.findall(attrs))
                    promoted.append(body)
                return "".join(promoted)

            new = _ALTERNATE_RE.sub(_promote, xml)
            if new != xml:
                new = _rebind_namespaces(new, carried)
                updates[name] = new.encode()
        if not updates:
            return 0
    rewrite_zip(deck, updates)
    return len(updates)


def finalize(deck: Path) -> list[str]:
    """Repair what pandoc drops and box its code blocks. Returns a
    human-readable list of what was done."""
    known = {TITLE_BG_MEDIA: TITLE_BG_IMAGE}
    done: list[str] = []
    for part in sorted(missing_layout_media(deck)):
        source = known.get(part)
        if source is None:
            # Not ours to fix -- leave it for the integrity gate to report.
            continue
        with zipfile.ZipFile(deck, "a", zipfile.ZIP_DEFLATED) as z:
            z.writestr(part, source.read_bytes())
        done.append(part)
    if unwrapped := unwrap_alternate_content(deck):
        done.append(f"AlternateContent unwrapped on {unwrapped} slides")
    # After the unwrap, so code inside a promoted mc:Choice is seen too.
    if boxed := style_code_blocks(deck):
        done.append(f"code blocks boxed on {boxed} slides")
    if fitted := fit_titles(deck):
        done.append(f"titles fitted on {fitted} slides")
    if numbered := inject_slide_numbers(deck):
        done.append(f"slide numbers on {numbered} slides")
    # Last, so every shape this module added is covered too.
    if renumbered := dedupe_shape_ids(deck):
        done.append(f"shape ids deduped on {renumbered} slides")
    return done


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: {Path(sys.argv[0]).name} <deck.pptx>", file=sys.stderr)
        sys.exit(2)
    deck = Path(sys.argv[1])
    if not deck.is_file():
        print(f"Error: no such deck: {deck}", file=sys.stderr)
        sys.exit(1)
    done = finalize(deck)
    if done:
        print(f"{deck.name}: finalized: {', '.join(done)}")
    else:
        print(f"{deck.name}: nothing to finalize.")


if __name__ == "__main__":
    main()
