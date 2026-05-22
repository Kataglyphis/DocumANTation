"""Sphinx configuration for Kataglyphis-mdToPdf."""

from __future__ import annotations

from datetime import datetime

project = "Kataglyphis-mdToPdf"
author = "Jonas Heinle"
copyright = f"{datetime.now():%Y}, {author}"

extensions: list[str] = []
templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "alabaster"
html_static_path = ["_static"]
