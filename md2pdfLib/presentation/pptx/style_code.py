"""Give pptx code blocks the beamer code box: dark, framed, and sized to fit.

The slides render fenced code inside the shared brand tcolorbox
(md2pdfLib/common/latex/brand-code-block.tex): dark fill, accent frame,
rounded corners, and \\scriptsize verbatim that wraps instead of overflowing.
Pandoc's pptx writer has no equivalent -- it drops the highlighted runs
straight into the content placeholder at the master's 24pt body size and draws
no background at all. Two things follow, both visible in a rendered deck: the
code runs off the bottom of the slide (nothing shrinks it, and long lines wrap
mid-token), and the dark palette's foreground (#c9d1d9, chosen for a #0d1117
box) sits on the white placeholder at almost no contrast.

So build the box here, the same way make_reference.py rebuilds the beamer
title wedge and footline in OOXML: lift each code paragraph out of the
placeholder into its own roundRect shape carrying the brand's code colours,
and pick the largest font size at which the block still fits the space it got.
Fitting is arithmetic rather than PowerPoint's normAutofit because the deck
must look right in a viewer that never re-lays it out: LibreOffice honours a
stored fontScale only when it agrees with its own measurement, and pandoc
emits no autofit hint at all.

The code boxes stack below whatever prose the placeholder keeps, in source
order. A code block that sits *between* two prose paragraphs therefore lands
under both -- the deck's code slides are code-only or prose-then-code, and
re-flowing prose out of its placeholder would cost it the list styling it
inherits from there.

Usage:
    python md2pdfLib/presentation/pptx/style_code.py <deck.pptx>
"""

from __future__ import annotations

import json
import math
import re
import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import unescape

try:  # imported as a package module (tests)
    from md2pdfLib.presentation.pptx.pptx_common import layout_for, rewrite_zip
except ImportError:  # run as a script from its own directory (the build)
    from pptx_common import layout_for, rewrite_zip

MD2PDF_ROOT = Path(__file__).resolve().parents[2]
BRAND_TOKENS = MD2PDF_ROOT / "style" / "brand.tokens.json"
# The palette pandoc coloured the runs with -- presets.pptx passes this exact
# file as --syntax-highlighting, so reading the box fill from it is the only
# way the fill cannot disagree with the text sitting on it.
SLIDE_HIGHLIGHT_THEME = MD2PDF_ROOT / "themes" / "pygments.theme"

EMU_PER_POINT = 12700
EMU_PER_MM = 36000

# tcolorbox geometry from brand-code-block.tex, in EMU: 3mm padding, 2mm
# corner arc, and the slides' heavier boxrule=1.3pt.
BOX_PAD_EMU = 3 * EMU_PER_MM
BOX_ARC_EMU = 2 * EMU_PER_MM
BOX_LINE_EMU = round(1.3 * EMU_PER_POINT)
BOX_GAP_EMU = EMU_PER_MM * 3
# What the frame costs a box on each axis. Named once: the fitter subtracts it
# and box_height adds it back, and the two disagreeing mis-sizes every box.
BOX_CHROME_EMU = 2 * (BOX_PAD_EMU + BOX_LINE_EMU)

# Font sizes in hundredths of a point, as OOXML counts them. The cap is
# beamer's \scriptsize scaled to this slide: 7pt on a 128mm beamer frame is
# 14pt across a 254mm PowerPoint slide. The floor is where code stops being
# readable from a room -- past it a block is allowed to overflow, exactly as
# an oversized beamer frame does, rather than shrinking to nothing.
CODE_SIZE_MAX = 1400
CODE_SIZE_MIN = 800
CODE_SIZE_STEP = 50

# Advance width per character as a fraction of the font size. Latin Modern
# Mono is 0.5, but a viewer without it substitutes (Courier New and DejaVu
# Sans Mono are both ~0.6), so measure with the widest of them: over-measuring
# costs a font step, under-measuring puts text through the frame.
MONO_ADVANCE = 0.6
# Proportional text averages narrower than mono; used only to guess how much
# vertical room the prose above a code box needs.
PROSE_ADVANCE = 0.5
LINE_HEIGHT = 1.25
# The master's bodyStyle asks for 20% space before each paragraph.
PROSE_SPACE_BEFORE = 0.2

# Ids for the shapes this module adds. Far above pandoc's own (2, 3, ...) and
# clear of finalize_deck.py's slide numbers at 9500.
_SHAPE_ID_BASE = 9600
# Also how an already-boxed block is recognised: the code paragraph inside a
# finished box still looks exactly like the one pandoc emitted, so a second
# run over the same deck would box the boxes.
_CODE_BOX_NAME = "Brand Code Block"
_SPTREE_CLOSE = "</p:spTree>"

_P_RE = re.compile(r"<a:p>.*?</a:p>|<a:p/>", re.S)
_RUN_RE = re.compile(r"<a:r>.*?</a:r>", re.S)
_TEXT_RE = re.compile(r"<a:t>(.*?)</a:t>", re.S)
_RPR_RE = re.compile(r"<a:rPr\b((?:[^>\"]|\"[^\"]*\")*?)(/?)>")
_PPR_RE = re.compile(r"<a:pPr\b((?:[^>\"]|\"[^\"]*\")*?)(?:/>|>.*?</a:pPr>)", re.S)
_BR_RE = re.compile(r"<a:br\s*/>|<a:br>.*?</a:br>", re.S)
_SP_RE = re.compile(r"<p:sp>.*?</p:sp>", re.S)
# saxutils only knows the three entities it must; code is full of quotes, and
# every undecoded &quot; would measure five characters wide instead of one.
_ENTITIES = {"&quot;": '"', "&apos;": "'"}
_TXBODY_RE = re.compile(r"(<p:txBody>)(.*?)(</p:txBody>)", re.S)
_SLIDE_RE = re.compile(r"ppt/slides/slide\d+\.xml")
_MASTER_RE = re.compile(r"ppt/slideMasters/slideMaster\d+\.xml")
_PH_RE = re.compile(r"<p:ph\b([^>]*)/>")
# Whitespace-tolerant: pandoc's reference deck writes `<a:off ... />` with a
# space before the slash, this repo's own patchers write it without.
_XFRM_RE = re.compile(
    r'<a:off\s+x="(-?\d+)"\s+y="(-?\d+)"\s*/>\s*<a:ext\s+cx="(\d+)"\s+cy="(\d+)"\s*/>'
)
_BODY_SIZE_RE = re.compile(r"<p:bodyStyle>.*?<a:lvl1pPr\b.*?<a:defRPr\b[^>]*\bsz=\"(\d+)\"", re.S)


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
    return json.loads(BRAND_TOKENS.read_text("utf-8"))["fonts"]["mono"]


def mono_run_re(mono: str) -> re.Pattern[str]:
    """Matches a run's mono typeface, however the writer spaced the empty tag."""
    return re.compile(rf'<a:latin\s+typeface="{re.escape(mono)}"\s*/>')


def is_code_paragraph(paragraph: str, mono: re.Pattern[str]) -> bool:
    """True when every run in *paragraph* is set in the mono font.

    Inline ``code`` inside prose is mono too, but never alone in its
    paragraph, so requiring *all* runs separates a fenced block from a bullet
    that merely mentions a filename.
    """
    runs = _RUN_RE.findall(paragraph)
    return bool(runs) and all(mono.search(run) for run in runs)


def _text(fragment: str) -> str:
    """Every ``<a:t>`` in *fragment*, joined and decoded -- what a reader sees."""
    return "".join(unescape(t, _ENTITIES) for t in _TEXT_RE.findall(fragment))


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
    """Return (font size, rendered line count) for a block of *cx* x *cy*.

    The largest size at which the wrapped block fits *cy*, or the floor when
    nothing fits -- a block is left to overflow rather than shrunk past
    readability.
    """
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
    """Estimated height of the prose left in the placeholder.

    Proportional text cannot be measured without the font, so this is an
    estimate; it decides only where the first code box starts, and erring wide
    costs a little slide space rather than an overlap.
    """
    columns = max(1, int(cx // _char_width(size, PROSE_ADVANCE)))
    total = 0.0
    for paragraph in paragraphs:
        text = _text(paragraph)
        lines = max(1, math.ceil(len(text) / columns)) if text else 1
        total += lines * _line_height(size) + PROSE_SPACE_BEFORE * size / 100 * EMU_PER_POINT
    return round(total)


def _sized_runs(paragraph: str, size: int) -> str:
    """The paragraph with every run pinned to *size* and its list styling dropped."""
    body = _PPR_RE.sub("", paragraph, count=1)
    props = (
        '<a:pPr marL="0" indent="0" algn="l">'
        '<a:lnSpc><a:spcPct val="100000"/></a:lnSpc>'
        '<a:spcBef><a:spcPts val="0"/></a:spcBef><a:buNone/></a:pPr>'
    )
    body = body.replace("<a:p>", f"<a:p>{props}", 1)
    return _RPR_RE.sub(
        lambda m: (
            f'<a:rPr{m.group(1)} sz="{size}"{m.group(2)}>'
            if " sz=" not in m.group(1)
            else m.group(0)
        ),
        body,
    )


def code_shape(
    shape_id: int, paragraph: str, size: int, x: int, y: int, cx: int, cy: int, fill: str
) -> str:
    """A rounded, dark, accent-framed box holding one code block."""
    # roundRect measures its corner radius against the shorter side, so the
    # arc has to be recomputed per box to stay a constant 2mm.
    adjust = min(50000, round(BOX_ARC_EMU / min(cx, cy) * 100000))
    pad = BOX_PAD_EMU
    return (
        f'<p:sp><p:nvSpPr><p:cNvPr id="{shape_id}" name="{_CODE_BOX_NAME} {shape_id}"/>'
        '<p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>'
        f'<p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
        f'<a:prstGeom prst="roundRect"><a:avLst><a:gd name="adj" fmla="val {adjust}"/>'
        "</a:avLst></a:prstGeom>"
        f'<a:solidFill><a:srgbClr val="{fill}"/></a:solidFill>'
        f'<a:ln w="{BOX_LINE_EMU}"><a:solidFill><a:schemeClr val="accent1"/></a:solidFill></a:ln>'
        "</p:spPr><p:txBody>"
        f'<a:bodyPr wrap="square" lIns="{pad}" tIns="{pad}" rIns="{pad}" bIns="{pad}" '
        'anchor="t"><a:noAutofit/></a:bodyPr><a:lstStyle/>'
        f"{_sized_runs(paragraph, size)}</p:txBody></p:sp>"
    )


def _append_shapes(xml: str, shapes: list[str]) -> str:
    """Add *shapes* to the slide's shape tree, like make_reference._append_shape.

    Loud on a missing spTree for the same reason that one is: a slide whose
    shape tree does not match would otherwise lose its code boxes silently
    while still being counted as styled.

    Substitution is literal, not ``re.sub``: unlike the shapes make_reference
    builds, these carry the deck's own code, and a slide holding LaTeX
    (``\\int_0^\\infty``) puts a backslash escape in the replacement string.
    """
    if _SPTREE_CLOSE not in xml:
        raise CodeStyleError("Slide has no <p:spTree> to receive its code boxes.")
    return xml.replace(_SPTREE_CLOSE, f"{''.join(shapes)}{_SPTREE_CLOSE}", 1)


def _placeholder_key(sp: str) -> str | None:
    """A ``<p:ph>``'s type/idx, the identity a slide shares with its layout."""
    match = _PH_RE.search(sp)
    if match is None:
        return None
    attrs = dict(re.findall(r'(\w+)="([^"]*)"', match.group(1)))
    return f"{attrs.get('type', 'body')}/{attrs.get('idx', '')}"


def placeholder_box(sp: str, layout_xml: str, master_xml: str) -> tuple[int, int, int, int] | None:
    """(x, y, cx, cy) of *sp*, resolved the way PowerPoint inherits geometry.

    Pandoc emits ``<p:spPr/>``, so a slide's content placeholder is positioned
    entirely by the layout, which in turn often defers to the master.
    """
    key = _placeholder_key(sp)
    candidates = [sp]
    for xml in (layout_xml, master_xml):
        candidates += [c for c in _SP_RE.findall(xml) if _placeholder_key(c) == key]
    for candidate in candidates:
        found = _XFRM_RE.search(candidate)
        if found:
            x, y, cx, cy = (int(v) for v in found.groups())
            return x, y, cx, cy
    return None


def body_text_size(master_xml: str) -> int:
    """The master's level-1 body size, which prose in the placeholder keeps."""
    match = _BODY_SIZE_RE.search(master_xml)
    return int(match.group(1)) if match else 2400


def style_slide(
    xml: str, layout_xml: str, master_xml: str, mono: re.Pattern[str], fill: str
) -> str | None:
    """Return *xml* with its code blocks boxed, or None when it has none."""
    result = xml
    shape_id = _SHAPE_ID_BASE
    body_size = body_text_size(master_xml)
    for sp in _SP_RE.findall(xml):
        body = _TXBODY_RE.search(sp)
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

        top = y + (prose_height(prose, body_size, cx) + BOX_GAP_EMU if prose else 0)
        available = y + cy - top - BOX_GAP_EMU * (len(code) - 1)
        if available <= 0:
            continue

        # Each block gets a share of the leftover room proportional to its
        # length, so one long block on a slide cannot starve a short one.
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
    with zipfile.ZipFile(deck) as z:
        masters = sorted(n for n in z.namelist() if _MASTER_RE.fullmatch(n))
        master_xml = z.read(masters[0]).decode() if masters else ""
        updates: dict[str, bytes] = {}
        for name in z.namelist():
            if not _SLIDE_RE.fullmatch(name):
                continue
            xml = z.read(name).decode()
            if not mono.search(xml):
                continue
            if not master_xml:
                raise CodeStyleError(f"{deck} has code slides but no slide master.")
            styled = style_slide(xml, layout_for(z, name), master_xml, mono, fill)
            if styled is not None:
                updates[name] = styled.encode()
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
    try:
        styled = style_code_blocks(deck)
    except CodeStyleError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    print(f"{deck.name}: code blocks boxed on {styled} slides.")


if __name__ == "__main__":
    main()
