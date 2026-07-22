"""Tests for the pptx code boxes (the beamer tcolorbox, rebuilt in OOXML).

Pandoc drops highlighted code into the content placeholder at the master's
body size with no background: the block runs off the bottom of the slide, and
the dark palette's foreground sits on white at almost no contrast. Neither is
something the build's other gates can see -- the deck is valid, on-brand and
well-formed while being unreadable -- so the box geometry is asserted here.
"""

from __future__ import annotations

import json
import re
import zipfile
from pathlib import Path

from md2pdfLib.presentation.pptx.style_code import (
    BOX_ARC_EMU,
    BOX_LINE_EMU,
    BOX_PAD_EMU,
    CODE_SIZE_MAX,
    CODE_SIZE_MIN,
    EMU_PER_MM,
    EMU_PER_POINT,
    SLIDE_HIGHLIGHT_THEME,
    code_box_fill,
    code_lines,
    fit_code_size,
    is_code_paragraph,
    mono_font,
    mono_run_re,
    placeholder_box,
    style_code_blocks,
    style_slide,
)
from md2pdfLib.presentation.pptx.verify_brand import brand_hexes
from md2pdfLib.presets import pptx

REPO_ROOT = Path(__file__).resolve().parents[1]
BRAND = json.loads((REPO_ROOT / "style" / "brand.tokens.json").read_text("utf-8"))
MONO = mono_run_re(mono_font())
MONO_FONT = mono_font()
CODE_FILL = code_box_fill()

# The content placeholder geometry every code slide inherits. Written the way
# pandoc's reference deck writes it -- `<a:off ... />`, with the space before
# the slash that this module's first cut did not match.
CONTENT_X, CONTENT_Y, CONTENT_CX, CONTENT_CY = 457200, 1200151, 8229600, 3394472
MASTER_XML = (
    "<p:sldMaster><p:cSld><p:spTree>"
    '<p:sp><p:nvSpPr><p:nvPr><p:ph idx="1" type="body" /></p:nvPr></p:nvSpPr>'
    f'<p:spPr><a:xfrm><a:off x="{CONTENT_X}" y="{CONTENT_Y}" />'
    f'<a:ext cx="{CONTENT_CX}" cy="{CONTENT_CY}" /></a:xfrm></p:spPr>'
    "<p:txBody><a:bodyPr/><a:lstStyle/><a:p/></p:txBody></p:sp>"
    "</p:spTree></p:cSld>"
    '<p:txStyles><p:bodyStyle><a:lvl1pPr marL="342900"><a:defRPr sz="2400"/></a:lvl1pPr>'
    "</p:bodyStyle></p:txStyles></p:sldMaster>"
)
# Pandoc's layout leaves the placeholder unpositioned; the master decides.
LAYOUT_XML = (
    "<p:sldLayout><p:cSld><p:spTree>"
    '<p:sp><p:nvSpPr><p:nvPr><p:ph idx="1" /></p:nvPr></p:nvSpPr><p:spPr/>'
    "<p:txBody><a:bodyPr/><a:lstStyle/><a:p/></p:txBody></p:sp>"
    "</p:spTree></p:cSld></p:sldLayout>"
)


def _run(text: str, *, mono: bool = True) -> str:
    face = f'<a:latin typeface="{MONO_FONT}" />' if mono else ""
    fill = '<a:solidFill><a:srgbClr val="C9D1D9" /></a:solidFill>'
    return f"<a:rPr>{fill}{face}</a:rPr><a:t>{text}</a:t>"


def _code_paragraph(*lines: str) -> str:
    runs = "<a:br />".join(f"<a:r>{_run(line)}</a:r>" for line in lines)
    return f'<a:p><a:pPr lvl="0" indent="0"><a:buNone /></a:pPr>{runs}</a:p>'


def _prose_paragraph(text: str) -> str:
    props = '<a:pPr lvl="0" indent="0" marL="0"><a:buNone /></a:pPr>'
    return f"<a:p>{props}<a:r>{_run(text, mono=False)}</a:r></a:p>"


def _slide(*paragraphs: str) -> str:
    return (
        "<p:sld><p:cSld><p:spTree>"
        '<p:sp><p:nvSpPr><p:cNvPr id="3" name="Content Placeholder 2"/>'
        '<p:nvPr><p:ph idx="1" /></p:nvPr></p:nvSpPr><p:spPr/>'
        f"<p:txBody><a:bodyPr /><a:lstStyle />{''.join(paragraphs)}</p:txBody></p:sp>"
        "</p:spTree></p:cSld></p:sld>"
    )


def _styled(*paragraphs: str) -> str:
    """The slide, with its code boxed -- the call every geometry test makes."""
    out = style_slide(_slide(*paragraphs), LAYOUT_XML, MASTER_XML, MONO, CODE_FILL)
    assert out is not None
    return out


def _boxes(xml: str) -> list[tuple[int, int, int, int]]:
    return [
        tuple(int(v) for v in m)  # type: ignore[misc]
        for m in re.findall(
            r'name="Brand Code Block \d+".*?<a:off x="(\d+)" y="(\d+)"/>'
            r'<a:ext cx="(\d+)" cy="(\d+)"/>',
            xml,
            re.S,
        )
    ]


# ── telling code from prose ──────────────────────────────────────────────────


def test_a_fenced_block_is_every_run_in_the_mono_font():
    assert is_code_paragraph(_code_paragraph("make beamer"), MONO)


def test_inline_code_in_a_bullet_is_not_a_code_block():
    """`Engine: `lualatex`` is mono in part -- boxing it would eat the bullet."""
    mixed = (
        f"<a:p><a:pPr/><a:r>{_run('Engine: ', mono=False)}</a:r><a:r>{_run('lualatex')}</a:r></a:p>"
    )
    assert not is_code_paragraph(mixed, MONO)


def test_code_lines_decode_entities_before_measuring():
    """A raw &quot; measures five characters wide and costs the block a font
    step it did not need -- and, once, a phantom trailing line in every box."""
    lines = code_lines(_code_paragraph("print(&quot;hi&quot;)", "done"))
    assert lines == ['print("hi")', "done"]


# ── fitting ──────────────────────────────────────────────────────────────────


def test_short_code_keeps_the_beamer_equivalent_size():
    size, rendered = fit_code_size(["fn main() {", "}"], CONTENT_CX, CONTENT_CY)
    assert size == CODE_SIZE_MAX
    assert rendered == 2


def test_a_long_block_shrinks_instead_of_overflowing():
    size, rendered = fit_code_size([f"line {i}" for i in range(40)], CONTENT_CX, CONTENT_CY)
    assert CODE_SIZE_MIN <= size < CODE_SIZE_MAX
    assert rendered == 40


def test_a_long_line_is_counted_as_the_rows_it_wraps_to():
    size, rendered = fit_code_size(["x" * 400], CONTENT_CX, CONTENT_CY)
    assert rendered > 1 and size == CODE_SIZE_MAX


def test_shrinking_stops_at_the_readable_floor():
    """Past the floor a block overflows, exactly as an oversized beamer frame
    does. Shrinking to fit any input would put unreadable code on a slide."""
    size, _ = fit_code_size([f"line {i}" for i in range(400)], CONTENT_CX, CONTENT_CY)
    assert size == CODE_SIZE_MIN


# ── geometry ─────────────────────────────────────────────────────────────────


def test_placeholder_geometry_is_inherited_from_the_master():
    """Pandoc emits `<p:spPr/>`, so nothing is positioned on the slide itself."""
    sp = _slide(_code_paragraph("x"))
    sp = sp[sp.index("<p:sp>") : sp.index("</p:sp>") + len("</p:sp>")]
    assert placeholder_box(sp, LAYOUT_XML, MASTER_XML) == (
        CONTENT_X,
        CONTENT_Y,
        CONTENT_CX,
        CONTENT_CY,
    )


def test_the_box_stays_inside_the_content_area():
    out = _styled(_code_paragraph(*[f"line {i}" for i in range(12)]))
    ((x, y, cx, cy),) = _boxes(out)
    assert (x, cx) == (CONTENT_X, CONTENT_CX)
    assert y >= CONTENT_Y
    assert y + cy <= CONTENT_Y + CONTENT_CY


def test_a_box_below_prose_starts_below_it():
    out = _styled(_prose_paragraph("Intro sentence." * 4), _code_paragraph("x", "y"))
    ((_, y, _, _),) = _boxes(out)
    assert y > CONTENT_Y


def test_two_blocks_stack_without_overlapping():
    out = _styled(_code_paragraph("a", "b"), _code_paragraph("c", "d", "e"))
    first, second = _boxes(out)
    assert second[1] >= first[1] + first[3]
    assert second[1] + second[3] <= CONTENT_Y + CONTENT_CY


def test_shapes_added_to_one_slide_get_distinct_ids():
    out = _styled(_code_paragraph("a"), _code_paragraph("b"))
    ids = re.findall(r'<p:cNvPr id="(\d+)"', out)
    assert len(ids) == len(set(ids)), "duplicate ids make PowerPoint repair the deck"


# ── the box itself ───────────────────────────────────────────────────────────


def test_the_code_moves_out_of_the_placeholder_into_a_branded_box():
    out = _styled(_code_paragraph("make beamer"))
    placeholder = out[out.index("<p:sp>") : out.index("</p:sp>")]
    assert "make beamer" not in placeholder, "the code must leave the placeholder"
    assert 'prst="roundRect"' in out
    assert f'<a:srgbClr val="{CODE_FILL}"/>' in out
    assert f'<a:ln w="{BOX_LINE_EMU}"><a:solidFill><a:schemeClr val="accent1"/>' in out
    assert f'sz="{CODE_SIZE_MAX}"' in out, "runs must be pinned, not left at body size"
    assert "<a:noAutofit/>" in out, "viewers must not re-lay out what was measured here"


def test_prose_on_the_slide_is_left_in_the_placeholder():
    out = _styled(_prose_paragraph("Keep me."), _code_paragraph("x"))
    placeholder = out[out.index("<p:sp>") : out.index("</p:sp>")]
    assert "Keep me." in placeholder


def test_code_containing_backslashes_survives_the_move():
    r"""The deck has a LaTeX slide: `\int_0^\infty` is a backslash escape in
    any regex replacement string, and a `re.sub`-based mover dies on it."""
    out = _styled(_code_paragraph(r"\int_0^\infty e^{-x} \, dx = 1"))
    assert r"\int_0^\infty e^{-x} \, dx = 1" in out


def test_styling_an_already_boxed_slide_is_a_no_op():
    """The paragraph inside a finished box still looks like pandoc's, and this
    module ships a CLI -- so a second run must not box the boxes."""
    once = _styled(_code_paragraph("make beamer"))
    assert style_slide(once, LAYOUT_XML, MASTER_XML, MONO, CODE_FILL) is None


def test_a_slide_without_code_is_untouched():
    slide = _slide(_prose_paragraph("No code here."))
    assert style_slide(slide, LAYOUT_XML, MASTER_XML, MONO, CODE_FILL) is None


def test_the_box_fill_is_the_palette_pandoc_highlighted_with():
    """The fill and the text on it come from one file, so a re-generated
    palette cannot leave light-on-light code behind."""
    assert BRAND["syntax_dark"]["bg"].lstrip("#").upper() == CODE_FILL


def test_the_box_reads_the_palette_the_pptx_preset_actually_passes_pandoc():
    """The fill is only guaranteed to match the code on it while this module
    and the preset name the same theme. Point the preset at the light palette
    and the runs go dark-on-dark inside an unchanged dark box."""
    assert Path(pptx().highlight_style).name == SLIDE_HIGHLIGHT_THEME.name


def test_the_box_uses_only_brand_colours():
    """The strict gate rejects any other value; catch it here instead."""
    out = _styled(_code_paragraph("x"))
    assert {c.upper() for c in re.findall(r'srgbClr val="([0-9A-Fa-f]{6})"', out)} <= brand_hexes(
        BRAND
    )


# ── the box against the one it copies ────────────────────────────────────────

CODE_BOX_TEX = REPO_ROOT / "md2pdfLib" / "common" / "latex" / "brand-code-block.tex"
SLIDES_TEX = REPO_ROOT / "data" / "presentation" / "latex" / "main.tex"


def _tex_length(path: Path, key: str, unit: str) -> float:
    # Comments first: brand-code-block.tex documents the book's own
    # `top=2.5mm` override in a comment, which otherwise matches before the
    # real option does.
    body = re.sub(r"(?<!\\)%.*", "", path.read_text("utf-8"))
    match = re.search(rf"\b{key}=([\d.]+){unit}\b", body)
    assert match is not None, f"no {key}=<n>{unit} in {path.name}"
    return float(match.group(1))


def test_the_box_geometry_matches_the_beamer_tcolorbox():
    """brand-code-block.tex calls itself "the single copy" of the brand code
    box, and this module is a second one in another language -- no --check or
    grep can relate them. Round the corners there and the deck must follow."""
    assert _tex_length(CODE_BOX_TEX, "arc", "mm") * EMU_PER_MM == BOX_ARC_EMU
    for side in ("left", "right", "top", "bottom"):
        assert _tex_length(CODE_BOX_TEX, side, "mm") * EMU_PER_MM == BOX_PAD_EMU, side
    # The rule is the slides' override, not the shared default.
    assert round(_tex_length(SLIDES_TEX, "boxrule", "pt") * EMU_PER_POINT) == BOX_LINE_EMU


# ── the deck ─────────────────────────────────────────────────────────────────


def test_style_code_blocks_rewrites_only_slides_with_code(tmp_path: Path):
    deck = tmp_path / "deck.pptx"
    rels = (
        '<Relationships><Relationship Id="rId1" Type="x" '
        'Target="../slideLayouts/slideLayout2.xml"/></Relationships>'
    )
    with zipfile.ZipFile(deck, "w") as z:
        z.writestr("ppt/slideMasters/slideMaster1.xml", MASTER_XML)
        z.writestr("ppt/slideLayouts/slideLayout2.xml", LAYOUT_XML)
        z.writestr("ppt/slides/slide1.xml", _slide(_code_paragraph("make beamer")))
        z.writestr("ppt/slides/_rels/slide1.xml.rels", rels)
        z.writestr("ppt/slides/slide2.xml", _slide(_prose_paragraph("No code here.")))
        z.writestr("ppt/slides/_rels/slide2.xml.rels", rels)

    assert style_code_blocks(deck) == 1
    with zipfile.ZipFile(deck) as z:
        assert "Brand Code Block" in z.read("ppt/slides/slide1.xml").decode()
        assert z.read("ppt/slides/slide2.xml").decode() == _slide(_prose_paragraph("No code here."))
