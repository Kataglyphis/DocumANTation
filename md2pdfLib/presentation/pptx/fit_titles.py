"""Keep a frame title inside its box, the way the beamer deck keeps it there.

The beamer theme sets frametitles small enough that even the longest one in
this deck -- "2.7 Code example: Rust (tiny CLI-like utility)" -- stays on a
single line. Pandoc's pptx writer leaves the title run unsized, so it renders
at the master's 33pt, where the same string needs two lines and the second one
falls out of the title placeholder: straight through the accent separator rule
that make_reference.py draws under it. Seven of this deck's slides do that.

The placeholder cannot simply grow. Its height is what positions the separator
and, below it, the content box, so a taller title would push the brand
furniture down on every slide -- including the forty-odd where the title was
never too long. Shrinking only the titles that overflow leaves the rest
untouched, which is also what the beamer deck looks like: one line, one rule,
the same place on every frame.

The size is computed here rather than left to PowerPoint's normAutofit for the
reason style_code.py does the same: a stored fontScale is advisory, and a
viewer that ignores it renders the overflow it was meant to prevent.

Usage:
    python md2pdfLib/presentation/pptx/fit_titles.py <deck.pptx>
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# Import as a package module even when run as a script by path, which is how the
# build invokes this. Without it the fallback was a second, top-level copy of
# every sibling module -- so a test and the build could hold two `style_code`
# module objects with two sets of constants.
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

# Advance width per character as a fraction of the font size, measured off a
# rendered deck rather than guessed: a 40-character title came out at 0.535em
# and a short digit-heavy one at 0.640em, because bold small caps are narrow
# but figures and punctuation are not. Long titles -- the only ones that can
# overflow -- sit at the low end, so this leans just above them.
TITLE_ADVANCE = 0.57
TITLE_LINE_HEIGHT = 1.2
TITLE_SIZE_STEP = 50
# Below this a title stops outranking the 24pt body text it sits above. A
# string that still does not fit is left as it is rather than shrunk out of
# the design -- at that length the heading itself is the thing to fix.
TITLE_SIZE_MIN = 2200
# What an unsized title run renders at when the master declares no size.
TITLE_SIZE_DEFAULT = 3300

_TITLE_PH_RE = re.compile(r'<p:ph\b[^>]*\btype="title"')


def title_text_size(master_xml: str) -> int:
    """The master's title size -- what an unsized title run renders at."""
    return master_style_size(master_xml, "titleStyle", TITLE_SIZE_DEFAULT)


def fits(text: str, size: int, cx: int, cy: int) -> bool:
    """Whether *text* at *size* stays on one line inside a *cx* x *cy* box.

    One line, not "however many lines the height allows": the placeholder is
    0.89in tall against a 33pt line, so a second line does not fit under the
    first -- it lands on the separator rule drawn at the box's bottom edge.
    Beamer keeps every frametitle in this deck on one line too.
    """
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
        # A run that already carries a size keeps it, so a title fitted by an
        # earlier pass comes back unchanged here. Reporting that as a change
        # rewrote the whole archive and claimed a slide had been fitted again
        # -- finalize_deck.py runs this after style_code.py, so re-running the
        # step on a finished deck is the normal case, not an odd one.
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
