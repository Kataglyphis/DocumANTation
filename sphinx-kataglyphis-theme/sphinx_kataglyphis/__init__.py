"""
Reusable Sphinx theme + scaffold for Kataglyphis documentation sites.

Usage in a new project's ``conf.py``::

    from sphinx_kataglyphis import setup_theme
    setup_theme(globals(), repository_url="https://github.com/org/repo")
"""

import argparse
from pathlib import Path

# ── helpers ──────────────────────────────────────────────────────────────────


def _discover_markdown_files(source_dir: Path) -> list[str]:
    """Return sorted markdown files (excluding index) relative to *source_dir*."""
    files = []
    for p in sorted(source_dir.glob("*.md")):
        if p.name.lower() == "index.md":
            continue
        files.append(p.name)
    for p in sorted(source_dir.glob("*.rst")):
        if p.name.lower() == "index.rst":
            continue
        files.append(p.name)
    return files


def _generate_index_content(project_name: str, files: list[str]) -> str:
    """Generate an index.md with a toctree listing *files*."""
    lines = [
        f"# {project_name}",
        "",
        "```{toctree}",
        ":maxdepth: 2",
        ":caption: Contents:",
        "",
    ]
    lines.extend(f.replace(".md", "").replace(".rst", "") for f in files)
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
            files = _discover_markdown_files(src)
            idx = _generate_index_content(project_name or "Documentation", files)
            (src / "index.md").write_text(idx, encoding="utf-8")
            print(f"[sphinx-kataglyphis] generated index.md with {len(files)} page(s)")

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
            "import sys\n"
            "from pathlib import Path\n"
            "sys.path.insert(0, str(Path(__file__).resolve().parent.parent /\n"
            '                         "sphinx-kataglyphis-theme"))\n'
            "from sphinx_kataglyphis import setup_theme\n"
            "setup_theme(globals(),\n"
            "    auto_discover=True,\n"
            '    repository_url="https://github.com/org/repo",\n'
            '    project_name="My Project",\n'
            '    copyright_="2025, You",\n'
            '    author="You",\n'
            '    release="0.1.0",\n'
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
            "   The base theme CSS lives in\n"
            "   sphinx-kataglyphis-theme/sphinx_kataglyphis/_static/css/custom.css\n"
            "   Edit that file to change the global look. */\n",
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
