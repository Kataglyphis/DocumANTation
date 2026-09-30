"""Shrink only overflowing frame titles: the title box cannot grow, it positions the rule."""

from __future__ import annotations

import re
import sys
from pathlib import Path

# Import as a package module even when run by path, or sibling modules load twice.
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from md2pdfLib.presentation.pptx.pptx_common import (  # noqa: E402
    SP_RE,
    TEXT_RE,
    TXBODY_RE,
    DeckParts,
    edit_slides,
    master_style_size,
    run_cli,
    sized_runs,
)
from md2pdfLib.presentation.pptx.style_code import EMU_PER_POINT, placeholder_box  # noqa: E402

# Per-character advance, measured on a rendered deck just above the long titles that overflow.
TITLE_ADVANCE = 0.57
TITLE_LINE_HEIGHT = 1.2
TITLE_SIZE_STEP = 50
# Below this a title stops outranking the 24pt body; a longer one is the heading's to fix.
TITLE_SIZE_MIN = 2200
# What an unsized title run renders at when the master declares no size.
TITLE_SIZE_DEFAULT = 3300

_TITLE_PH_RE = re.compile(r'<p:ph\b[^>]*\btype="title"')


def title_text_size(master_xml: str) -> int:
    """The master's title size -- what an unsized title run renders at."""
    return master_style_size(master_xml, "titleStyle", TITLE_SIZE_DEFAULT)


def fits(text: str, size: int, cx: int, cy: int) -> bool:
    """Whether *text* at *size* fits one line of a *cx* x *cy* box; a second hits the rule."""
    columns = max(1, int(cx // (size / 100 * TITLE_ADVANCE * EMU_PER_POINT)))
    line_height = size / 100 * TITLE_LINE_HEIGHT * EMU_PER_POINT
    return len(text) <= columns and line_height <= cy


def fit_title_size(text: str, cx: int, cy: int, cap: int) -> int:
    """The largest size up to *cap* at which *text* stays in the box."""
    for size in range(cap, TITLE_SIZE_MIN - 1, -TITLE_SIZE_STEP):
        if fits(text, size, cx, cy):
            return size
    return TITLE_SIZE_MIN


def fit_slide_title(xml: str, layout_xml: str, master_xml: str) -> str | None:
    """Return *xml* with an overflowing title shrunk, or None when it fits."""
    cap = title_text_size(master_xml)
    for sp in SP_RE.findall(xml):
        if not _TITLE_PH_RE.search(sp):
            continue
        body = TXBODY_RE.search(sp)
        geometry = placeholder_box(sp, layout_xml, master_xml)
        if body is None or geometry is None:
            continue
        _, _, cx, cy = geometry
        text = "".join(TEXT_RE.findall(body.group(2)))
        if not text or fits(text, cap, cx, cy):
            continue
        sized = sized_runs(body.group(2), fit_title_size(text, cx, cy, cap))
        new_sp = sp[: body.start(2)] + sized + sp[body.end(2) :]
        # Sized runs keep their size, so a re-run on a finished deck is no change.
        if new_sp == sp:
            continue
        return xml.replace(sp, new_sp, 1)
    return None


def fit_titles(deck: Path) -> int:
    """Shrink every overflowing frame title in *deck*; return how many."""

    def transform(parts: DeckParts, name: str, xml: str) -> str | None:
        master_xml = parts.master()
        if not master_xml:
            return None
        return fit_slide_title(xml, parts.layout(name), master_xml)

    return edit_slides(deck, transform)


def main() -> None:
    run_cli(lambda deck: f"{deck.name}: titles fitted on {fit_titles(deck)} slides.")


if __name__ == "__main__":
    main()
