"""Sphinx configuration for Kataglyphis-DocumANTation.

Uses the same setup_theme() entry point as every downstream repo, so this
repo's own docs get the Kataglyphis brand -- colours, fonts and the shared code
palette -- from the theme package rather than from a second copy of the
baseline.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from sphinx_kataglyphis import setup_theme

REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_LOGO = REPO_ROOT / "images" / "logo-t3-wireframe.png"
DOCS_LOGO_RELATIVE = "../images/logo-t3-wireframe.png"

if not DOCS_LOGO.exists():
    raise FileNotFoundError(f"Missing docs logo at {DOCS_LOGO}")

project = "Kataglyphis-DocumANTation"
author = "Jonas Heinle"

setup_theme(
    globals(),
    repository_url="https://github.com/Kataglyphis/Kataglyphis-DocumANTation",
    project_name=project,
    author=author,
    copyright_=f"{datetime.now():%Y}, {author}",
    theme_options_extra={
        "logo": {"text": project, "image_light": "logo.png", "image_dark": "logo.png"},
    },
    # Project-specific config, applied on top of the shared defaults.
    exclude_patterns=["_build", "Thumbs.db", ".DS_Store"],
    source_suffix={".rst": "restructuredtext", ".md": "markdown"},
    myst_heading_anchors=3,
    html_title=project,
    html_logo=DOCS_LOGO_RELATIVE,
    html_favicon=DOCS_LOGO_RELATIVE,
)

# The logo lives outside docs/, so it needs a static path entry of its own,
# alongside the theme's that setup_theme has already put in place.
html_static_path = [*html_static_path, str(REPO_ROOT / "images")]  # noqa: F821
