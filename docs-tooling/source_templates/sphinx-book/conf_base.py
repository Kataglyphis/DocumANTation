"""Frozen Sphinx baseline loaded by path; see docs/overview.md § Shared Sphinx Baseline."""

SPHINX_EXTENSIONS = [
    "myst_parser",
    "sphinx_design",
]

HTML_THEME = "sphinx_book_theme"

# custom.css paints code dark in both modes; github-dark is Pygments' own match for the brand.
PYGMENTS_STYLE = "github-dark"

HTML_THEME_OPTIONS = {
    # No repository_url: the baseline is shared, so each consumer's conf.py sets its own.
    "use_repository_button": True,
    "show_navbar_depth": 2,
    "navigation_with_keys": True,
    "show_toc_level": 2,
    # Matches setup_theme(): the page table of contents in the right sidebar.
    "secondary_sidebar_items": ["page-toc"],
    "primary_sidebar_end": [],
    "pygments_light_style": PYGMENTS_STYLE,
    "pygments_dark_style": PYGMENTS_STYLE,
}

HTML_STATIC_PATH = ["_static"]
HTML_CSS_FILES = ["css/custom.css"]
