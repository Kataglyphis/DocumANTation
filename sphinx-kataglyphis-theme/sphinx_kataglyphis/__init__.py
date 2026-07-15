"""
Reusable Sphinx theme + scaffold for Kataglyphis documentation sites.

Usage in a new project's ``conf.py``::

    from sphinx_kataglyphis import setup_theme
    setup_theme(globals(), repository_url="https://github.com/org/repo")

The brand tokens (colours, fonts) are packaged with the theme, so any Python
project that installs it can read them without vendoring values::

    from sphinx_kataglyphis import brand
    brand()["colors"]["accent"]        # '#6af0ad'
    brand()["fonts"]["main"]           # 'Roboto'
"""

import argparse
import json
from functools import lru_cache
from importlib.resources import files
from pathlib import Path

# ── brand tokens ─────────────────────────────────────────────────────────────

BRAND_TOKENS_RESOURCE = "brand.tokens.json"
# __name__ rather than __package__: both name this package, but __package__ is
# typed `str | None`, which importlib.resources.files() does not accept.
_PACKAGE = __name__


@lru_cache(maxsize=1)
def brand() -> dict:
    """Return the Kataglyphis brand tokens, with all aliases resolved.

    Generated from ``style/brand.json`` by ``style/generate_style.py``; this is
    the single source of truth for every colour and font. Shipped inside the
    package so ``pip install sphinx-kataglyphis-theme`` is enough to read it.
    """
    payload = files(_PACKAGE).joinpath(BRAND_TOKENS_RESOURCE).read_text(encoding="utf-8")
    return json.loads(payload)


def brand_css_path() -> Path:
    """Filesystem path to the brand stylesheet, for non-Sphinx consumers."""
    return Path(str(files(_PACKAGE).joinpath("_static/css/custom.css")))


# ── helpers ──────────────────────────────────────────────────────────────────


def _discover_markdown_files(source_dir: Path) -> list[str]:
    """Return sorted source files (excluding index) relative to *source_dir*."""
    # Not named `files`: that is importlib.resources.files, imported above.
    found: list[str] = []
    for suffix in (".md", ".rst"):
        for p in sorted(source_dir.glob(f"*{suffix}")):
            if p.stem.lower() == "index":
                continue
            found.append(p.name)
    return found


def _generate_index_content(project_name: str, sources: list[str]) -> str:
    """Generate an index.md with a toctree listing *sources*."""
    lines = [
        f"# {project_name}",
        "",
        "```{toctree}",
        ":maxdepth: 2",
        ":caption: Contents:",
        "",
    ]
    lines.extend(s.rsplit(".", 1)[0] for s in sources)
    lines.append("```")
    lines.append("")
    return "\n".join(lines)


def _needs_index(source_dir: Path) -> bool:
    """True when *source_dir* lacks both index.md and index.rst."""
    return not (source_dir / "index.md").exists() and not (source_dir / "index.rst").exists()


# ── conf.py helper ───────────────────────────────────────────────────────────


def setup_theme(
    conf_globals: dict,
    # ---- project metadata ----
    repository_url: str = "",
    project_name: str = "",
    copyright_: str = "",
    author: str = "",
    release: str = "0.0.1",
    # ---- auto-discovery ----
    auto_discover: bool = False,
    source_dir: str = ".",
    # ---- config overrides ----
    extensions_extra: list | None = None,
    theme_options_extra: dict | None = None,
    html_css_files_extra: list | None = None,
    **extra_conf,
) -> None:
    """Apply Kataglyphis theme defaults to a Sphinx conf.py namespace.

    Call from your project's ``conf.py``::

        from sphinx_kataglyphis import setup_theme
        setup_theme(globals(), repository_url="https://github.com/org/repo")

    When *auto_discover* is ``True`` the package scans *source_dir* for
    ``.md`` / ``.rst`` files and writes an ``index.md`` with a toctree that
    references them – so you can simply drop markdown files and build.
    """
    pkg_dir = Path(__file__).resolve().parent

    # ---- auto-discover markdown files and generate index.md ----
    if auto_discover:
        src = Path(source_dir).resolve()
        if _needs_index(src):
            sources = _discover_markdown_files(src)
            idx = _generate_index_content(project_name or "Documentation", sources)
            (src / "index.md").write_text(idx, encoding="utf-8")
            print(f"[sphinx-kataglyphis] generated index.md with {len(sources)} page(s)")

    # ---- extensions ----
    extensions = ["myst_parser", "sphinx_design"]
    if extensions_extra:
        extensions.extend(extensions_extra)
    conf_globals["extensions"] = extensions

    # ---- MyST ----
    conf_globals["myst_all_links_external"] = True

    # ---- theme ----
    theme_options = {
        "use_repository_button": bool(repository_url),
        "show_navbar_depth": 2,
        "navigation_with_keys": True,
        "show_toc_level": 2,
        "secondary_sidebar_items": ["page-toc"],
        "primary_sidebar_end": [],
        # Same code palette as the book and the slides -- see
        # sphinx_kataglyphis/highlight.py, generated from style/brand.json.
        "pygments_light_style": "kataglyphis-light",
        "pygments_dark_style": "kataglyphis-dark",
    }
    if repository_url:
        theme_options["repository_url"] = repository_url
    if theme_options_extra:
        theme_options |= theme_options_extra

    conf_globals["html_theme"] = "sphinx_book_theme"
    conf_globals["html_theme_options"] = theme_options

    # ---- static paths & CSS ----
    static_paths = ["_static", str(pkg_dir / "_static")]
    conf_globals["html_static_path"] = static_paths

    css_files: list[str] = ["css/custom.css"]
    if html_css_files_extra:
        css_files.extend(html_css_files_extra)
    conf_globals["html_css_files"] = css_files

    # ---- templates ----
    conf_globals.setdefault("templates_path", []).append("_templates")

    # ---- project metadata ----
    if project_name:
        conf_globals.setdefault("project", project_name)
    if copyright_:
        conf_globals.setdefault("copyright", copyright_)
    if author:
        conf_globals.setdefault("author", author)
    if release:
        conf_globals.setdefault("release", release)

    # ---- extra conf variables ----
    for key, value in extra_conf.items():
        conf_globals[key] = value


# ── scaffold CLI ─────────────────────────────────────────────────────────────


def _scaffold(dest: Path) -> None:
    """Create a minimal Sphinx doc directory at *dest*."""
    dest.mkdir(parents=True, exist_ok=True)
    conf_py = dest / "conf.py"
    if conf_py.exists():
        print(f"[sphinx-kataglyphis] {conf_py} already exists — skipping")
    else:
        conf_py.write_text(
            "# Sphinx config — auto-generated by sphinx-kataglyphis\n"
            "# Requires the theme to be installed, e.g. in requirements.txt:\n"
            "#   -e ./external/Kataglyphis-DocumANTation/sphinx-kataglyphis-theme\n"
            "from sphinx_kataglyphis import setup_theme\n"
            "\n"
            "setup_theme(globals(),\n"
            "    auto_discover=True,\n"
            '    repository_url="https://github.com/org/repo",\n'
            '    project_name="My Project",\n'
            '    copyright_="2025, You",\n'
            '    author="You",\n'
            '    release="0.1.0",\n'
            '    html_css_files_extra=["css/custom-overrides.css"],\n'
            ")\n",
            encoding="utf-8",
        )
        print(f"[sphinx-kataglyphis] wrote {conf_py}")

    makefile = dest / "Makefile"
    if not makefile.exists():
        makefile.write_text(
            "# Minimal makefile for Sphinx documentation\n"
            "SPHINXOPTS    ?=\n"
            "SPHINXBUILD   ?= sphinx-build\n"
            "SOURCEDIR     = .\n"
            "BUILDDIR      = _build\n"
            "%:\n"
            '\t@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)\n',
            encoding="utf-8",
        )
        print(f"[sphinx-kataglyphis] wrote {makefile}")

    make_bat = dest / "make.bat"
    if not make_bat.exists():
        make_bat.write_text(
            "@ECHO OFF\n"
            "pushd %~dp0\n"
            'if "%SPHINXBUILD%"=="" set SPHINXBUILD=sphinx-build\n'
            "%SPHINXBUILD% -M %1 %SOURCEDIR% %BUILDDIR% %SPHINXOPTS% %O%\n"
            "popd\n",
            encoding="utf-8",
        )
        print(f"[sphinx-kataglyphis] wrote {make_bat}")

    static_dir = dest / "_static" / "css"
    static_dir.mkdir(parents=True, exist_ok=True)

    overrides = static_dir / "custom-overrides.css"
    if not overrides.exists():
        overrides.write_text(
            "/* Per-project CSS overrides.\n"
            "   Do not redefine brand colours or fonts here — use the tokens:\n"
            "     .my-thing { color: var(--brand-accent-strong); }\n"
            "   The brand itself lives in style/brand.json in\n"
            "   Kataglyphis-DocumANTation; the base theme CSS is generated from\n"
            "   it and ships with this package. */\n",
        )
        print(f"[sphinx-kataglyphis] wrote {overrides}")

    (dest / "_build").mkdir(exist_ok=True)

    print(f"[sphinx-kataglyphis] scaffold complete in {dest}")
    print("  Next steps:")
    print(f"    1. Drop .md files into {dest}/")
    print(f"    2. cd {dest} && sphinx-build -b html . _build/html")
    print("    3. Open _build/html/index.html")


def main() -> None:
    parser = argparse.ArgumentParser(prog="sphinx-kataglyphis")
    sub = parser.add_subparsers(dest="command", required=True)

    sc = sub.add_parser("scaffold", help="Create a new Sphinx doc directory")
    sc.add_argument("dest", nargs="?", default="docs", help="Target directory (default: docs)")

    args = parser.parse_args()
    if args.command == "scaffold":
        _scaffold(Path(args.dest).resolve())


if __name__ == "__main__":
    main()
