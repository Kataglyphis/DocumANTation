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

# Import as a package module even when run as a script by path -- see the note
# in fit_titles.py.
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from md2pdfLib.presentation.pptx.fit_titles import fit_titles  # noqa: E402
from md2pdfLib.presentation.pptx.make_reference import (  # noqa: E402
    FOOTLINE_ACCENT_CX,
    FOOTLINE_HEIGHT_EMU,
    SEPARATOR_LAYOUTS,
    SLIDE_CX,
    SLIDE_CY,
    TITLE_BG_IMAGE,
    TITLE_BG_MEDIA,
)
from md2pdfLib.presentation.pptx.pptx_common import (  # noqa: E402
    FLUSH_CENTERED_BODY,
    DeckParts,
    append_shapes,
    dangling_layout_media,
    edit_slides,
    run_cli,
    shape,
)
from md2pdfLib.presentation.pptx.style_code import style_code_blocks  # noqa: E402

# A fixed field GUID: any stable value is valid; viewers re-evaluate the field.
_SLDNUM_FLD_ID = "{93BE9E90-0A5C-4E0B-BA7A-1EDB98A1C7DE}"


def missing_layout_media(deck: Path) -> set[str]:
    """Media parts referenced from layout rels but absent from the archive."""
    return {
        f"ppt/media/{target}"
        for targets in dangling_layout_media(deck).values()
        for target in targets
    }


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
    paragraph = (
        '<a:p><a:pPr algn="ctr"/>'
        f'<a:fld id="{_SLDNUM_FLD_ID}" type="slidenum">'
        f'<a:rPr lang="en-US" sz="1000" b="1">{white}</a:rPr><a:t>0</a:t></a:fld>'
        f'<a:r><a:rPr lang="en-US" sz="1000" b="1">{white}</a:rPr>'
        f"<a:t> / {total}</a:t></a:r></a:p>"
    )
    return shape(
        shape_id=9500,
        name="Brand Slide Number",
        x=SLIDE_CX - FOOTLINE_ACCENT_CX,
        y=SLIDE_CY - FOOTLINE_HEIGHT_EMU,
        cx=FOOTLINE_ACCENT_CX,
        cy=FOOTLINE_HEIGHT_EMU,
        body_pr=FLUSH_CENTERED_BODY,
        body=paragraph,
    )


def inject_slide_numbers(deck: Path) -> int:
    """Add slide-number shapes to content slides; return how many were added."""

    def transform(parts: DeckParts, name: str, xml: str) -> str | None:
        if parts.layout_name(name) not in SEPARATOR_LAYOUTS:
            return None  # no footline on this layout, so nothing to number
        if 'type="slidenum"' in xml:
            return None  # pandoc grew the feature; nothing to do
        # append_shapes rather than a regex substitution: it puts the shape in
        # literally, and returns None for a slide with no shape tree -- which is
        # the same "leave this slide alone" the transform already means by it.
        # The local name it replaces also shadowed the imported shape() builder.
        return append_shapes(xml, [_sldnum_shape(len(parts.slides))])

    return edit_slides(deck, transform)


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
    return edit_slides(deck, lambda parts, name, xml: _renumber_duplicate_ids(xml))


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


def _promote_alternate_content(xml: str) -> str | None:
    """Promote every mc:Choice out of its wrapper; None when there is none."""
    if "<mc:AlternateContent" not in xml:
        return None
    carried: dict[str, str] = {}

    def _promote(match: re.Match[str]) -> str:
        carried.update(_XMLNS_RE.findall(match.group(1)))
        promoted: list[str] = []
        for attrs, body in _CHOICE_RE.findall(match.group(2)):
            carried.update(_XMLNS_RE.findall(attrs))
            promoted.append(body)
        return "".join(promoted)

    new = _ALTERNATE_RE.sub(_promote, xml)
    return _rebind_namespaces(new, carried) if new != xml else None


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
    return edit_slides(deck, lambda parts, name, xml: _promote_alternate_content(xml))


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
    def summary(deck: Path) -> str:
        done = finalize(deck)
        if not done:
            return f"{deck.name}: nothing to finalize."
        return f"{deck.name}: finalized: {', '.join(done)}"

    run_cli(summary)


if __name__ == "__main__":
    main()
