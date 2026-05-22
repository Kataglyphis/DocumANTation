"""Sphinx configuration for Kataglyphis-mdToPdf."""

from __future__ import annotations

from datetime import datetime
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

project = "Kataglyphis-mdToPdf"
author = "Jonas Heinle"
copyright = f"{datetime.now():%Y}, {author}"

REPO_ROOT = Path(__file__).resolve().parents[1]
SHARED_DOCS_ROOT = REPO_ROOT / "ExternalLib" / "Kataglyphis-ContainerHub" / "docs"
SHARED_THEME_CONF = SHARED_DOCS_ROOT / "source_templates" / "sphinx-book" / "conf_base.py"
DOCS_LOGO = REPO_ROOT / "images" / "logo.png"
DOCS_LOGO_RELATIVE = "../images/logo.png"

if not SHARED_THEME_CONF.exists():
    raise FileNotFoundError(
        "Missing shared docs theme in ExternalLib/Kataglyphis-ContainerHub. "
        "Run `git submodule update --init --recursive`."
    )

if not DOCS_LOGO.exists():
    raise FileNotFoundError(f"Missing docs logo at {DOCS_LOGO}")

shared_conf_spec = spec_from_file_location("shared_sphinx_book_conf_base", SHARED_THEME_CONF)
if shared_conf_spec is None or shared_conf_spec.loader is None:
    raise ImportError(f"Unable to load shared docs config from {SHARED_THEME_CONF}")

shared_conf = module_from_spec(shared_conf_spec)
shared_conf_spec.loader.exec_module(shared_conf)

extensions = list(shared_conf.SPHINX_EXTENSIONS)
templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}
myst_heading_anchors = 3

html_theme = shared_conf.HTML_THEME
html_theme_options = dict(shared_conf.HTML_THEME_OPTIONS)
html_theme_options["repository_url"] = "https://github.com/Kataglyphis/Kataglyphis-mdToPdf"
html_theme_options["logo"] = {
    "text": project,
    "image_light": "logo.png",
    "image_dark": "logo.png",
}
html_static_path = [
    *shared_conf.HTML_STATIC_PATH,
    str(SHARED_DOCS_ROOT / "_static"),
    str(REPO_ROOT / "images"),
]
html_css_files = list(shared_conf.HTML_CSS_FILES)
html_title = project
html_logo = DOCS_LOGO_RELATIVE
html_favicon = DOCS_LOGO_RELATIVE
