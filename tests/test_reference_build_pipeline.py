"""Drive build_reference() end to end without pandoc installed.

``make_reference.build_reference`` is ~100 statements that patch pandoc's default
reference deck into the brand: twelve theme colour slots, both font slots, the
title wedge, the section background, the footline on five content layouts, the
slide-size guard and the "did every expected layout turn up" check.

The only test that covered it, ``test_build_reference_against_real_pandoc``,
skips unless pandoc is on PATH -- and pandoc lives in the build image, not in the
environment CI runs the suite in. So on every CI run that whole function was
skipped, and the module sat at ~60% coverage with its largest function untested.

Pandoc is only needed to *obtain* the input deck, so this substitutes a minimal
one carrying exactly the parts the patchers require. That covers the pipeline and
its failure modes anywhere, and the real-pandoc test still guards the assumption
that pandoc's own deck still looks like this.
"""

from __future__ import annotations

import re
import zipfile
from pathlib import Path

import pytest

from md2pdfLib.presentation.pptx import make_reference
from md2pdfLib.presentation.pptx.make_reference import (
    SEPARATOR_LAYOUTS,
    SLIDE_CX,
    SLIDE_CY,
    ReferenceBuildError,
    build_reference,
)
from md2pdfLib.presentation.pptx.pptx_common import THEME_RE, brand_tokens, layout_name

BRAND = brand_tokens()

_A = 'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"'
_P = 'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"'
_R = 'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'

# The twelve Office slots patch_theme_xml rewrites. dk1/lt1 ship as sysClr in
# pandoc's deck and the rest as srgbClr, so the fixture mixes both forms.
_SLOTS = {
    "dk1": '<a:sysClr val="windowText" lastClr="000000"/>',
    "lt1": '<a:sysClr val="window" lastClr="FFFFFF"/>',
    "dk2": '<a:srgbClr val="1F497D"/>',
    "lt2": '<a:srgbClr val="EEECE1"/>',
    "accent1": '<a:srgbClr val="4F81BD"/>',
    "accent2": '<a:srgbClr val="C0504D"/>',
    "accent3": '<a:srgbClr val="9BBB59"/>',
    "accent4": '<a:srgbClr val="8064A2"/>',
    "accent5": '<a:srgbClr val="4BACC6"/>',
    "accent6": '<a:srgbClr val="F79646"/>',
    "hlink": '<a:srgbClr val="0000FF"/>',
    "folHlink": '<a:srgbClr val="800080"/>',
}

TITLE_X, TITLE_Y, TITLE_CX, TITLE_CY = 457200, 274638, 8229600, 1143000


def _theme() -> str:
    slots = "".join(f"<a:{k}>{v}</a:{k}>" for k, v in _SLOTS.items())
    return (
        f"<a:theme {_A}><a:themeElements><a:clrScheme>{slots}</a:clrScheme>"
        '<a:fontScheme><a:majorFont><a:latin typeface="Calibri Light"/></a:majorFont>'
        '<a:minorFont><a:latin typeface="Calibri"/></a:minorFont></a:fontScheme>'
        "</a:themeElements></a:theme>"
    )


def _placeholder(ph_type: str, *, geometry: bool = False) -> str:
    xfrm = (
        f'<a:xfrm><a:off x="{TITLE_X}" y="{TITLE_Y}"/>'
        f'<a:ext cx="{TITLE_CX}" cy="{TITLE_CY}"/></a:xfrm>'
    )
    sp_pr = f"<p:spPr>{xfrm}</p:spPr>" if geometry else "<p:spPr/>"
    return (
        f'<p:sp><p:nvSpPr><p:cNvPr id="2" name="{ph_type} 1"/>'
        f'<p:nvPr><p:ph type="{ph_type}"/></p:nvPr></p:nvSpPr>{sp_pr}'
        "<p:txBody><a:bodyPr/><a:lstStyle/><a:p/></p:txBody></p:sp>"
    )


def _layout(name: str, placeholders: list[str], *, geometry: bool = False) -> str:
    body = "".join(_placeholder(p, geometry=geometry) for p in placeholders)
    return (
        f'<p:sldLayout {_P} {_A} {_R}><p:cSld name="{name}">'
        f"<p:spTree>{body}</p:spTree></p:cSld></p:sldLayout>"
    )


def _master() -> str:
    return (
        f"<p:sldMaster {_P} {_A}><p:cSld><p:spTree>"
        f"{_placeholder('title', geometry=True)}"
        "</p:spTree></p:cSld></p:sldMaster>"
    )


# Every layout build_reference expects to find, plus one it should ignore.
LAYOUTS = [
    ("Title Slide", ["ctrTitle", "subTitle"]),
    ("Section Header", ["title", "body"]),
    *[(name, ["title", "sldNum"]) for name in SEPARATOR_LAYOUTS],
    ("Blank", []),
]


def _default_deck(dest: Path, *, omit_layout: str | None = None) -> None:
    """Stand in for pandoc's `--print-default-data-file reference.pptx`."""
    with zipfile.ZipFile(dest, "w") as z:
        z.writestr(
            "[Content_Types].xml",
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"></Types>',
        )
        z.writestr(
            "ppt/presentation.xml",
            f'<p:presentation {_P}><p:sldSz cx="{SLIDE_CX}" cy="{SLIDE_CY}"/></p:presentation>',
        )
        z.writestr("ppt/theme/theme1.xml", _theme())
        z.writestr("ppt/theme/theme2.xml", _theme())  # the notes master has its own
        z.writestr("ppt/slideMasters/slideMaster1.xml", _master())
        index = 0
        for name, placeholders in LAYOUTS:
            if name == omit_layout:
                continue
            index += 1
            z.writestr(f"ppt/slideLayouts/slideLayout{index}.xml", _layout(name, placeholders))
            z.writestr(
                f"ppt/slideLayouts/_rels/slideLayout{index}.xml.rels",
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/'
                'relationships"></Relationships>',
            )


@pytest.fixture
def stub_pandoc(monkeypatch):
    """Replace the pandoc call with the synthetic deck above."""

    def install(*, omit_layout: str | None = None) -> None:
        monkeypatch.setattr(
            make_reference,
            "default_reference_pptx",
            lambda dest: _default_deck(dest, omit_layout=omit_layout),
        )

    return install


def _read(deck: Path, part: str) -> str:
    with zipfile.ZipFile(deck) as z:
        return z.read(part).decode("utf-8")


def _built(tmp_path: Path) -> Path:
    return build_reference(tmp_path / "reference.pptx")


# ── the happy path ───────────────────────────────────────────────────────────


def test_it_produces_a_deck_with_every_part_it_was_given(stub_pandoc, tmp_path):
    stub_pandoc()
    deck = _built(tmp_path)
    assert deck.is_file()
    with zipfile.ZipFile(deck) as z:
        names = set(z.namelist())
    assert "ppt/presentation.xml" in names
    assert len([n for n in names if THEME_RE.fullmatch(n)]) == 2
    # The intermediate download is cleaned up, not left beside the output.
    assert not (tmp_path / "reference.default.pptx").exists()


def test_every_office_colour_slot_becomes_a_literal_brand_colour(stub_pandoc, tmp_path):
    """Including dk1/lt1, which arrive as sysClr and must not stay that way."""
    stub_pandoc()
    theme = _read(_built(tmp_path), "ppt/theme/theme1.xml")
    assert "sysClr" not in theme
    brand_hexes = {v.lstrip("#").upper() for v in BRAND["colors"].values()}
    used = set(re.findall(r'<a:srgbClr val="([0-9A-F]{6})"/>', theme))
    assert used and used <= brand_hexes


def test_both_font_slots_become_the_brand_font(stub_pandoc, tmp_path):
    stub_pandoc()
    theme = _read(_built(tmp_path), "ppt/theme/theme1.xml")
    assert "Calibri" not in theme
    assert theme.count(f'<a:latin typeface="{BRAND["fonts"]["main"]}"/>') == 2


def test_the_notes_master_theme_is_patched_too(stub_pandoc, tmp_path):
    """Both theme parts, or the notes pages render stock Office."""
    stub_pandoc()
    deck = _built(tmp_path)
    assert _read(deck, "ppt/theme/theme1.xml") == _read(deck, "ppt/theme/theme2.xml")


def test_the_title_layout_gets_the_wedge_and_its_image(stub_pandoc, tmp_path):
    stub_pandoc()
    deck = _built(tmp_path)
    with zipfile.ZipFile(deck) as z:
        names = z.namelist()
        title = next(
            z.read(n).decode()
            for n in names
            if "slideLayout" in n and "Brand Wedge" in z.read(n).decode()
        )
    assert make_reference.TITLE_BG_MEDIA in names, "the wedge image must be embedded"
    assert "Brand Wedge Edge" in title, "the accent sliver along the diagonal"
    assert make_reference.TITLE_BG_REL_ID in title
    # The jpg content type has to be declared or PowerPoint rejects the part.
    assert 'Extension="jpg"' in _read(deck, "[Content_Types].xml")


def test_content_layouts_get_the_separator_and_footline(stub_pandoc, tmp_path):
    stub_pandoc()
    deck = _built(tmp_path)
    with zipfile.ZipFile(deck) as z:
        patched = {
            layout_name(z.read(n).decode()): z.read(n).decode()
            for n in z.namelist()
            if re.fullmatch(r"ppt/slideLayouts/slideLayout\d+\.xml", n)
        }
    for name in SEPARATOR_LAYOUTS:
        xml = patched[name]
        assert "Brand Separator" in xml, name
        assert "Brand Footline" in xml, name
        assert "Brand Footline Accent" in xml, name


def test_the_blank_layout_is_left_alone(stub_pandoc, tmp_path):
    """Only the named layouts are branded; anything else passes through."""
    stub_pandoc()
    with zipfile.ZipFile(_built(tmp_path)) as z:
        blank = next(
            z.read(n).decode()
            for n in z.namelist()
            if re.fullmatch(r"ppt/slideLayouts/slideLayout\d+\.xml", n)
            and layout_name(z.read(n).decode()) == "Blank"
        )
    assert "Brand" not in blank


def test_the_section_layout_goes_accent_on_dark(stub_pandoc, tmp_path):
    stub_pandoc()
    with zipfile.ZipFile(_built(tmp_path)) as z:
        section = next(
            z.read(n).decode()
            for n in z.namelist()
            if re.fullmatch(r"ppt/slideLayouts/slideLayout\d+\.xml", n)
            and layout_name(z.read(n).decode()) == "Section Header"
        )
    assert '<a:schemeClr val="dk1"/>' in section  # dark background
    assert '<a:schemeClr val="accent1"/>' in section  # accent title


def test_a_supplied_brand_is_used_instead_of_the_packaged_one(stub_pandoc, tmp_path):
    """The `brand` parameter exists so a test can drive it; prove it is honoured."""
    stub_pandoc()
    custom = {
        **BRAND,
        "colors": {**BRAND["colors"], "accent": "#ff0000"},
        "fonts": {**BRAND["fonts"], "main": "Comic Sans MS"},
    }
    deck = build_reference(tmp_path / "custom.pptx", brand=custom)
    theme = _read(deck, "ppt/theme/theme1.xml")
    assert '<a:srgbClr val="FF0000"/>' in theme
    assert '<a:latin typeface="Comic Sans MS"/>' in theme


# ── the guards ───────────────────────────────────────────────────────────────


def test_a_changed_slide_size_fails_loudly(stub_pandoc, tmp_path, monkeypatch):
    """Every patcher positions in EMU against a fixed slide size."""
    stub_pandoc()

    def wrong_size(dest: Path) -> None:
        _default_deck(dest)
        with zipfile.ZipFile(dest) as z:
            parts = {n: z.read(n) for n in z.namelist()}
        parts["ppt/presentation.xml"] = (
            f'<p:presentation {_P}><p:sldSz cx="1" cy="2"/></p:presentation>'.encode()
        )
        with zipfile.ZipFile(dest, "w") as z:
            for name, payload in parts.items():
                z.writestr(name, payload)

    monkeypatch.setattr(make_reference, "default_reference_pptx", wrong_size)
    with pytest.raises(ReferenceBuildError, match="Slide size changed"):
        _built(tmp_path)


@pytest.mark.parametrize("missing", ["Title Slide", "Section Header", SEPARATOR_LAYOUTS[0]])
def test_a_missing_layout_fails_loudly(stub_pandoc, tmp_path, missing: str):
    """Pandoc's default deck changing shape must not quietly half-brand a deck."""
    stub_pandoc(omit_layout=missing)
    with pytest.raises(ReferenceBuildError, match="Layouts not found"):
        _built(tmp_path)


def test_a_deck_with_no_theme_fails_loudly(tmp_path, monkeypatch):
    def no_theme(dest: Path) -> None:
        _default_deck(dest)
        with zipfile.ZipFile(dest) as z:
            parts = {n: z.read(n) for n in z.namelist() if not THEME_RE.fullmatch(n)}
        with zipfile.ZipFile(dest, "w") as z:
            for name, payload in parts.items():
                z.writestr(name, payload)

    monkeypatch.setattr(make_reference, "default_reference_pptx", no_theme)
    with pytest.raises(ReferenceBuildError, match="No ppt/theme"):
        _built(tmp_path)


def test_a_deck_with_no_master_fails_loudly(tmp_path, monkeypatch):
    """The content layouts read their title geometry from it."""

    def no_master(dest: Path) -> None:
        _default_deck(dest)
        with zipfile.ZipFile(dest) as z:
            parts = {n: z.read(n) for n in z.namelist() if "slideMaster" not in n}
        with zipfile.ZipFile(dest, "w") as z:
            for name, payload in parts.items():
                z.writestr(name, payload)

    monkeypatch.setattr(make_reference, "default_reference_pptx", no_master)
    with pytest.raises(ReferenceBuildError, match="No slide master"):
        _built(tmp_path)


def test_a_title_layout_without_a_rels_part_fails_loudly(tmp_path, monkeypatch):
    """The wedge image is attached through it, so a missing one loses the image."""

    def no_rels(dest: Path) -> None:
        _default_deck(dest)
        with zipfile.ZipFile(dest) as z:
            parts = {n: z.read(n) for n in z.namelist() if "slideLayouts/_rels" not in n}
        with zipfile.ZipFile(dest, "w") as z:
            for name, payload in parts.items():
                z.writestr(name, payload)

    monkeypatch.setattr(make_reference, "default_reference_pptx", no_rels)
    with pytest.raises(ReferenceBuildError, match="no rels part"):
        _built(tmp_path)


def test_the_emitted_deck_is_well_formed_xml(stub_pandoc, tmp_path):
    """Every patcher edits markup by hand; PowerPoint refuses a broken part."""
    from md2pdfLib.presentation.pptx.verify_brand import malformed_parts

    stub_pandoc()
    assert malformed_parts(_built(tmp_path)) == {}
