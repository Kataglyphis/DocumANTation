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
import zipfile
from pathlib import Path

try:  # imported as a package module (tests)
    from md2pdfLib.presentation.pptx.pptx_common import layout_for, rewrite_zip
    from md2pdfLib.presentation.pptx.style_code import EMU_PER_POINT, placeholder_box
except ImportError:  # run as a script from its own directory (the build)
    from pptx_common import layout_for, rewrite_zip
    from style_code import EMU_PER_POINT, placeholder_box

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

_SP_RE = re.compile(r"<p:sp>.*?</p:sp>", re.S)
_TEXT_RE = re.compile(r"<a:t>(.*?)</a:t>", re.S)
_RPR_RE = re.compile(r"<a:rPr\b((?:[^>\"]|\"[^\"]*\")*?)(/?)>")
_TITLE_PH_RE = re.compile(r'<p:ph\b[^>]*\btype="title"')
_TXBODY_RE = re.compile(r"(<p:txBody>)(.*?)(</p:txBody>)", re.S)
_SLIDE_RE = re.compile(r"ppt/slides/slide\d+\.xml")
_MASTER_RE = re.compile(r"ppt/slideMasters/slideMaster\d+\.xml")
_TITLE_SIZE_RE = re.compile(r"<p:titleStyle>.*?<a:lvl1pPr\b.*?<a:defRPr\b[^>]*\bsz=\"(\d+)\"", re.S)


def title_text_size(master_xml: str) -> int:
    """The master's title size -- what an unsized title run renders at."""
    match = _TITLE_SIZE_RE.search(master_xml)
    return int(match.group(1)) if match else 3300


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


def _sized_runs(txbody: str, size: int) -> str:
    return _RPR_RE.sub(
        lambda m: (
            f'<a:rPr{m.group(1)} sz="{size}"{m.group(2)}>'
            if " sz=" not in m.group(1)
            else m.group(0)
        ),
        txbody,
    )


def fit_slide_title(xml: str, layout_xml: str, master_xml: str) -> str | None:
    """Return *xml* with an overflowing title shrunk, or None when it fits."""
    cap = title_text_size(master_xml)
    for sp in _SP_RE.findall(xml):
        if not _TITLE_PH_RE.search(sp):
            continue
        body = _TXBODY_RE.search(sp)
        geometry = placeholder_box(sp, layout_xml, master_xml)
        if body is None or geometry is None:
            continue
        _, _, cx, cy = geometry
        text = "".join(_TEXT_RE.findall(body.group(2)))
        if not text or fits(text, cap, cx, cy):
            continue
        sized = _sized_runs(body.group(2), fit_title_size(text, cx, cy, cap))
        new_sp = sp[: body.start(2)] + sized + sp[body.end(2) :]
        return xml.replace(sp, new_sp, 1)
    return None


def fit_titles(deck: Path) -> int:
    """Shrink every overflowing frame title in *deck*; return how many."""
    with zipfile.ZipFile(deck) as z:
        masters = sorted(n for n in z.namelist() if _MASTER_RE.fullmatch(n))
        master_xml = z.read(masters[0]).decode() if masters else ""
        if not master_xml:
            return 0
        updates: dict[str, bytes] = {}
        for name in z.namelist():
            if not _SLIDE_RE.fullmatch(name):
                continue
            fitted = fit_slide_title(z.read(name).decode(), layout_for(z, name), master_xml)
            if fitted is not None:
                updates[name] = fitted.encode()
        if not updates:
            return 0
    rewrite_zip(deck, updates)
    return len(updates)


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: {Path(sys.argv[0]).name} <deck.pptx>", file=sys.stderr)
        sys.exit(2)
    deck = Path(sys.argv[1])
    if not deck.is_file():
        print(f"Error: no such deck: {deck}", file=sys.stderr)
        sys.exit(1)
    print(f"{deck.name}: titles fitted on {fit_titles(deck)} slides.")


if __name__ == "__main__":
    main()
