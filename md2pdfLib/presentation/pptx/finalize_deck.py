"""Repair what pandoc drops from an emitted deck: layout media, slide numbers.

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

Usage:
    python md2pdfLib/presentation/pptx/finalize_deck.py <deck.pptx>
"""

from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path

try:  # imported as a package module (tests)
    from md2pdfLib.presentation.pptx.make_reference import (
        FOOTLINE_ACCENT_CX,
        FOOTLINE_HEIGHT_EMU,
        SEPARATOR_LAYOUTS,
        SLIDE_CX,
        SLIDE_CY,
        TITLE_BG_IMAGE,
        TITLE_BG_MEDIA,
    )
except ImportError:  # run as a script from its own directory (the build)
    from make_reference import (
        FOOTLINE_ACCENT_CX,
        FOOTLINE_HEIGHT_EMU,
        SEPARATOR_LAYOUTS,
        SLIDE_CX,
        SLIDE_CY,
        TITLE_BG_IMAGE,
        TITLE_BG_MEDIA,
    )

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
        parts = {i.filename: z.read(i.filename) for i in z.infolist()}
    parts.update(updates)
    with zipfile.ZipFile(deck, "w", zipfile.ZIP_DEFLATED) as z:
        for name, payload in parts.items():
            z.writestr(name, payload)
    return len(updates)


_ALTERNATE_RE = re.compile(r"<mc:AlternateContent[^>]*>(.*?)</mc:AlternateContent>", re.S)
_CHOICE_RE = re.compile(r"<mc:Choice[^>]*>(.*?)</mc:Choice>", re.S)


def unwrap_alternate_content(deck: Path) -> int:
    """Unwrap mc:AlternateContent on slides; return how many slides changed.

    Pandoc wraps the --toc slide's content placeholder in an AlternateContent
    whose Choice requires the Microsoft a14 extension -- with an EMPTY
    Fallback. PowerPoint renders the Choice; every other viewer honours the
    fallback and shows a blank slide (LibreOffice renders literally nothing,
    verified). The Choice's content is ordinary shapes with ordinary
    hyperlinks, valid outside the wrapper everywhere, so promote it and drop
    the wrapper.
    """
    with zipfile.ZipFile(deck) as z:
        updates: dict[str, bytes] = {}
        for name in z.namelist():
            if not re.fullmatch(r"ppt/slides/slide\d+\.xml", name):
                continue
            xml = z.read(name).decode()
            if "<mc:AlternateContent" not in xml:
                continue

            def _promote(m: re.Match[str]) -> str:
                choices = _CHOICE_RE.findall(m.group(1))
                return "".join(choices)

            new = _ALTERNATE_RE.sub(_promote, xml)
            if new != xml:
                updates[name] = new.encode()
        if not updates:
            return 0
        parts = {i.filename: z.read(i.filename) for i in z.infolist()}
    parts.update(updates)
    with zipfile.ZipFile(deck, "w", zipfile.ZIP_DEFLATED) as z:
        for name, payload in parts.items():
            z.writestr(name, payload)
    return len(updates)


def finalize(deck: Path) -> list[str]:
    """Repair what pandoc drops: layout media and slide numbers. Returns a
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
    if numbered := inject_slide_numbers(deck):
        done.append(f"slide numbers on {numbered} slides")
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
