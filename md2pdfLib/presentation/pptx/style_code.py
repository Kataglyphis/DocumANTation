"""Box pptx code blocks like the beamer tcolorbox; see docs/build-pipeline.md § Presentation."""

from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path
from xml.sax.saxutils import unescape

# Import as a package module even when run by path; see fit_titles.py.
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from md2pdfLib.presentation.pptx.pptx_common import (  # noqa: E402
    MD2PDF_ROOT,
    SP_RE,
    TEXT_RE,
    TXBODY_RE,
    DeckParts,
    append_shapes,
    brand_tokens,
    edit_slides,
    geometry_of,
    master_style_size,
    run_cli,
    shape,
    sized_runs,
)

# The file presets.pptx passes as --syntax-highlighting, so box fill and text always agree.
SLIDE_HIGHLIGHT_THEME = MD2PDF_ROOT / "themes" / "pygments.theme"

EMU_PER_POINT = 12700
EMU_PER_MM = 36000

# tcolorbox geometry from brand-code-block.tex: 3mm padding, 2mm arc, the slides' 1.3pt rule.
BOX_PAD_EMU = 3 * EMU_PER_MM
BOX_ARC_EMU = 2 * EMU_PER_MM
BOX_LINE_EMU = round(1.3 * EMU_PER_POINT)
BOX_GAP_EMU = EMU_PER_MM * 3
# Named once: the fitter subtracts it and box_height adds it back, so they cannot disagree.
BOX_CHROME_EMU = 2 * (BOX_PAD_EMU + BOX_LINE_EMU)

# Hundredths of a pt: the cap is beamer's scriptsize scaled up, the floor stays readable.
CODE_SIZE_MAX = 1400
CODE_SIZE_MIN = 800
CODE_SIZE_STEP = 50

# The widest substitute mono: over-measuring costs a font step, under-measuring hits the frame.
MONO_ADVANCE = 0.6
# Prose is narrower; used only to place the first code box.
PROSE_ADVANCE = 0.5
LINE_HEIGHT = 1.25
# The master's bodyStyle asks for 20% space before each paragraph.
PROSE_SPACE_BEFORE = 0.2
# What prose in the placeholder renders at when the master declares no size.
BODY_SIZE_DEFAULT = 2400

# Far above pandoc's ids and clear of finalize_deck.py's slide numbers at 9500.
_SHAPE_ID_BASE = 9600
# Also marks an already-boxed block, so a second run does not box the boxes.
_CODE_BOX_NAME = "Brand Code Block"
_P_RE = re.compile(r"<a:p>.*?</a:p>|<a:p/>", re.S)
_RUN_RE = re.compile(r"<a:r>.*?</a:r>", re.S)
_PPR_RE = re.compile(r"<a:pPr\b((?:[^>\"]|\"[^\"]*\")*?)(?:/>|>.*?</a:pPr>)", re.S)
_BR_RE = re.compile(r"<a:br\s*/>|<a:br>.*?</a:br>", re.S)
# saxutils decodes only three entities; an undecoded &quot; would measure six characters.
_ENTITIES = {"&quot;": '"', "&apos;": "'"}
_PH_RE = re.compile(r"<p:ph\b([^>]*)/>")


class CodeStyleError(Exception):
    """Raised when a deck's code blocks cannot be styled."""


def code_box_fill() -> str:
    """The highlight theme's background colour, as bare uppercase hex."""
    theme = json.loads(SLIDE_HIGHLIGHT_THEME.read_text("utf-8"))
    background = theme.get("background-color")
    if not background:
        raise CodeStyleError(f"{SLIDE_HIGHLIGHT_THEME} declares no background-color.")
    return background.lstrip("#").upper()


def mono_font() -> str:
    """The brand's monospace family -- what marks a run as code."""
    return brand_tokens()["fonts"]["mono"]


def mono_run_re(mono: str) -> re.Pattern[str]:
    """Matches a run's mono typeface, however the writer spaced the empty tag."""
    return re.compile(rf'<a:latin\s+typeface="{re.escape(mono)}"\s*/>')


def is_code_paragraph(paragraph: str, mono: re.Pattern[str]) -> bool:
    """True when every run is mono; inline ``code`` is never alone in its paragraph."""
    runs = _RUN_RE.findall(paragraph)
    return bool(runs) and all(mono.search(run) for run in runs)


def _text(fragment: str) -> str:
    """Every ``<a:t>`` in *fragment*, joined and decoded -- what a reader sees."""
    return "".join(unescape(t, _ENTITIES) for t in TEXT_RE.findall(fragment))


def code_lines(paragraph: str) -> list[str]:
    """The code block's source lines, as pandoc split them across ``<a:br/>``."""
    return [_text(segment) for segment in _BR_RE.split(paragraph)]


def _char_width(size: int, advance: float) -> float:
    return size / 100 * advance * EMU_PER_POINT


def _line_height(size: int) -> float:
    return size / 100 * LINE_HEIGHT * EMU_PER_POINT


def wrapped_line_count(lines: list[str], size: int, usable_cx: int) -> int:
    """How many rendered lines *lines* takes at *size* in a box *usable_cx* wide."""
    columns = max(1, int(usable_cx // _char_width(size, MONO_ADVANCE)))
    return sum(max(1, math.ceil(len(line) / columns)) for line in lines)


def fit_code_size(lines: list[str], cx: int, cy: int) -> tuple[int, int]:
    """(font size, rendered lines) of the largest fit, else the floor: overflow beats unreadable."""
    usable_cx = cx - BOX_CHROME_EMU
    usable_cy = cy - BOX_CHROME_EMU
    count = 0
    for candidate in range(CODE_SIZE_MAX, CODE_SIZE_MIN - 1, -CODE_SIZE_STEP):
        count = wrapped_line_count(lines, candidate, usable_cx)
        if count * _line_height(candidate) <= usable_cy:
            return candidate, count
    # The range ends on the floor, so `count` is already its line count.
    return CODE_SIZE_MIN, count


def box_height(rendered_lines: int, size: int) -> int:
    """The box height that hugs *rendered_lines*, like tcolorbox's does."""
    return round(rendered_lines * _line_height(size)) + BOX_CHROME_EMU


def prose_height(paragraphs: list[str], size: int, cx: int) -> int:
    """Estimated prose height; it only places the first code box, so it errs wide."""
    columns = max(1, int(cx // _char_width(size, PROSE_ADVANCE)))
    total = 0.0
    for paragraph in paragraphs:
        text = _text(paragraph)
        lines = max(1, math.ceil(len(text) / columns)) if text else 1
        total += lines * _line_height(size) + PROSE_SPACE_BEFORE * size / 100 * EMU_PER_POINT
    return round(total)


def _code_paragraph_runs(paragraph: str, size: int) -> str:
    """The paragraph with every run pinned to *size* and its list styling dropped."""
    body = _PPR_RE.sub("", paragraph, count=1)
    props = (
        '<a:pPr marL="0" indent="0" algn="l">'
        '<a:lnSpc><a:spcPct val="100000"/></a:lnSpc>'
        '<a:spcBef><a:spcPts val="0"/></a:spcBef><a:buNone/></a:pPr>'
    )
    body = body.replace("<a:p>", f"<a:p>{props}", 1)
    return sized_runs(body, size)


def code_shape(
    shape_id: int, paragraph: str, size: int, x: int, y: int, cx: int, cy: int, fill: str
) -> str:
    """A rounded, dark, accent-framed box holding one code block."""
    # roundRect measures its radius against the shorter side, so recompute it per box.
    adjust = min(50000, round(BOX_ARC_EMU / min(cx, cy) * 100000))
    pad = BOX_PAD_EMU
    geometry = (
        f'<a:prstGeom prst="roundRect"><a:avLst><a:gd name="adj" fmla="val {adjust}"/>'
        "</a:avLst></a:prstGeom>"
    )
    body_pr = (
        f'<a:bodyPr wrap="square" lIns="{pad}" tIns="{pad}" rIns="{pad}" bIns="{pad}" '
        'anchor="t"><a:noAutofit/></a:bodyPr>'
    )
    return shape(
        shape_id=shape_id,
        name=f"{_CODE_BOX_NAME} {shape_id}",
        x=x,
        y=y,
        cx=cx,
        cy=cy,
        geometry=geometry,
        fill=f'<a:solidFill><a:srgbClr val="{fill}"/></a:solidFill>',
        line=(
            f'<a:ln w="{BOX_LINE_EMU}"><a:solidFill>'
            '<a:schemeClr val="accent1"/></a:solidFill></a:ln>'
        ),
        cnv_sp_pr='<p:cNvSpPr txBox="1"/>',
        body_pr=body_pr,
        body=_code_paragraph_runs(paragraph, size),
    )


def _append_shapes(xml: str, shapes: list[str]) -> str:
    """Add *shapes* to the slide's shape tree, raising rather than losing them silently."""
    patched = append_shapes(xml, shapes)
    if patched is None:
        raise CodeStyleError("Slide has no <p:spTree> to receive its code boxes.")
    return patched


def _placeholder_key(sp: str) -> str | None:
    """A ``<p:ph>``'s type/idx, the identity a slide shares with its layout."""
    match = _PH_RE.search(sp)
    if match is None:
        return None
    attrs = dict(re.findall(r'(\w+)="([^"]*)"', match.group(1)))
    return f"{attrs.get('type', 'body')}/{attrs.get('idx', '')}"


def placeholder_box(sp: str, layout_xml: str, master_xml: str) -> tuple[int, int, int, int] | None:
    """(x, y, cx, cy) of *sp*, inherited from layout then master as PowerPoint does."""
    key = _placeholder_key(sp)
    candidates = [sp]
    for xml in (layout_xml, master_xml):
        candidates += [c for c in SP_RE.findall(xml) if _placeholder_key(c) == key]
    for candidate in candidates:
        geometry = geometry_of(candidate)
        if geometry is not None:
            return geometry
    return None


def body_text_size(master_xml: str) -> int:
    """The master's level-1 body size, which prose in the placeholder keeps."""
    return master_style_size(master_xml, "bodyStyle", BODY_SIZE_DEFAULT)


def style_slide(
    xml: str, layout_xml: str, master_xml: str, mono: re.Pattern[str], fill: str
) -> str | None:
    """Return *xml* with its code blocks boxed, or None when it has none."""
    result = xml
    shape_id = _SHAPE_ID_BASE
    body_size = body_text_size(master_xml)
    for sp in SP_RE.findall(xml):
        body = TXBODY_RE.search(sp)
        if body is None or _CODE_BOX_NAME in sp:
            continue
        code: list[str] = []
        prose: list[str] = []
        for paragraph in _P_RE.findall(body.group(2)):
            (code if is_code_paragraph(paragraph, mono) else prose).append(paragraph)
        if not code:
            continue
        geometry = placeholder_box(sp, layout_xml, master_xml)
        if geometry is None:
            continue
        x, y, cx, cy = geometry

        # Boxes stack below all remaining prose, so code between two paragraphs lands under both.
        top = y + (prose_height(prose, body_size, cx) + BOX_GAP_EMU if prose else 0)
        available = y + cy - top - BOX_GAP_EMU * (len(code) - 1)
        if available <= 0:
            continue

        # Room in proportion to length, so one long block cannot starve a short one.
        blocks = [code_lines(paragraph) for paragraph in code]
        total_lines = sum(len(lines) for lines in blocks)
        shapes: list[str] = []
        cursor = top
        for paragraph, lines in zip(code, blocks, strict=True):
            allotted = int(available * len(lines) / total_lines)
            size, rendered = fit_code_size(lines, cx, allotted)
            height = min(box_height(rendered, size), allotted)
            shapes.append(code_shape(shape_id, paragraph, size, x, cursor, cx, height, fill))
            shape_id += 1
            cursor += height + BOX_GAP_EMU

        stripped = body.group(2)
        for paragraph in code:
            stripped = stripped.replace(paragraph, "", 1)
        if not _P_RE.search(stripped):
            stripped += "<a:p/>"
        new_sp = sp[: body.start(2)] + stripped + sp[body.end(2) :]
        result = result.replace(sp, new_sp, 1)
        result = _append_shapes(result, shapes)
    return result if shape_id > _SHAPE_ID_BASE else None


def style_code_blocks(deck: Path) -> int:
    """Box every code block in *deck*; return how many slides changed."""
    mono = mono_run_re(mono_font())
    fill = code_box_fill()

    def transform(parts: DeckParts, name: str, xml: str) -> str | None:
        if not mono.search(xml):
            return None
        master_xml = parts.master()
        if not master_xml:
            raise CodeStyleError(f"{deck} has code slides but no slide master.")
        return style_slide(xml, parts.layout(name), master_xml, mono, fill)

    return edit_slides(deck, transform)


def main() -> None:
    run_cli(
        lambda deck: f"{deck.name}: code blocks boxed on {style_code_blocks(deck)} slides.",
        errors=(CodeStyleError,),
    )


if __name__ == "__main__":
    main()
