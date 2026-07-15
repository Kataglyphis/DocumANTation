"""Tests for the generated pptx reference deck (the brand's route into PowerPoint).

The reference deck is the only thing that colours a pptx, and it is binary --
so if it ever silently fell back to pandoc's stock Office theme, no diff and no
drift check would show it. These tests assert the brand actually lands in the
theme XML, and that a slot the patcher fails to find is a loud error rather
than a half-branded deck.
"""

from __future__ import annotations

import json
import re
import zipfile
from pathlib import Path

import pytest

from md2pdfLib.presentation.pptx.make_reference import (
    ReferenceBuildError,
    brand_theme_colors,
    build_reference,
    patch_theme_xml,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
BRAND = json.loads((REPO_ROOT / "style" / "brand.tokens.json").read_text("utf-8"))

# The shape pandoc's default reference.pptx uses: dk1/lt1 as sysClr, the rest
# as srgbClr. Kept minimal on purpose -- the real file is asserted against in
# test_build_reference_against_real_pandoc.
THEME_XML = (
    "<a:theme><a:themeElements><a:clrScheme name='Office'>"
    '<a:dk1><a:sysClr val="windowText" lastClr="000000"/></a:dk1>'
    '<a:lt1><a:sysClr val="window" lastClr="FFFFFF"/></a:lt1>'
    '<a:dk2><a:srgbClr val="1F497D"/></a:dk2>'
    '<a:lt2><a:srgbClr val="EEECE1"/></a:lt2>'
    '<a:accent1><a:srgbClr val="4F81BD"/></a:accent1>'
    '<a:accent2><a:srgbClr val="C0504D"/></a:accent2>'
    '<a:accent3><a:srgbClr val="9BBB59"/></a:accent3>'
    '<a:accent4><a:srgbClr val="8064A2"/></a:accent4>'
    '<a:accent5><a:srgbClr val="4BACC6"/></a:accent5>'
    '<a:accent6><a:srgbClr val="F79646"/></a:accent6>'
    '<a:hlink><a:srgbClr val="0000FF"/></a:hlink>'
    '<a:folHlink><a:srgbClr val="800080"/></a:folHlink>'
    "</a:clrScheme>"
    '<a:fontScheme name="Office">'
    '<a:majorFont><a:latin typeface="Calibri"/></a:majorFont>'
    '<a:minorFont><a:latin typeface="Calibri"/></a:minorFont>'
    "</a:fontScheme></a:themeElements></a:theme>"
)


def _colors(xml: str) -> dict[str, str]:
    return dict(re.findall(r'<a:(\w+)><a:srgbClr val="([0-9A-F]{6})"/></a:\1>', xml))


# ── the brand -> Office mapping ──────────────────────────────────────────────


def test_every_office_slot_is_brand_defined():
    """All twelve, so nothing is left at an Office default."""
    mapped = brand_theme_colors(BRAND)
    assert set(mapped) == {
        "dk1", "lt1", "dk2", "lt2",
        "accent1", "accent2", "accent3", "accent4", "accent5", "accent6",
        "hlink", "folHlink",
    }  # fmt: skip
    brand_values = set(BRAND["colors"].values())
    for slot, value in mapped.items():
        assert value in brand_values, f"{slot} is not a brand colour"


def test_accent1_is_the_brand_accent():
    """accent1 is what shapes and headings pick up by default."""
    assert brand_theme_colors(BRAND)["accent1"] == BRAND["colors"]["accent"]


def test_links_match_the_other_documents():
    """The CV, book and slides all use brandLink; the deck must not differ."""
    assert brand_theme_colors(BRAND)["hlink"] == BRAND["colors"]["link"]


# ── theme patching ───────────────────────────────────────────────────────────


def test_patch_replaces_colours_and_font():
    out = patch_theme_xml(THEME_XML, brand_theme_colors(BRAND), BRAND["fonts"]["main"])
    got = _colors(out)
    assert got["accent1"] == BRAND["colors"]["accent"].lstrip("#").upper()
    assert got["hlink"] == BRAND["colors"]["link"].lstrip("#").upper()
    assert out.count(f'typeface="{BRAND["fonts"]["main"]}"') == 2


def test_patch_converts_syscolour_slots_to_literal_brand_colours():
    """dk1/lt1 ship as sysClr (windowText/window) and must not stay that way."""
    out = patch_theme_xml(THEME_XML, brand_theme_colors(BRAND), BRAND["fonts"]["main"])
    assert "sysClr" not in out
    assert _colors(out)["dk1"] == BRAND["colors"]["text_main"].lstrip("#").upper()


def test_no_stock_office_value_survives():
    out = patch_theme_xml(THEME_XML, brand_theme_colors(BRAND), BRAND["fonts"]["main"])
    for stale in ("4F81BD", "1F497D", "C0504D", "0000FF", "800080", "Calibri"):
        assert stale not in out


def test_patch_is_idempotent():
    once = patch_theme_xml(THEME_XML, brand_theme_colors(BRAND), BRAND["fonts"]["main"])
    twice = patch_theme_xml(once, brand_theme_colors(BRAND), BRAND["fonts"]["main"])
    assert once == twice


def test_a_missing_slot_fails_loudly():
    """Half-branded is worse than failed: pandoc changing its default must break the build."""
    without_accent1 = THEME_XML.replace('<a:accent1><a:srgbClr val="4F81BD"/></a:accent1>', "")
    with pytest.raises(ReferenceBuildError, match="accent1"):
        patch_theme_xml(without_accent1, brand_theme_colors(BRAND), BRAND["fonts"]["main"])


def test_a_missing_font_slot_fails_loudly():
    without_font = THEME_XML.replace('<a:majorFont><a:latin typeface="Calibri"/></a:majorFont>', "")
    with pytest.raises(ReferenceBuildError, match="majorFont"):
        patch_theme_xml(without_font, brand_theme_colors(BRAND), BRAND["fonts"]["main"])


# ── end to end, against pandoc's real reference deck ─────────────────────────


@pytest.mark.skipif(
    __import__("shutil").which("pandoc") is None,
    reason="pandoc not on PATH (it lives in the image)",
)
def test_build_reference_against_real_pandoc(tmp_path):
    """Guards the assumption the patcher rests on: pandoc's actual file layout."""
    out = build_reference(tmp_path / "reference.pptx", BRAND)
    assert out.is_file()
    with zipfile.ZipFile(out) as z:
        assert z.testzip() is None
        themes = [n for n in z.namelist() if re.fullmatch(r"ppt/theme/theme\d+\.xml", n)]
        assert themes, "no theme part in pandoc's reference.pptx"
        for name in themes:
            xml = z.read(name).decode()
            assert _colors(xml)["accent1"] == BRAND["colors"]["accent"].lstrip("#").upper()
            assert BRAND["fonts"]["main"] in xml
    assert not (tmp_path / "reference.default.pptx").exists(), "temp file left behind"
