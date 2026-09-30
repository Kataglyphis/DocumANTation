"""Kataglyphis Sphinx theme: ``setup_theme(globals(), ...)`` in conf.py, ``brand()`` for tokens."""

import argparse
import copy
import json
from functools import lru_cache
from importlib.resources import files
from pathlib import Path

# Brand tokens

BRAND_TOKENS_RESOURCE = "brand.tokens.json"
# __name__, not __package__: files() does not accept __package__'s `str | None`.
_PACKAGE = __name__


@lru_cache(maxsize=1)
def _load_brand() -> dict:
    payload = files(_PACKAGE).joinpath(BRAND_TOKENS_RESOURCE).read_text(encoding="utf-8")
    return json.loads(payload)


def brand() -> dict:
    """Return a fresh copy of the resolved brand tokens, so no caller edits them for all."""
    return copy.deepcopy(_load_brand())


def brand_css_path() -> Path:
    """Filesystem path to the brand stylesheet, for non-Sphinx consumers."""
    return Path(str(files(_PACKAGE).joinpath("_static/css/custom.css")))


# Helpers


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


# The groups setup_theme applies, one function per group of settings


def _write_index(source_dir: Path, project_name: str) -> None:
    """Generate index.md over *source_dir*, never over a hand-written index."""
    if not _needs_index(source_dir):
        return
    sources = _discover_markdown_files(source_dir)
    content = _generate_index_content(project_name or "Documentation", sources)
    (source_dir / "index.md").write_text(content, encoding="utf-8")
    print(f"[sphinx-kataglyphis] generated index.md with {len(sources)} page(s)")


def _apply_extensions(conf_globals: dict, extensions_extra: list | None) -> None:
    """Assign the extension list and the one MyST setting the brand fixes."""
    extensions = ["myst_parser", "sphinx_design"]
    if extensions_extra:
        extensions.extend(extensions_extra)
    conf_globals["extensions"] = extensions
    conf_globals["myst_all_links_external"] = True


def _apply_theme(conf_globals: dict, repository_url: str, theme_options_extra: dict | None) -> None:
    """Assign the theme and its options -- the part that is not negotiable."""
    theme_options = {
        "use_repository_button": bool(repository_url),
        "show_navbar_depth": 2,
        "navigation_with_keys": True,
        "show_toc_level": 2,
        "secondary_sidebar_items": ["page-toc"],
        "primary_sidebar_end": [],
        # Code blocks are dark in every output, so both modes take the dark token set.
        "pygments_light_style": "kataglyphis-dark",
        "pygments_dark_style": "kataglyphis-dark",
    }
    if repository_url:
        theme_options["repository_url"] = repository_url
    if theme_options_extra:
        theme_options |= theme_options_extra

    conf_globals["html_theme"] = "sphinx_book_theme"
    conf_globals["html_theme_options"] = theme_options


def _apply_static_paths(conf_globals: dict, html_css_files_extra: list | None) -> None:
    """Assign static paths and CSS; the package's _static comes last so its custom.css wins."""
    pkg_dir = Path(__file__).resolve().parent
    conf_dir = Path(conf_globals.get("__file__", "conf.py")).resolve().parent

    static_paths = [str(pkg_dir / "_static")]
    if (conf_dir / "_static").is_dir():
        static_paths.insert(0, "_static")
    conf_globals["html_static_path"] = static_paths

    css_files: list[str] = ["css/custom.css"]
    if html_css_files_extra:
        css_files.extend(html_css_files_extra)
    conf_globals["html_css_files"] = css_files

    conf_globals.setdefault("templates_path", []).append("_templates")


def _apply_metadata(
    conf_globals: dict, project_name: str, copyright_: str, author: str, release: str
) -> None:
    """setdefault the project metadata; author and copyright fall back to the brand identity."""
    identity = brand()["identity"]
    if project_name:
        conf_globals.setdefault("project", project_name)
    conf_globals.setdefault(
        "copyright", copyright_ or f"{identity['copyright_year']}, {identity['name']}"
    )
    conf_globals.setdefault("author", author or identity["name"])
    if release:
        conf_globals.setdefault("release", release)


# conf.py helper


def setup_theme(
    conf_globals: dict,
    # Project metadata
    repository_url: str = "",
    project_name: str = "",
    copyright_: str = "",
    author: str = "",
    # Empty: a version is per project, and a truthy default publishes a wrong one silently.
    release: str = "",
    # Auto-discovery
    auto_discover: bool = False,
    source_dir: str = ".",
    # Config overrides
    extensions_extra: list | None = None,
    theme_options_extra: dict | None = None,
    html_css_files_extra: list | None = None,
    **extra_conf,
) -> None:
    """Apply the Kataglyphis theme to a conf.py namespace: ``setup_theme(globals(), ...)``.

    Theme settings are assigned (extend them via the ``*_extra`` arguments), project
    metadata is only set when absent, and ``**extra_conf`` wins over both.
    """
    if auto_discover:
        _write_index(Path(source_dir).resolve(), project_name)

    _apply_extensions(conf_globals, extensions_extra)
    _apply_theme(conf_globals, repository_url, theme_options_extra)
    _apply_static_paths(conf_globals, html_css_files_extra)
    _apply_metadata(conf_globals, project_name, copyright_, author, release)

    # Last, so a project can override anything above.
    for key, value in extra_conf.items():
        conf_globals[key] = value


# Scaffold CLI


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
            "#   -e ./third_party/DocumANTation/sphinx-kataglyphis-theme\n"
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
            "   DocumANTation; the base theme CSS is generated from\n"
            "   it and ships with this package. */\n",
            encoding="utf-8",
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
