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
    TITLE_BG_IMAGE,
    TITLE_BG_REL_ID,
    TITLE_BG_SRCRECT,
    ReferenceBuildError,
    brand_theme_colors,
    build_reference,
    patch_content_layout,
    patch_section_header_layout,
    patch_theme_xml,
    patch_title_slide_layout,
)
from md2pdfLib.presentation.pptx.verify_brand import brand_hexes, off_brand_colors

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
        # layout branding landed: media part, title bg, dark section, separators
        assert "ppt/media/brandTitleBg.jpg" in z.namelist()
        layouts = {
            m.group(1): n
            for n in z.namelist()
            if n.startswith("ppt/slideLayouts/slideLayout")
            and n.endswith(".xml")
            and (m := re.search(r'<p:cSld name="([^"]+)"', z.read(n).decode()))
        }
        assert f'r:embed="{TITLE_BG_REL_ID}"' in z.read(layouts["Title Slide"]).decode()
        assert '<a:schemeClr val="dk1"/>' in z.read(layouts["Section Header"]).decode()
        assert "Brand Separator" in z.read(layouts["Title and Content"]).decode()
    assert not (tmp_path / "reference.default.pptx").exists(), "temp file left behind"


# ── the on-brand gate ────────────────────────────────────────────────────────


def _deck(path: Path, theme: str = "", slide: str = "") -> Path:
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("ppt/theme/theme1.xml", f"<a:theme>{theme}</a:theme>")
        z.writestr("ppt/slides/slide1.xml", f"<p:sld>{slide}</p:sld>")
    return path


def test_brand_hexes_covers_colours_and_syntax():
    """Slides carry syntax colours, so a colours-only allowlist would reject them."""
    hexes = brand_hexes(BRAND)
    assert BRAND["colors"]["accent"].lstrip("#").upper() in hexes
    assert BRAND["syntax_dark"]["keyword"].lstrip("#").upper() in hexes


def test_gate_passes_an_on_brand_deck(tmp_path):
    accent = BRAND["colors"]["accent"].lstrip("#").upper()
    kw = BRAND["syntax_dark"]["keyword"].lstrip("#").upper()
    deck = _deck(
        tmp_path / "ok.pptx",
        theme=f'<a:srgbClr val="{accent}"/>',
        slide=f'<a:srgbClr val="{kw}"/>',
    )
    assert off_brand_colors(deck, brand_hexes(BRAND)) == {}


def test_gate_catches_stock_office_blue_in_the_theme(tmp_path):
    """The failure this gate exists for: --reference-doc silently not applied."""
    deck = _deck(tmp_path / "bad.pptx", theme='<a:srgbClr val="4F81BD"/>')
    assert off_brand_colors(deck, brand_hexes(BRAND)) == {"ppt/theme/theme1.xml": {"4F81BD"}}


def test_gate_catches_an_off_brand_colour_on_a_slide(tmp_path):
    """e.g. --syntax-highlighting dropped, so code renders in stock colours."""
    deck = _deck(tmp_path / "bad.pptx", slide='<a:srgbClr val="123456"/>')
    assert off_brand_colors(deck, brand_hexes(BRAND)) == {"ppt/slides/slide1.xml": {"123456"}}


def test_gate_is_case_insensitive_about_hex(tmp_path):
    """OOXML writes uppercase; brand.json stores lowercase. A gate that missed
    this would pass everything and check nothing."""
    accent = BRAND["colors"]["accent"].lstrip("#").lower()
    deck = _deck(tmp_path / "ok.pptx", theme=f'<a:srgbClr val="{accent}"/>')
    assert off_brand_colors(deck, brand_hexes(BRAND)) == {}


def test_gate_refuses_a_deck_with_nothing_to_check(tmp_path):
    """An empty/renamed-parts deck must not silently pass as 'no offenders'."""
    empty = tmp_path / "empty.pptx"
    with zipfile.ZipFile(empty, "w") as z:
        z.writestr("docProps/app.xml", "<x/>")
    with pytest.raises(SystemExit):
        off_brand_colors(empty, brand_hexes(BRAND))


# ── layout branding (the beamer look, ported) ───────────────────────────────

# Minimal but structurally faithful to pandoc's default deck: cSld/spTree,
# placeholders with the lstStyle/spPr shapes observed in the real file.
TITLE_LAYOUT_XML = (
    '<p:sldLayout><p:cSld name="Title Slide"><p:spTree>'
    '<p:sp><p:nvSpPr><p:cNvPr id="2" name="Title 1"/><p:cNvSpPr/>'
    '<p:nvPr><p:ph type="ctrTitle"/></p:nvPr></p:nvSpPr>'
    '<p:spPr><a:xfrm><a:off x="685800" y="1597819"/>'
    '<a:ext cx="7772400" cy="1102519"/></a:xfrm></p:spPr>'
    "<p:txBody><a:bodyPr/><a:lstStyle/><a:p/></p:txBody></p:sp>"
    '<p:sp><p:nvSpPr><p:cNvPr id="3" name="Subtitle 2"/><p:cNvSpPr/>'
    '<p:nvPr><p:ph type="subTitle" idx="1"/></p:nvPr></p:nvSpPr>'
    '<p:spPr><a:xfrm><a:off x="1371600" y="2914650"/>'
    '<a:ext cx="6400800" cy="1314450"/></a:xfrm></p:spPr>'
    "<p:txBody><a:bodyPr/><a:lstStyle><a:lvl1pPr/></a:lstStyle><a:p/></p:txBody></p:sp>"
    "</p:spTree></p:cSld></p:sldLayout>"
)

SECTION_LAYOUT_XML = (
    '<p:sldLayout><p:cSld name="Section Header"><p:spTree>'
    '<p:sp><p:nvSpPr><p:cNvPr id="2" name="Title 1"/><p:cNvSpPr/>'
    '<p:nvPr><p:ph type="title"/></p:nvPr></p:nvSpPr>'
    '<p:spPr><a:xfrm><a:off x="722313" y="3305176"/>'
    '<a:ext cx="7772400" cy="1021556"/></a:xfrm></p:spPr>'
    "<p:txBody><a:bodyPr/><a:lstStyle><a:lvl1pPr/></a:lstStyle><a:p/></p:txBody></p:sp>"
    '<p:sp><p:nvSpPr><p:cNvPr id="3" name="Text 2"/><p:cNvSpPr/>'
    '<p:nvPr><p:ph type="body" idx="1"/></p:nvPr></p:nvSpPr>'
    "<p:spPr/>"
    "<p:txBody><a:bodyPr/><a:lstStyle/><a:p/></p:txBody></p:sp>"
    "</p:spTree></p:cSld></p:sldLayout>"
)

# Title placeholder with no xfrm of its own -- geometry inherited from master,
# exactly like the real "Title and Content" layout.
CONTENT_LAYOUT_XML = (
    '<p:sldLayout><p:cSld name="Title and Content"><p:spTree>'
    '<p:sp><p:nvSpPr><p:cNvPr id="2" name="Title 1"/><p:cNvSpPr/>'
    '<p:nvPr><p:ph type="title"/></p:nvPr></p:nvSpPr>'
    "<p:spPr/><p:txBody><a:bodyPr/><a:lstStyle/><a:p/></p:txBody></p:sp>"
    "</p:spTree></p:cSld></p:sldLayout>"
)

MASTER_XML = (
    "<p:sldMaster><p:cSld><p:spTree>"
    '<p:sp><p:nvSpPr><p:cNvPr id="2" name="Title"/><p:cNvSpPr/>'
    '<p:nvPr><p:ph type="title"/></p:nvPr></p:nvSpPr>'
    '<p:spPr><a:xfrm><a:off x="457200" y="274638"/>'
    '<a:ext cx="8229600" cy="1143000"/></a:xfrm></p:spPr>'
    "<p:txBody><a:bodyPr/><a:lstStyle/><a:p/></p:txBody></p:sp>"
    "</p:spTree></p:cSld></p:sldMaster>"
)


def test_title_layout_gets_background_and_soft_boxes():
    out = patch_title_slide_layout(TITLE_LAYOUT_XML)
    # bg is the first child of cSld, referencing the brand image with the crop
    assert re.search(r'<p:cSld name="Title Slide"><p:bg>', out)
    assert f'r:embed="{TITLE_BG_REL_ID}"' in out
    assert f'<a:srcRect t="{TITLE_BG_SRCRECT}" b="{TITLE_BG_SRCRECT}"/>' in out
    # both text placeholders got the accent_soft info box (accent6 by scheme)
    assert out.count('<a:schemeClr val="accent6"><a:alpha val="92000"/>') == 2


def test_section_layout_goes_accent_on_dark():
    out = patch_section_header_layout(SECTION_LAYOUT_XML)
    assert '<a:solidFill><a:schemeClr val="dk1"/></a:solidFill>' in out
    assert '<a:schemeClr val="accent1"/>' in out  # title text
    assert '<a:schemeClr val="lt2"/>' in out  # body text


def test_content_layout_separator_uses_master_geometry():
    out = patch_content_layout(CONTENT_LAYOUT_XML, MASTER_XML, 9000)
    # bar sits at the master title's left edge, directly under its box
    assert '<a:off x="457200" y="1417638"/>' in out  # 274638 + 1143000
    assert '<a:ext cx="8229600" cy="27432"/>' in out
    assert '<a:schemeClr val="accent1"/>' in out
    assert out.index("Brand Separator") < out.index("</p:spTree>")


def test_layout_without_placeholder_fails_loudly():
    with pytest.raises(ReferenceBuildError, match="ctrTitle"):
        patch_title_slide_layout(SECTION_LAYOUT_XML.replace("Section Header", "Title Slide"))


def _jpeg_size(path: Path) -> tuple[int, int]:
    """Width/height from JPEG SOF markers -- no imaging dependency needed."""
    data = path.read_bytes()
    i = 2
    while i < len(data):
        assert data[i] == 0xFF, "not a JPEG marker"
        marker = data[i + 1]
        if marker in {0xC0, 0xC1, 0xC2, 0xC3}:  # SOF0..3
            return (
                int.from_bytes(data[i + 7 : i + 9]),
                int.from_bytes(data[i + 5 : i + 7]),
            )
        i += 2 + int.from_bytes(data[i + 2 : i + 4])
    raise AssertionError("no SOF marker found")


def test_srcrect_constant_matches_the_actual_asset():
    """TITLE_BG_SRCRECT is derived from the image's aspect ratio; if the asset
    is ever replaced or resized, this recomputes the crop and catches drift."""
    w, h = _jpeg_size(TITLE_BG_IMAGE)
    visible = w * 9 / 16
    expected = round((h - visible) / 2 / h * 100_000)
    assert abs(TITLE_BG_SRCRECT - expected) <= 10


# ── finalize: the media pandoc drops, and the gate that notices ─────────────


def _mini_deck(tmp_path: Path, with_media: bool) -> Path:
    """A deck whose Title Slide layout references the brand bg image."""
    deck = tmp_path / "deck.pptx"
    rels = (
        '<Relationships><Relationship Id="rIdBrandTitleBg" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" '
        'Target="../media/brandTitleBg.jpg"/></Relationships>'
    )
    with zipfile.ZipFile(deck, "w") as z:
        z.writestr("ppt/slideLayouts/slideLayout1.xml", TITLE_LAYOUT_XML)
        z.writestr("ppt/slideLayouts/_rels/slideLayout1.xml.rels", rels)
        if with_media:
            z.writestr("ppt/media/brandTitleBg.jpg", b"\xff\xd8jpegbytes")
    return deck


def test_finalize_reattaches_dropped_layout_media(tmp_path: Path):
    from md2pdfLib.presentation.pptx.finalize_deck import finalize, missing_layout_media

    deck = _mini_deck(tmp_path, with_media=False)
    assert missing_layout_media(deck) == {"ppt/media/brandTitleBg.jpg"}
    added = finalize(deck)
    assert added == ["ppt/media/brandTitleBg.jpg"]
    with zipfile.ZipFile(deck) as z:
        assert z.read("ppt/media/brandTitleBg.jpg") == TITLE_BG_IMAGE.read_bytes()
    assert missing_layout_media(deck) == set()


def test_verify_brand_flags_dangling_layout_media(tmp_path: Path):
    from md2pdfLib.presentation.pptx.verify_brand import dangling_layout_media

    broken = _mini_deck(tmp_path, with_media=False)
    assert dangling_layout_media(broken) == {
        "ppt/slideLayouts/_rels/slideLayout1.xml.rels": {"brandTitleBg.jpg"}
    }
    ok_dir = tmp_path / "ok"
    ok_dir.mkdir()
    assert dangling_layout_media(_mini_deck(ok_dir, with_media=True)) == {}
