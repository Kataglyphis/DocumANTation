"""Sphinx configuration for DocumANTation, branded through setup_theme() like downstream repos."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from sphinx_kataglyphis import brand, setup_theme

REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_LOGO = REPO_ROOT / "images" / "logo-t3-wireframe.png"
DOCS_LOGO_RELATIVE = "../images/logo-t3-wireframe.png"

if not DOCS_LOGO.exists():
    raise FileNotFoundError(f"Missing docs logo at {DOCS_LOGO}")

project = "DocumANTation"
# Identity comes from style/brand.json; retyping it here is how copies drift.
IDENTITY = brand()["identity"]
author = IDENTITY["name"]

setup_theme(
    globals(),
    repository_url=f"{IDENTITY['github_url']}/{project}",
    project_name=project,
    author=author,
    copyright_=f"{datetime.now():%Y}, {author}",
    # The same file html_logo points at, named as html_static_path exposes it.
    theme_options_extra={
        "logo": {
            "text": project,
            "image_light": DOCS_LOGO.name,
            "image_dark": DOCS_LOGO.name,
        },
    },
    # Project-specific config, applied on top of the shared defaults.
    exclude_patterns=["_build", "Thumbs.db", ".DS_Store"],
    source_suffix={".rst": "restructuredtext", ".md": "markdown"},
    myst_heading_anchors=3,
    html_title=project,
    html_logo=DOCS_LOGO_RELATIVE,
    html_favicon=DOCS_LOGO_RELATIVE,
)

# The logo lives outside docs/, so it needs a static path entry of its own.
html_static_path = [*html_static_path, str(REPO_ROOT / "images")]  # noqa: F821
