"""Tests for the sphinx-kataglyphis-theme contract downstream repos rely on."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from sphinx_kataglyphis import LINKS_EXTENSION, brand, brand_css_path, setup_theme

REPO_ROOT = Path(__file__).resolve().parents[1]


# brand()


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
    """One caller assigning into the result must not change the brand for the next."""
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


# setup_theme()


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
    """The book, the slides and the website must highlight code the same way."""
    setup_theme(conf)
    assert conf["html_theme_options"]["pygments_light_style"] == "kataglyphis-dark"
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
    assert conf["html_theme_options"]["pygments_light_style"] == "kataglyphis-dark"


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


# Links and branding defaults


def test_markdown_links_resolve_as_sphinx_targets(conf):
    """myst_all_links_external kept `x.md` verbatim, a 404 on every site."""
    setup_theme(conf)
    assert not conf.get("myst_all_links_external")
    assert conf["myst_heading_anchors"] == 6
    assert LINKS_EXTENSION in conf["extensions"]


def test_heading_anchors_set_in_conf_py_survive(conf):
    conf["myst_heading_anchors"] = 2
    setup_theme(conf)
    assert conf["myst_heading_anchors"] == 2


def test_the_family_logo_is_the_default_logo_and_favicon(conf):
    setup_theme(conf)
    logo = Path(conf["html_logo"])
    assert logo.is_file()
    assert conf["html_favicon"] == conf["html_logo"]
    assert logo.read_bytes() == (REPO_ROOT / "images" / logo.name).read_bytes()


def test_the_project_name_is_the_page_title_and_logo_text(conf):
    """Sphinx's default title doubled "documentation" on an index titled "<x> documentation"."""
    setup_theme(conf, project_name="Hub", release="1.0")
    assert conf["html_title"] == "Hub"
    assert conf["html_theme_options"]["logo"] == {"text": "Hub"}


def test_no_title_is_invented_without_a_project(conf):
    setup_theme(conf)
    assert "html_title" not in conf
    assert "logo" not in conf["html_theme_options"]


def test_explicit_branding_wins(conf):
    conf["html_logo"] = "mine.png"
    setup_theme(
        conf,
        project_name="Hub",
        theme_options_extra={"logo": {"text": "Other"}},
        html_title="Custom",
        html_favicon="mine.ico",
    )
    assert conf["html_logo"] == "mine.png"
    assert conf["html_favicon"] == "mine.ico"
    assert conf["html_title"] == "Custom"
    assert conf["html_theme_options"]["logo"] == {"text": "Other"}


# auto_discover


def test_auto_discover_writes_an_index_over_the_sources_it_finds(conf, tmp_path):
    (tmp_path / "getting-started.md").write_text("# Start", encoding="utf-8")
    (tmp_path / "architecture.rst").write_text("Arch\n====\n", encoding="utf-8")
    setup_theme(conf, auto_discover=True, source_dir=str(tmp_path), project_name="Mine")

    index = (tmp_path / "index.md").read_text(encoding="utf-8")
    assert index.startswith("# Mine")
    assert "```{toctree}" in index
    # Referenced without their extensions, which is what a toctree wants.
    assert "getting-started" in index and "architecture" in index
    assert ".md" not in index and ".rst" not in index


def test_auto_discover_never_lists_index_itself(conf, tmp_path):
    """A toctree that includes its own page makes Sphinx warn, failing -W builds."""
    (tmp_path / "page.md").write_text("# Page", encoding="utf-8")
    (tmp_path / "INDEX.md").write_text("# Shouting", encoding="utf-8")
    # INDEX.md counts as an index, so nothing should be generated at all.
    setup_theme(conf, auto_discover=True, source_dir=str(tmp_path))
    assert not (tmp_path / "index.md").exists() or "INDEX" not in (tmp_path / "index.md").read_text(
        encoding="utf-8"
    )


def test_auto_discover_leaves_a_hand_written_index_alone(conf, tmp_path):
    """Overwriting someone's landing page would be a data-loss bug."""
    (tmp_path / "index.md").write_text("# Mine, hand written", encoding="utf-8")
    (tmp_path / "page.md").write_text("# Page", encoding="utf-8")
    setup_theme(conf, auto_discover=True, source_dir=str(tmp_path))
    assert (tmp_path / "index.md").read_text(encoding="utf-8") == "# Mine, hand written"


def test_auto_discover_respects_an_rst_index_too(conf, tmp_path):
    (tmp_path / "index.rst").write_text("Mine\n====\n", encoding="utf-8")
    setup_theme(conf, auto_discover=True, source_dir=str(tmp_path))
    assert not (tmp_path / "index.md").exists()


def test_auto_discover_is_off_by_default(conf, tmp_path):
    (tmp_path / "page.md").write_text("# Page", encoding="utf-8")
    setup_theme(conf, source_dir=str(tmp_path))
    assert not (tmp_path / "index.md").exists()


# The scaffold CLI


def test_scaffold_writes_a_doc_directory_that_builds(tmp_path, monkeypatch):
    """`python -m sphinx_kataglyphis scaffold docs` is the advertised first step."""
    import sphinx_kataglyphis

    dest = tmp_path / "docs"
    monkeypatch.setattr("sys.argv", ["sphinx-kataglyphis", "scaffold", str(dest)])
    sphinx_kataglyphis.main()

    assert (dest / "conf.py").is_file()
    assert (dest / "Makefile").is_file()
    assert (dest / "make.bat").is_file()
    assert (dest / "_static" / "css" / "custom-overrides.css").is_file()
    assert (dest / "_build").is_dir()

    # The generated conf.py must be valid Python that calls setup_theme.
    source = (dest / "conf.py").read_text(encoding="utf-8")
    compile(source, str(dest / "conf.py"), "exec")
    assert "from sphinx_kataglyphis import setup_theme" in source


def test_the_scaffolded_overrides_file_teaches_tokens_not_literals(tmp_path, monkeypatch):
    """The whole point of the brand pipeline: no hex written by hand."""
    import re as _re

    import sphinx_kataglyphis

    dest = tmp_path / "docs"
    monkeypatch.setattr("sys.argv", ["sphinx-kataglyphis", "scaffold", str(dest)])
    sphinx_kataglyphis.main()
    css = (dest / "_static" / "css" / "custom-overrides.css").read_text(encoding="utf-8")
    assert "var(--brand-" in css
    assert not _re.search(r"#[0-9a-fA-F]{6}\b", css)


def test_scaffold_does_not_clobber_an_existing_conf(tmp_path, monkeypatch, capsys):
    import sphinx_kataglyphis

    dest = tmp_path / "docs"
    dest.mkdir()
    (dest / "conf.py").write_text("# mine\n", encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["sphinx-kataglyphis", "scaffold", str(dest)])
    sphinx_kataglyphis.main()
    assert (dest / "conf.py").read_text(encoding="utf-8") == "# mine\n"
    assert "already exists" in capsys.readouterr().out


def test_scaffold_is_idempotent(tmp_path, monkeypatch):
    """Running it twice must not change what the first run produced."""
    import sphinx_kataglyphis

    dest = tmp_path / "docs"
    monkeypatch.setattr("sys.argv", ["sphinx-kataglyphis", "scaffold", str(dest)])
    sphinx_kataglyphis.main()
    before = {p.name: p.read_bytes() for p in dest.rglob("*") if p.is_file()}
    sphinx_kataglyphis.main()
    after = {p.name: p.read_bytes() for p in dest.rglob("*") if p.is_file()}
    assert before == after


def test_scaffold_defaults_to_a_docs_directory(tmp_path, monkeypatch):
    import sphinx_kataglyphis

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("sys.argv", ["sphinx-kataglyphis", "scaffold"])
    sphinx_kataglyphis.main()
    assert (tmp_path / "docs" / "conf.py").is_file()


def test_the_cli_requires_a_command(monkeypatch):
    import sphinx_kataglyphis

    monkeypatch.setattr("sys.argv", ["sphinx-kataglyphis"])
    with pytest.raises(SystemExit) as exc:
        sphinx_kataglyphis.main()
    assert exc.value.code == 2


def test_the_module_is_runnable_as_advertised(tmp_path):
    """A subprocess, because __main__.py only runs under `python -m sphinx_kataglyphis`."""
    import subprocess
    import sys

    dest = tmp_path / "docs"
    result = subprocess.run(
        [sys.executable, "-m", "sphinx_kataglyphis", "scaffold", str(dest)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert (dest / "conf.py").is_file()
    assert "scaffold complete" in result.stdout


# Identity reaches downstream repos


def test_author_and_copyright_fall_back_to_the_brand_identity(conf):
    """A consuming repo inherits author and copyright the way it inherits the colours."""
    setup_theme(conf)
    identity = brand()["identity"]
    assert conf["author"] == identity["name"]
    assert conf["copyright"] == f"{identity['copyright_year']}, {identity['name']}"


def test_an_explicit_author_still_wins(conf):
    """A project with a different author must not be overwritten by the brand."""
    setup_theme(conf, author="Someone Else", copyright_="1999, Someone Else")
    assert conf["author"] == "Someone Else"
    assert conf["copyright"] == "1999, Someone Else"


def test_a_value_already_in_conf_py_still_wins(conf):
    """setdefault semantics, unchanged: conf.py beats both the call and the brand."""
    conf["author"] = "Set In Conf"
    conf["copyright"] = "2000, Set In Conf"
    setup_theme(conf, author="Passed In")
    assert conf["author"] == "Set In Conf"
    assert conf["copyright"] == "2000, Set In Conf"
