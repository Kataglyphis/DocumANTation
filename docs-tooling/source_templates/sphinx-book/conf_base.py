"""Shared Sphinx baseline for Kataglyphis docs websites.

**This is a frozen compatibility shim, not the supported route.** New projects
call ``sphinx_kataglyphis.setup_theme()`` instead -- it wires up the brand CSS,
the shared code palette and the brand fonts in one call, and it is what this
repo's own ``docs/conf.py`` uses.

It exists because **two** repositories load this file **by filesystem path**
(``importlib.util.spec_from_file_location``) rather than importing the package:

- ``AccelerANTgine`` — ``docs/source/conf.py``, which also symlinks
  its ``_static/css/custom.css`` into this directory.
- ``BeschleunigerBallett`` — ``docs/source/conf.py`` (branch
  ``develop``), which repoints at this path and falls back to an inline copy of
  these values when it is missing.

Both read the same five module constants: ``SPHINX_EXTENSIONS``, ``HTML_THEME``,
``HTML_THEME_OPTIONS``, ``HTML_STATIC_PATH`` and ``HTML_CSS_FILES``, and both
override ``repository_url`` on their own copy afterwards. Deleting the file broke
the first of them until it was restored, so those five names are a public
contract -- rename one and both builds fail with nothing failing here.

Two rules follow from how it is consumed:

- **No imports beyond the standard library.** Neither consumer's requirements
  install ``sphinx-kataglyphis-theme`` -- they install ``sphinx-book-theme`` and
  friends -- so anything read from the theme package (the brand tokens, the
  ``kataglyphis-*`` Pygments styles) is unavailable here. That is why the
  highlight style below is one Pygments itself ships, and Pygments is always
  present because Sphinx depends on it.
- **No brand values written by hand.** There are none in this file. The colours
  arrive through the sibling ``custom.css``, which is generated from
  ``style/brand.json`` (see ``style/generate_style.py``) rather than forked.

The rest of this baseline tracks ``setup_theme()``'s options, so the one site
still on this route looks like every other Kataglyphis site.
"""

SPHINX_EXTENSIONS = [
    "myst_parser",
    "sphinx_design",
]

HTML_THEME = "sphinx_book_theme"

# The dark code palette is the single brand code-block look: the LaTeX book, the
# beamer slides, the PPTX deck and the website all use it, and the generated
# custom.css paints `div.highlight` with the dark brand background in *both*
# colour modes. So both Pygments slots have to be dark too -- a light token set
# on that background is the dark-on-dark code this pairing is meant to avoid.
#
# setup_theme() names the theme package's "kataglyphis-dark" style here, which
# this file cannot: see the module docstring. "github-dark" is the closest thing
# Pygments ships -- its background is #0d1117, which *is* the brand's
# syntax_dark background, because the brand palette is derived from it. A test
# pins both facts (tests/test_theme.py).
PYGMENTS_STYLE = "github-dark"

HTML_THEME_OPTIONS = {
    # repository_url is deliberately absent: this baseline is shared, so it
    # cannot know whose repo it is. It used to hardcode ContainerHub's URL,
    # which sent every consumer's repository button to the wrong project. Set it
    # in your own conf.py:
    #     html_theme_options = dict(conf_base.HTML_THEME_OPTIONS)
    #     html_theme_options["repository_url"] = "https://github.com/org/repo"
    "use_repository_button": True,
    "show_navbar_depth": 2,
    "navigation_with_keys": True,
    "show_toc_level": 2,
    # Matches setup_theme(): the page table of contents in the right sidebar.
    # This file used to blank it, so the one site on this route was the only
    # Kataglyphis site without a page TOC.
    "secondary_sidebar_items": ["page-toc"],
    "primary_sidebar_end": [],
    "pygments_light_style": PYGMENTS_STYLE,
    "pygments_dark_style": PYGMENTS_STYLE,
}

HTML_STATIC_PATH = ["_static"]
HTML_CSS_FILES = ["css/custom.css"]
