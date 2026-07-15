"""Tests for the brand-style generator (style/brand.json -> derived files)."""

from __future__ import annotations

import json
import re

import pytest

from style.generate_style import (
    PYGMENTS_TOKENS,
    SYNTAX_TOKENS,
    _resolve_group,
    apply_css_block,
    apply_yaml_block,
    desired_outputs,
    load_brand,
    render_css_block,
    render_latex,
    render_latex_fonts,
    render_pygments_module,
    render_syntax_theme,
    render_tokens_json,
    render_yaml_block,
    resolve_brand,
)

RAW_BRAND = {
    "name": "Test",
    "colors": {
        "white": "#ffffff",
        "accent": "#6af0ad",
        "accent_strong": "#2ad488",
        "accent_soft": "#e9fbf2",
        "link": "#1ca06a",
        "text_main": "#1f2a24",
        "text_on_accent": "@white",
    },
    "colors_dark": {"link": "#7df5ba", "hero_text": "@accent"},
    "syntax": {
        "fg": "#111111",
        "bg": "#f6f8fa",
        "line_number": "@comment",
        "line_number_bg": "#ffffff",
        "comment": "#6a737d",
        "keyword": "#d73a49",
        "error": "#b31d28",
        "error_bg": "#ffebee",
        "string": "#032f62",
        "constant": "#005cc5",
        "float": "@constant",
        "function": "#6f42c1",
        "type": "@function",
        "preprocessor": "#e36209",
        "warning": "@preprocessor",
        "attribute": "#22863a",
    },
    "syntax_dark": {
        "fg": "#c9d1d9",
        "bg": "#0d1117",
        "line_number": "@comment",
        "line_number_bg": "#161b22",
        "comment": "#8b949e",
        "keyword": "#ff7b72",
        "error": "@keyword",
        "error_bg": "#2d0b0f",
        "string": "#a5d6ff",
        "constant": "#79c0ff",
        "float": "#ae81ff",
        "function": "#d2a8ff",
        "type": "#ffa657",
        "preprocessor": "@type",
        "warning": "@type",
        "attribute": "#7ee787",
    },
    "fonts": {
        "main": "Roboto",
        "main_weights": "400;700",
        "mono": "Latin Modern Mono",
        "mono_options": ["Scale=1", "BoldFont=lmmonolt10-bold.otf"],
    },
}

# The render_* functions require resolved input, exactly as load_brand() supplies it.
BRAND = resolve_brand(RAW_BRAND)


# -- alias resolution: the "never write a literal twice" guarantee -------------


def test_alias_resolves_within_a_group():
    out = _resolve_group({"white": "#ffffff", "text_on_accent": "@white"})
    assert out["text_on_accent"] == "#ffffff"


def test_dark_group_can_alias_into_the_light_group():
    colors = _resolve_group(BRAND["colors"])
    dark = _resolve_group(RAW_BRAND["colors_dark"], fallback=colors)
    assert dark["hero_text"] == "#6af0ad"


def test_alias_chain_resolves():
    out = _resolve_group({"a": "#123456", "b": "@a", "c": "@b"})
    assert out["c"] == "#123456"


def test_alias_cycle_is_reported_not_hung_on():
    with pytest.raises(SystemExit):
        _resolve_group({"a": "@b", "b": "@a"})


def test_unknown_alias_is_an_error():
    with pytest.raises(SystemExit):
        _resolve_group({"a": "@nope"})


# -- LaTeX --------------------------------------------------------------------


def test_latex_uses_uppercase_hex_without_hash():
    out = render_latex(BRAND)
    assert "\\definecolor{brandAccent}{HTML}{6AF0AD}" in out
    assert "#" not in out


def test_latex_defines_the_aliases_documents_rely_on():
    out = render_latex(BRAND)
    for alias in ("greenAccent", "myGreenAccent", "basecolor"):
        assert f"\\colorlet{{{alias}}}{{brandAccent}}" in out


def test_latex_defines_the_shared_link_colour():
    out = render_latex(BRAND)
    assert "\\definecolor{brandLink}{HTML}{1CA06A}" in out
    # The book, the CV and the slides all resolve `linkcolor` from here.
    assert "\\colorlet{linkcolor}{brandLink}" in out


def test_latex_fonts_are_safe_to_input_twice():
    out = render_latex_fonts(BRAND)
    # \newcommand would raise "already defined" on a second \input.
    assert "\\newcommand" not in out
    assert "\\providecommand{\\brandMainFont}{Roboto}" in out
    assert "\\providecommand{\\brandSetMainFont}{\\setmainfont{Roboto}}" in out


def test_latex_mono_carries_its_options():
    # Scale=1 defeats Pandoc's Scale=MatchLowercase; without it the mono is
    # widened against Roboto and the book's line breaking regresses.
    out = render_latex_fonts(BRAND)
    assert "\\brandMonoFont}{Latin Modern Mono}" in out
    assert "\\setmonofont[Scale=1,BoldFont=lmmonolt10-bold.otf]{Latin Modern Mono}" in out


# -- CSS ----------------------------------------------------------------------


def test_css_block_carries_fonts_import_and_every_token():
    out = render_css_block(BRAND)
    assert "family=Roboto:wght@400;700" in out
    assert "--brand-font-main: 'Roboto', sans-serif;" in out
    assert "--brand-accent: #6af0ad;" in out
    assert "--brand-text-on-accent: #ffffff;" in out  # alias resolved


def test_css_omits_the_tex_mono_font():
    # fonts.mono names a TeX font no browser has; emitting it would suggest the
    # web renders code in it.
    assert "--brand-font-mono" not in render_css_block(BRAND)


def test_dark_tokens_get_their_own_names_and_never_shadow_light_ones():
    out = render_css_block(BRAND)
    assert "--brand-dark-link: #7df5ba;" in out
    # A second `--brand-link:` would retint every var(--brand-link) use in dark
    # mode, which is exactly the silent breakage we avoid.
    assert len(re.findall(r"^\s*--brand-link:", out, re.M)) == 1


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


# -- Pandoc YAML --------------------------------------------------------------


def test_yaml_block_sets_font_and_link_colour_by_name():
    out = render_yaml_block(BRAND)
    assert "mainfont: Roboto" in out
    assert "monofont: Latin Modern Mono" in out
    assert "monofontoptions:\n  - Scale=1\n  - BoldFont=lmmonolt10-bold.otf" in out
    # Naming the LaTeX colour keeps the hex in brand-colors.tex only.
    for key in ("linkcolor", "urlcolor", "citecolor"):
        assert f"{key}: brandLink" in out


def test_yaml_bootstraps_from_a_plain_mainfont_line():
    yml = "theme:\n  - awesome\nmainfont: Georgia #DejaVuSerif\ntoc: true\n"
    out = apply_yaml_block(yml, render_yaml_block(BRAND))
    assert "mainfont: Roboto" in out
    assert "Georgia" not in out
    assert "toc: true" in out  # neighbouring keys untouched


def test_hand_written_managed_keys_are_removed():
    # A document must not be able to quietly re-specify the brand.
    yml = "mainfont: Georgia\nmonofont: Courier\nlinkcolor: blue\ntitle: keep me\n"
    out = apply_yaml_block(yml, render_yaml_block(BRAND))
    assert "Courier" not in out
    assert "linkcolor: blue" not in out
    assert "title: keep me" in out
    assert out.count("mainfont:") == 1


def test_yaml_update_is_idempotent():
    block = render_yaml_block(BRAND)
    once = apply_yaml_block("mainfont: Georgia\ntitle: x\n", block)
    twice = apply_yaml_block(once, block)
    assert once == twice
    assert "title: x" in twice


def test_yaml_without_mainfont_is_an_error_not_a_silent_noop():
    with pytest.raises(SystemExit):
        apply_yaml_block("title: x\n", render_yaml_block(BRAND))


# -- The real brand.json ------------------------------------------------------


def test_tokens_json_is_fully_resolved_for_other_applications():
    payload = render_tokens_json(load_brand())
    assert "@" not in re.sub(r'"_comment":.*', "", payload)  # no unresolved aliases


def test_repo_brand_json_renders_every_target():
    brand = load_brand()
    assert brand["colors"]["accent"].startswith("#")
    assert brand["fonts"]["main"]
    targets = {p.name for p in desired_outputs()}
    assert {
        "brand-colors.tex",
        "brand-fonts.tex",
        "brand.tokens.json",
        "base.yml",
        "metadata.yml",
        "custom.css",
    } <= targets


def test_web_style_has_exactly_one_css_target():
    # A second CSS target would mean the style is copied, which is how the old
    # source_templates/sphinx-book/custom.css silently drifted ~270 lines.
    css = [p for p in desired_outputs() if p.suffix == ".css"]
    assert len(css) == 1


def test_resolve_brand_is_idempotent():
    once = resolve_brand(RAW_BRAND)
    assert resolve_brand(once) == once


def test_tokens_ship_inside_the_installable_package():
    # Without this, `pip install sphinx-kataglyphis-theme` gives you the CSS but
    # no way to read the brand from Python, and projects re-type the hex.
    targets = [p for p in desired_outputs() if p.name == "brand.tokens.json"]
    assert len(targets) == 2
    assert any("sphinx_kataglyphis" in p.parts for p in targets)
    # Both copies are generated from the same render, so they cannot diverge.
    assert len({desired_outputs()[p] for p in targets}) == 1


# -- Code highlighting: shared between the PDFs and the website ---------------


def test_syntax_theme_is_a_valid_pandoc_theme():
    payload = json.loads(render_syntax_theme(BRAND["syntax"]))
    assert payload["background-color"] == "#f6f8fa"
    assert set(payload["text-styles"]) == set(SYNTAX_TOKENS)
    assert payload["text-styles"]["Keyword"] == {
        "text-color": "#d73a49",
        "background-color": None,
        "bold": True,
        "italic": False,
        "underline": False,
    }
    # Error is the only token with a background.
    assert payload["text-styles"]["Error"]["background-color"] == "#ffebee"
    assert payload["text-styles"]["Extension"]["text-color"] is None


def test_pygments_and_pandoc_draw_from_the_same_palette():
    # The whole point: a code block must not look different in the book and on
    # the website. Neither mapping may reference a key the palettes don't have.
    pandoc_keys = {key for key, _, _ in SYNTAX_TOKENS.values() if key}
    pygments_keys = {key for _, key, _ in PYGMENTS_TOKENS}
    for palette in (BRAND["syntax"], BRAND["syntax_dark"]):
        assert pandoc_keys <= set(palette), pandoc_keys - set(palette)
        assert pygments_keys <= set(palette), pygments_keys - set(palette)


def test_pygments_module_defines_both_registered_styles():
    out = render_pygments_module(BRAND)
    assert 'name = "kataglyphis-light"' in out
    assert 'name = "kataglyphis-dark"' in out
    assert 'background_color = "#0d1117"' in out
    assert 'Keyword: "bold #ff7b72",' in out
    assert 'Keyword: "bold #d73a49",' in out


def test_pygments_module_is_importable_python():
    compile(render_pygments_module(BRAND), "highlight.py", "exec")
