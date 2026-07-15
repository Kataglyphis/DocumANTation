"""Tests for the brand-style generator (style/brand.json -> derived files)."""

from __future__ import annotations

import pytest

from style.generate_style import (
    apply_css_block,
    apply_yaml_block,
    desired_outputs,
    load_brand,
    render_css_block,
    render_latex,
    render_latex_fonts,
    render_yaml_block,
)

BRAND = {
    "colors": {
        "accent": "#6af0ad",
        "accent_strong": "#2ad488",
        "accent_soft": "#e9fbf2",
        "text_main": "#1f2a24",
        "surface_soft": "#f7fbf9",
        "surface_border": "#dcefe5",
    },
    "fonts": {"main": "Roboto"},
}


def test_latex_uses_uppercase_hex_without_hash():
    out = render_latex(BRAND)
    assert "\\definecolor{brandAccent}{HTML}{6AF0AD}" in out
    assert "#" not in out


def test_latex_defines_the_aliases_documents_rely_on():
    out = render_latex(BRAND)
    for alias in ("greenAccent", "myGreenAccent", "basecolor"):
        assert f"\\colorlet{{{alias}}}{{brandAccent}}" in out


def test_latex_fonts_are_safe_to_input_twice():
    out = render_latex_fonts(BRAND)
    # \newcommand would raise "already defined" on a second \input.
    assert "\\newcommand" not in out
    assert "\\providecommand{\\brandMainFont}{Roboto}" in out
    assert "\\providecommand{\\brandSetMainFont}{\\setmainfont{Roboto}}" in out


def test_css_block_exposes_color_and_font_tokens():
    out = render_css_block(BRAND)
    assert "--brand-accent: #6af0ad;" in out
    assert "--brand-font-main: 'Roboto', sans-serif;" in out


def test_css_bootstraps_from_an_unmarked_root_block():
    css = ":root {\n  --brand-accent: #old;\n}\n\nbody { color: red; }\n"
    out = apply_css_block(css, render_css_block(BRAND))
    assert "#old" not in out
    assert "--brand-accent: #6af0ad;" in out
    assert "body { color: red; }" in out  # unrelated rules survive


def test_css_update_is_idempotent():
    block = render_css_block(BRAND)
    once = apply_css_block(":root {\n  --brand-accent: #old;\n}\n", block)
    twice = apply_css_block(once, block)
    assert once == twice


def test_yaml_bootstraps_from_a_plain_mainfont_line():
    yml = "theme:\n  - awesome\nmainfont: Georgia #DejaVuSerif\nmonofont: FreeMono\n"
    out = apply_yaml_block(yml, render_yaml_block(BRAND))
    assert "mainfont: Roboto" in out
    assert "Georgia" not in out
    assert "monofont: FreeMono" in out  # neighbouring keys untouched


def test_yaml_update_is_idempotent():
    block = render_yaml_block(BRAND)
    once = apply_yaml_block("mainfont: Georgia\ntitle: x\n", block)
    twice = apply_yaml_block(once, block)
    assert once == twice
    assert "title: x" in twice


def test_yaml_without_mainfont_is_an_error_not_a_silent_noop():
    with pytest.raises(SystemExit):
        apply_yaml_block("title: x\n", render_yaml_block(BRAND))


def test_repo_brand_json_renders_every_target():
    # Guards against a token being added to brand.json but never consumed.
    brand = load_brand()
    assert brand["colors"]["accent"].startswith("#")
    assert brand["fonts"]["main"]
    targets = {p.name for p in desired_outputs()}
    assert {"brand-colors.tex", "brand-fonts.tex", "base.yml", "metadata.yml"} <= targets
