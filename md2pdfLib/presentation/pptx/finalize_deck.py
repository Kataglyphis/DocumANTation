"""Finish an emitted deck; see docs/build-pipeline.md § Presentation."""

from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path

# Import as a package module even when run by path; see fit_titles.py.
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
    """Text shape "<n> / <total>" on the footline accent block, not a sldNum placeholder."""
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
        # append_shapes substitutes literally and returns None without a shape tree.
        return append_shapes(xml, [_sldnum_shape(len(parts.slides))])

    return edit_slides(deck, transform)


_CNVPR_ID_RE = re.compile(r'(<p:cNvPr\b[^>]*?\bid=")(\d+)(")')


def _renumber_duplicate_ids(xml: str) -> str | None:
    """Give repeat ids in one slide part fresh ones; None when already unique."""
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
    """Make shape ids unique per slide, first claimant keeping its id; return slides changed."""
    return edit_slides(deck, lambda parts, name, xml: _renumber_duplicate_ids(xml))


_ALTERNATE_RE = re.compile(r"<mc:AlternateContent([^>]*)>(.*?)</mc:AlternateContent>", re.S)
_CHOICE_RE = re.compile(r"<mc:Choice([^>]*)>(.*?)</mc:Choice>", re.S)
_XMLNS_RE = re.compile(r'\sxmlns:([A-Za-z_][\w.-]*)\s*=\s*"([^"]*)"')
_SLD_ROOT_RE = re.compile(r"(<p:sld\b)([^>]*)(>)")


def _rebind_namespaces(xml: str, carried: dict[str, str]) -> str:
    """Re-declare on ``<p:sld>`` each *carried* prefix -> URI the root lacks."""
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
    """Promote each a14 mc:Choice, whose Fallback other viewers show; return slides changed."""
    return edit_slides(deck, lambda parts, name, xml: _promote_alternate_content(xml))


def finalize(deck: Path) -> list[str]:
    """Repair what pandoc drops and box its code blocks; return what was done."""
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
