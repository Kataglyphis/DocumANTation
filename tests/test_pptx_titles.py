"""Tests for frame-title fitting (keeping a title out of the separator rule).

Pandoc leaves the title run unsized, so it renders at the master's 33pt, where
seven of this deck's titles need a second line that falls out of the
placeholder and through the accent rule beneath it. The beamer deck keeps the
same strings on one line, so overflow is a defect, not a style choice.
"""

from __future__ import annotations

import re
import zipfile
from pathlib import Path

from md2pdfLib.presentation.pptx.fit_titles import (
    TITLE_SIZE_MIN,
    fit_slide_title,
    fit_title_size,
    fit_titles,
    fits,
    title_text_size,
)

# The master's title box and size, as pandoc's reference deck defines them.
TITLE_X, TITLE_Y, TITLE_CX, TITLE_CY = 457200, 205979, 8229600, 857250
CAP = 3300
MASTER_XML = (
    "<p:sldMaster><p:cSld><p:spTree>"
    '<p:sp><p:nvSpPr><p:nvPr><p:ph type="title" /></p:nvPr></p:nvSpPr>'
    f'<p:spPr><a:xfrm><a:off x="{TITLE_X}" y="{TITLE_Y}" />'
    f'<a:ext cx="{TITLE_CX}" cy="{TITLE_CY}" /></a:xfrm></p:spPr>'
    "<p:txBody><a:bodyPr/><a:lstStyle/><a:p/></p:txBody></p:sp>"
    "</p:spTree></p:cSld>"
    f'<p:txStyles><p:titleStyle><a:lvl1pPr><a:defRPr sz="{CAP}"/></a:lvl1pPr>'
    "</p:titleStyle></p:txStyles></p:sldMaster>"
)
LAYOUT_XML = (
    "<p:sldLayout><p:cSld><p:spTree>"
    '<p:sp><p:nvSpPr><p:nvPr><p:ph type="title" /></p:nvPr></p:nvSpPr><p:spPr/>'
    "<p:txBody><a:bodyPr/><a:lstStyle/><a:p/></p:txBody></p:sp>"
    "</p:spTree></p:cSld></p:sldLayout>"
)
# The longest title in this deck; beamer keeps it on one line.
LONG = "2.7 Code example: Rust (tiny CLI-like utility)"
SHORT = "2.10 Trade-offs"


def _slide(title: str) -> str:
    return (
        "<p:sld><p:cSld><p:spTree>"
        '<p:sp><p:nvSpPr><p:cNvPr id="2" name="Title 1"/>'
        '<p:nvPr><p:ph type="title" /></p:nvPr></p:nvSpPr><p:spPr/>'
        f"<p:txBody><a:bodyPr /><a:lstStyle /><a:p><a:r><a:rPr />"
        f"<a:t>{title}</a:t></a:r></a:p></p:txBody></p:sp>"
        "</p:spTree></p:cSld></p:sld>"
    )


def test_the_cap_is_read_from_the_master():
    assert title_text_size(MASTER_XML) == CAP


def test_a_short_title_is_left_at_the_master_size():
    assert fits(SHORT, CAP, TITLE_CX, TITLE_CY)
    assert fit_slide_title(_slide(SHORT), LAYOUT_XML, MASTER_XML) is None


def test_the_deck_s_longest_title_no_longer_overflows():
    assert not fits(LONG, CAP, TITLE_CX, TITLE_CY), "this is the bug being fixed"
    size = fit_title_size(LONG, TITLE_CX, TITLE_CY, CAP)
    assert size < CAP
    assert fits(LONG, size, TITLE_CX, TITLE_CY)


def test_the_fitted_size_is_the_largest_that_fits():
    size = fit_title_size(LONG, TITLE_CX, TITLE_CY, CAP)
    assert not fits(LONG, size + 50, TITLE_CX, TITLE_CY)


def test_an_impossible_title_stops_at_the_floor():
    """Past the floor a title reads as body text; leave it long instead."""
    assert fit_title_size("x" * 4000, TITLE_CX, TITLE_CY, CAP) == TITLE_SIZE_MIN


def test_the_size_lands_on_the_title_run():
    out = fit_slide_title(_slide(LONG), LAYOUT_XML, MASTER_XML)
    assert out is not None
    size = fit_title_size(LONG, TITLE_CX, TITLE_CY, CAP)
    assert f'sz="{size}"' in out
    assert LONG in out, "the title text itself must survive"


def test_fit_titles_only_rewrites_the_slides_that_overflow(tmp_path: Path):
    deck = tmp_path / "deck.pptx"
    rels = (
        '<Relationships><Relationship Id="rId1" Type="x" '
        'Target="../slideLayouts/slideLayout2.xml"/></Relationships>'
    )
    with zipfile.ZipFile(deck, "w") as z:
        z.writestr("ppt/slideMasters/slideMaster1.xml", MASTER_XML)
        z.writestr("ppt/slideLayouts/slideLayout2.xml", LAYOUT_XML)
        z.writestr("ppt/slides/slide1.xml", _slide(LONG))
        z.writestr("ppt/slides/_rels/slide1.xml.rels", rels)
        z.writestr("ppt/slides/slide2.xml", _slide(SHORT))
        z.writestr("ppt/slides/_rels/slide2.xml.rels", rels)

    assert fit_titles(deck) == 1
    with zipfile.ZipFile(deck) as z:
        assert re.search(r'sz="\d+"', z.read("ppt/slides/slide1.xml").decode())
        assert z.read("ppt/slides/slide2.xml").decode() == _slide(SHORT)
