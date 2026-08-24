"""Tests for the sphinx-kataglyphis-theme package.

The generator (style/generate_style.py) is well covered, but the package that
*ships* the brand to every downstream repo had no tests at all -- so nothing
caught the drifted conf_base.py that left this repo's own docs site without a
code palette. These cover the contract downstream projects actually depend on:
brand() and setup_theme().
"""

from __future__ import annotations

import json
import re
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


# ── the frozen path-loaded baseline ──────────────────────────────────────────
#
# docs-tooling/source_templates/sphinx-book/conf_base.py is loaded by
# *filesystem path* from two repos' docs/source/conf.py -- Kataglyphis-Cpp-Inference
# and Kataglyphis-BeschleunigerBallett -- each reading the same five constants off
# it. Nothing in this repo imports it, so nothing here would otherwise notice a
# rename, a brand literal creeping back in, or a Pygments style that only exists
# once sphinx-kataglyphis-theme is installed -- neither consumer installs it.
# These tests stand in for the two builds this repo cannot run.


def _load_conf_base():
    import importlib.util

    path = REPO_ROOT / "docs-tooling" / "source_templates" / "sphinx-book" / "conf_base.py"
    assert path.is_file(), f"{path} is loaded by path from another repo -- keep it"
    spec = importlib.util.spec_from_file_location("conf_base_under_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CONF_BASE_CONTRACT = (
    "SPHINX_EXTENSIONS",
    "HTML_THEME",
    "HTML_THEME_OPTIONS",
    "HTML_STATIC_PATH",
    "HTML_CSS_FILES",
)


def test_the_path_loaded_baseline_keeps_every_constant_its_consumer_reads():
    base = _load_conf_base()
    for name in CONF_BASE_CONTRACT:
        assert hasattr(base, name), (
            f"{name} is read by the conf.py of Kataglyphis-Cpp-Inference and "
            "Kataglyphis-BeschleunigerBallett; renaming it breaks both builds "
            "with no failure here"
        )


def _builtin_pygments_styles() -> set[str]:
    """The styles Pygments itself ships, excluding entry-point registrations.

    Not ``get_all_styles()``: that also yields styles registered by installed
    packages, so in *this* repo's venv -- where sphinx-kataglyphis-theme is a dev
    dependency -- it happily contains "kataglyphis-dark", and a check built on it
    passes for exactly the value it exists to reject.
    """
    import pygments.styles as styles

    builtin = getattr(styles, "_STYLE_NAME_TO_MODULE_MAP", None)
    if builtin is None:  # pragma: no cover - older Pygments
        builtin = styles.STYLE_MAP
    return set(builtin)


def test_the_path_loaded_baseline_needs_only_pygments_own_styles():
    """It cannot name kataglyphis-dark: its consumer has no theme package.

    Sphinx fails on an unregistered style, so a style that only the theme
    package provides would turn that site's build red -- while still passing
    here, because this venv does install the package.
    """
    shipped = _builtin_pygments_styles()
    assert "kataglyphis-dark" not in shipped, "guard is inert if the brand style is built in"
    options = _load_conf_base().HTML_THEME_OPTIONS
    for slot in ("pygments_light_style", "pygments_dark_style"):
        assert options[slot] in shipped, (
            f"{options[slot]} is not a style Pygments ships; the consumer that "
            "loads this file does not install sphinx-kataglyphis-theme"
        )


def test_the_path_loaded_baseline_highlights_dark_in_both_colour_modes():
    """The generated custom.css paints div.highlight dark in *both* modes.

    A light token set on that background is unreadable, not merely off-brand:
    the previous pairing put #515151 comments on #1a2d23 at 1.8:1, well under
    WCAG AA. Both slots must therefore be the same dark style.
    """
    from pygments.styles import get_style_by_name

    options = _load_conf_base().HTML_THEME_OPTIONS
    assert options["pygments_light_style"] == options["pygments_dark_style"]
    style = get_style_by_name(options["pygments_light_style"])
    assert style.background_color.lower() == brand()["syntax_dark"]["bg"].lower(), (
        "the stand-in palette must be built for the same background as the "
        "brand's own dark syntax palette"
    )


def _string_literals(value: object):
    """Every string reachable inside *value*, walking dicts and sequences."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from _string_literals(key)
            yield from _string_literals(item)
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            yield from _string_literals(item)


def test_the_path_loaded_baseline_writes_no_brand_value_of_its_own():
    """Colours reach it through the generated custom.css, never by hand.

    Checked against the module's *values*, not its source text. Its comments
    legitimately quote the brand background the stand-in palette was chosen to
    match, and a line-based comment stripper cannot tell those from a literal:
    it reads the ``#`` of ``"#6af0ad"`` as the start of a comment and discards
    the very colour it was looking for.
    """
    hex_colour = re.compile(r"#[0-9a-fA-F]{6}\b")
    base = _load_conf_base()
    for name in dir(base):
        if name.startswith("__"):
            continue
        for text in _string_literals(getattr(base, name)):
            assert not hex_colour.search(text), (
                f"{name} carries the colour {text!r}; brand values belong in "
                "style/brand.json and reach this file through custom.css"
            )


def test_the_path_loaded_baseline_claims_no_repository_of_its_own():
    """It is shared, so it cannot know whose repo it is.

    It used to hardcode ContainerHub's URL, pointing every consumer's
    repository button at the wrong project.
    """
    assert "repository_url" not in _load_conf_base().HTML_THEME_OPTIONS


# The shim's docstring says it "tracks setup_theme()'s options", and for a long
# time nothing checked that it did. It drifted at least twice on record -- once
# blanking `secondary_sidebar_items`, so the one site on this route was the only
# Kataglyphis site with no page TOC, and once pointing the repository button at
# ContainerHub. Both were found by looking, and fixed by hand.
#
# Everything the two sides deliberately disagree on, and why:
CONF_BASE_MAY_DIFFER = {
    # setup_theme names the theme package's own style; the shim cannot, because
    # neither consumer installs the package. Pinned instead by
    # test_the_path_loaded_baseline_needs_only_pygments_own_styles above.
    "pygments_light_style",
    "pygments_dark_style",
    # setup_theme derives it from the repository_url it was handed; the shim has
    # no argument to derive it from and leaves the button on for its consumers,
    # which set repository_url on their own copy afterwards.
    "use_repository_button",
}


def _setup_theme_options() -> dict:
    conf: dict = {"__file__": "conf.py"}
    setup_theme(conf)
    return conf["html_theme_options"]


def test_the_path_loaded_baseline_tracks_setup_themes_theme_options():
    """Same keys, same values, except the ones listed as deliberate.

    Without this, a navbar depth or TOC level changed in setup_theme() leaves
    the path-loaded consumers on the old value and every test still passes --
    which is how the missing page TOC survived.
    """
    shim = _load_conf_base().HTML_THEME_OPTIONS
    canonical = _setup_theme_options()

    assert set(shim) == set(canonical) - {"repository_url"}, (
        "the shim and setup_theme() offer different theme-option keys; add the "
        "new one to both, or to CONF_BASE_MAY_DIFFER with the reason"
    )
    drifted = {
        key: (shim[key], canonical[key])
        for key in set(shim) - CONF_BASE_MAY_DIFFER
        if shim[key] != canonical[key]
    }
    assert not drifted, (
        f"the shim has drifted from setup_theme(): {drifted}. Both render the "
        "same brand on different sites, so they cannot disagree silently."
    )


def test_the_path_loaded_baseline_tracks_setup_themes_theme_and_stylesheets():
    """The theme and its stylesheet are the same on either route."""
    base = _load_conf_base()
    conf: dict = {"__file__": "conf.py"}
    setup_theme(conf)

    assert conf["html_theme"] == base.HTML_THEME
    assert conf["html_css_files"] == base.HTML_CSS_FILES
    assert base.HTML_STATIC_PATH == ["_static"], (
        "the shim's consumers have no packaged _static to add, so this stays "
        "the consumer's own directory"
    )


def test_the_path_loaded_baseline_tracks_setup_themes_extensions():
    """A site missing sphinx_design renders its cards as raw directives."""
    conf: dict = {"__file__": "conf.py"}
    setup_theme(conf)
    assert conf["extensions"] == _load_conf_base().SPHINX_EXTENSIONS


# ── auto_discover ────────────────────────────────────────────────────────────
#
# setup_theme(auto_discover=True) writes an index.md with a toctree over the
# sources it finds, and the scaffold CLI below writes a whole doc directory.
# Both are documented entry points a downstream project uses on day one, and
# neither had a test -- invisible because the package was outside --cov.


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


# ── the scaffold CLI ─────────────────────────────────────────────────────────


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
    """`python -m sphinx_kataglyphis scaffold <dir>` is what the docs tell you to run.

    A subprocess, because __main__.py only executes on that path -- importing the
    package never runs it, so nothing else here would notice it breaking.
    """
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


# ── identity reaches downstream repos ────────────────────────────────────────


def test_author_and_copyright_fall_back_to_the_brand_identity(conf):
    """A consuming repo should inherit these the way it inherits the colours.

    Every downstream conf.py used to retype the author; three of the four still
    do. Defaulting them here is what makes the identity reusable rather than
    merely centralised inside this one repo.
    """
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
