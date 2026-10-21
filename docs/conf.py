"""Sphinx configuration for DocumANTation, branded through setup_theme() like downstream repos."""

from __future__ import annotations

from datetime import datetime

from sphinx_kataglyphis import brand, setup_theme

project = "DocumANTation"
# Identity comes from style/brand.json; retyping it here is how copies drift.
IDENTITY = brand()["identity"]
author = IDENTITY["name"]

# Title and heading anchors are the theme's defaults, as downstream gets them; the logo is below.
setup_theme(
    globals(),
    repository_url=f"{IDENTITY['github_url']}/{project}",
    project_name=project,
    author=author,
    copyright_=f"{datetime.now():%Y}, {author}",
    exclude_patterns=["_build", "Thumbs.db", ".DS_Store"],
    source_suffix={".rst": "restructuredtext", ".md": "markdown"},
)

# The repository's own logo, in place of setup_theme()'s shared default.
html_logo = "../images/logos/documantation.svg"
html_favicon = html_logo
