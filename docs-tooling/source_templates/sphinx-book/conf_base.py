"""Shared Sphinx baseline for Kataglyphis docs websites."""

SPHINX_EXTENSIONS = [
    "myst_parser",
    "sphinx_design",
]

HTML_THEME = "sphinx_book_theme"

HTML_THEME_OPTIONS = {
    "repository_url": "https://github.com/Kataglyphis/Kataglyphis-ContainerHub",
    "use_repository_button": True,
    "show_navbar_depth": 2,
    "navigation_with_keys": True,
    "show_toc_level": 2,
    "secondary_sidebar_items": [],
    "primary_sidebar_end": [],
}

HTML_STATIC_PATH = ["_static"]
HTML_CSS_FILES = ["css/custom.css"]
