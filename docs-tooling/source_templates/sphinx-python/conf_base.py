"""Shared Sphinx baseline for Kataglyphis Python projects."""

import sys
from pathlib import Path


def get_python_project_config(
    project_name: str,
    version_file: str = "VERSION.txt",
    repo_root: str | Path | None = None,
) -> dict:
    """Get standard Sphinx configuration for a Python project.

    Args:
        project_name: Name of the project
        version_file: Path to VERSION.txt relative to project root
        repo_root: Root of the consuming repository. Pass the consuming
            project's own root (e.g. ``Path(__file__).resolve().parents[1]``
            from its ``docs/conf.py``). When omitted, defaults to the current
            working directory, since this template now lives in a shared
            submodule and can no longer infer the consumer's layout by walking
            a fixed number of parent directories.

    Returns:
        Dictionary with Sphinx configuration values
    """
    repo_root = Path.cwd() if repo_root is None else Path(repo_root)
    repo_root = repo_root.resolve()
    if (repo_root / version_file).exists():
        version = (repo_root / version_file).read_text().strip()
    else:
        version = "0.0.1"

    sys.path.insert(0, str(repo_root))

    return {
        "project": project_name,
        "copyright": "2025, Jonas Heinle",
        "author": "Jonas Heinle",
        "release": version,
        "version": version.split("+")[0].rsplit(".", 1)[0]
        if "+" in version
        else version.rsplit(".", 1)[0],
    }


SPHINX_EXTENSIONS = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "myst_parser",
    "sphinx_design",
]

MYST_ENABLE_EXTENSIONS = [
    "dollarmath",
    "amsmath",
    "colon_fence",
    "deflist",
]

MYST_HEADING_ANCHORS = 6

AUTODOC_DEFAULT_OPTIONS = {
    "members": True,
    "undoc-members": True,
    "private-members": True,
    "special-members": True,
}

SPHINX_RTD_THEME_OPTIONS = {
    "style_nav_header_background": "#6af0ad",
}

SPHINX_BOOK_THEME_OPTIONS = {
    "repository_url": "https://github.com/Kataglyphis/Kataglyphis-ContainerHub",
    "use_repository_button": True,
    "show_navbar_depth": 2,
    "navigation_with_keys": True,
    "show_toc_level": 2,
    "secondary_sidebar_items": [],
    "primary_sidebar_end": [],
}

SOURCE_SUFFIX = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}
