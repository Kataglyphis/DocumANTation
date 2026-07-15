"""Tests for the sphinx-kataglyphis-theme package.

The generator (style/generate_style.py) is well covered, but the package that
*ships* the brand to every downstream repo had no tests at all -- so nothing
caught the drifted conf_base.py that left this repo's own docs site without a
code palette. These cover the contract downstream projects actually depend on:
brand() and setup_theme().
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from sphinx_kataglyphis import brand, brand_css_path, setup_theme

REPO_ROOT = Path(__file__).resolve().parents[1]


# ── brand() ──────────────────────────────────────────────────────────────────


def test_brand_exposes_the_documented_tokens():
    tokens = brand()
    assert tokens["colors"]["accent"].startswith("#")
    assert tokens["colors_dark"]["link"].startswith("#")
    assert tokens["fonts"]["main"]


def test_brand_has_no_unresolved_aliases():
    """The packaged copy is the resolved one -- consumers need no alias support."""
    for section in ("colors", "colors_dark", "syntax", "syntax_dark"):
        for key, value in brand()[section].items():
            assert not str(value).startswith("@"), f"{section}.{key} still an alias"


def test_brand_is_immune_to_caller_mutation():
    """One caller assigning into the result must not change the brand for the next.

    The parse is cached; handing out the cached dict itself made the brand
    editable at a distance.
    """
    original = brand()["colors"]["accent"]
    brand()["colors"]["accent"] = "#ff0000"
    brand()["colors"].pop("link", None)
    assert brand()["colors"]["accent"] == original
    assert "link" in brand()["colors"]


def test_packaged_tokens_match_the_source_of_truth():
    """The copy inside the wheel must not drift from style/brand.tokens.json."""
    canonical = json.loads((REPO_ROOT / "style" / "brand.tokens.json").read_text("utf-8"))
    assert brand() == canonical


def test_brand_css_ships_with_the_package():
    css = brand_css_path()
    assert css.is_file()
    assert f"--brand-accent: {brand()['colors']['accent']}" in css.read_text("utf-8")


# ── setup_theme() ────────────────────────────────────────────────────────────


@pytest.fixture
def conf(tmp_path: Path) -> dict:
    """A conf.py namespace, as Sphinx would exec it."""
    return {"__file__": str(tmp_path / "conf.py")}


def test_setup_theme_applies_the_brand(conf):
    setup_theme(conf)
    assert conf["html_theme"] == "sphinx_book_theme"
    assert "css/custom.css" in conf["html_css_files"]
    assert any("_static" in p for p in conf["html_static_path"])


def test_setup_theme_wires_the_shared_code_palette(conf):
    """The book, the slides and the website must highlight code the same way.

    A drifted baseline that omitted these is why this repo's own site rendered
    code with stock Pygments colours instead of the brand.
    """
    setup_theme(conf)
    assert conf["html_theme_options"]["pygments_light_style"] == "kataglyphis-light"
    assert conf["html_theme_options"]["pygments_dark_style"] == "kataglyphis-dark"


def test_registered_pygments_styles_use_the_brand():
    pygments_styles = pytest.importorskip("pygments.styles")
    for name, section in (("kataglyphis-light", "syntax"), ("kataglyphis-dark", "syntax_dark")):
        style = pygments_styles.get_style_by_name(name)
        rendered = " ".join(style.styles.values()).lower()
        assert brand()[section]["keyword"].lower() in rendered


def test_package_static_comes_last_so_a_local_fork_cannot_win(conf, tmp_path):
    """Two same-named stylesheets: the packaged one must overwrite the local one."""
    (tmp_path / "_static").mkdir()
    setup_theme(conf)
    paths = conf["html_static_path"]
    assert paths[0] == "_static"
    assert "sphinx_kataglyphis" in paths[-1]


def test_no_static_path_entry_when_the_project_has_no_static_dir(conf):
    """Listing a missing dir makes Sphinx warn, which fails the -W builds."""
    setup_theme(conf)
    assert "_static" not in conf["html_static_path"]


def test_extras_extend_rather_than_replace(conf):
    setup_theme(
        conf,
        extensions_extra=["sphinx.ext.autodoc"],
        theme_options_extra={"show_toc_level": 9},
        html_css_files_extra=["css/mine.css"],
    )
    assert {"myst_parser", "sphinx_design", "sphinx.ext.autodoc"} <= set(conf["extensions"])
    assert conf["html_css_files"] == ["css/custom.css", "css/mine.css"]
    assert conf["html_theme_options"]["show_toc_level"] == 9
    # Extending options must not drop the rest of the baseline.
    assert conf["html_theme_options"]["pygments_light_style"] == "kataglyphis-light"


def test_repository_button_only_when_there_is_a_repository(conf):
    setup_theme(conf)
    assert conf["html_theme_options"]["use_repository_button"] is False
    assert "repository_url" not in conf["html_theme_options"]

    other: dict = {"__file__": conf["__file__"]}
    setup_theme(other, repository_url="https://github.com/org/repo")
    assert other["html_theme_options"]["use_repository_button"] is True
    assert other["html_theme_options"]["repository_url"] == "https://github.com/org/repo"


def test_conf_py_metadata_wins_over_the_defaults(conf):
    """Metadata is setdefault, so a project's own values survive the call."""
    conf["project"] = "Mine"
    setup_theme(conf, project_name="Theirs", author="A", release="1.2.3")
    assert conf["project"] == "Mine"
    assert conf["author"] == "A"
    assert conf["release"] == "1.2.3"


def test_release_is_not_invented(conf):
    """A truthy default silently published every project as version 0.0.1."""
    setup_theme(conf)
    assert not conf.get("release")


def test_extra_conf_wins_over_the_baseline(conf):
    setup_theme(conf, html_title="Custom", myst_heading_anchors=3)
    assert conf["html_title"] == "Custom"
    assert conf["myst_heading_anchors"] == 3
