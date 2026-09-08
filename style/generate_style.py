#!/usr/bin/env python3
"""Generate derived brand-style files from the single source of truth.

``style/brand.json`` holds the canonical brand tokens (colors, fonts). This
script renders the LaTeX and CSS consumers from it so the style is defined
exactly once and stays identical everywhere:

- LaTeX:  md2pdfLib/style/brand-colors.tex  (\\definecolor + aliases)
- LaTeX:  md2pdfLib/style/brand-fonts.tex   (\\brandMainFont + \\brandSetMainFont)
- LaTeX:  md2pdfLib/style/brand-identity.tex (\\brandName, \\myurl, \\githubBase, ...)
- CSS:    the token block inside the theme's custom.css, maintained between
          generated markers. That file is the only web stylesheet -- the theme
          package ships it, so consuming repos install it instead of copying it.
          The consumers that load it by path instead get a generated verbatim
          copy (``CSS_COPY_TARGETS``), so their copy cannot drift.
- YAML:   the ``mainfont:`` key in each Pandoc metadata file (Pandoc reads YAML,
          not LaTeX, so the value is generated in place between markers).
- JSON:   brand.json with aliases resolved, for any other application that wants
          the brand without implementing alias resolution. Written both to
          style/brand.tokens.json (stable path for non-Python consumers reading
          the submodule) and into the theme package, so `pip install
          sphinx-kataglyphis-theme` + `from sphinx_kataglyphis import brand`
          works with no repo checkout at all.

Usage:
    python style/generate_style.py --check   # fail if derived files drifted
    python style/generate_style.py --write   # regenerate derived files
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BRAND_JSON = REPO_ROOT / "style" / "brand.json"
# Resolved tokens, for consumers that should not have to understand aliases.
# Emitted twice on purpose: once at a stable repo path for non-Python projects
# reading the submodule, and once inside the theme package so that
# `pip install sphinx-kataglyphis-theme` ships it. Both are generated, so
# --check keeps them identical to brand.json.
TOKENS_TARGETS = [
    REPO_ROOT / "style" / "brand.tokens.json",
    REPO_ROOT / "sphinx-kataglyphis-theme/sphinx_kataglyphis/brand.tokens.json",
    # The document builds run in a container that mounts only md2pdfLib/ and
    # data/, so the pptx reference builder cannot reach style/. These copies are
    # generated and --check'd, so they cannot drift from brand.json.
    REPO_ROOT / "md2pdfLib" / "style" / "brand.tokens.json",
]

STY_PATH = REPO_ROOT / "md2pdfLib" / "style" / "brand-colors.tex"
FONTS_PATH = REPO_ROOT / "md2pdfLib" / "style" / "brand-fonts.tex"
# Who the documents are by. On TEXINPUTS, so any document or class can
# \input{brand-identity.tex} without knowing where it lives.
IDENTITY_PATH = REPO_ROOT / "md2pdfLib" / "style" / "brand-identity.tex"
# Code highlighting: the dark palette drives every code block (book, slides,
# pptx, web). A former light/print theme was removed -- all documents now use
# the same dark syntax palette for a single brand code-block look.
SYNTAX_THEME_DARK = REPO_ROOT / "md2pdfLib/themes/pygments.theme"
PYGMENTS_MODULE = REPO_ROOT / "sphinx-kataglyphis-theme/sphinx_kataglyphis/highlight.py"
# Standalone token stylesheet for web projects that are not Sphinx (the
# Flutter site): a plain <link> away from the same brand, no build step.
BRAND_CSS = REPO_ROOT / "style" / "brand.css"
# Dartdoc theme sheet, appended to `dart doc`'s own static-assets/styles.css
# by ContainerHub linux/scripts/lib/dartdoc-build.sh.
DARTDOC_CSS = REPO_ROOT / "style" / "dartdoc.css"
# The web style lives in exactly one file: the theme package ships it and
# setup_theme() puts it on html_static_path, so every consuming repo gets the
# same CSS without copying it. Do not add a second target here.
CSS_TARGETS = [
    REPO_ROOT / "sphinx-kataglyphis-theme/sphinx_kataglyphis/_static/css/custom.css",
]
# Verbatim copies of that stylesheet, for the consumers that cannot install the
# package. Two repos load source_templates/sphinx-book/conf_base.py by path --
# AccelerANTgine and BeschleunigerBallett -- and the first
# symlinks its _static/css/custom.css into that directory, so the file has to
# exist there. Deleting it broke that repo's docs site until it was restored.
#
# Generated rather than maintained, which is the whole point. The hand-written
# fork fell ~490 lines behind and still painted links the pre-cyan green
# (#1ca06a / #7df5ba), so that one site rendered a different brand from every
# other Kataglyphis site while every drift check passed. A copy the generator
# owns cannot do that: --check fails the moment one is edited in place.
CSS_COPY_TARGETS = [
    REPO_ROOT / "docs-tooling/source_templates/sphinx-book/custom.css",
]

# Pandoc metadata files, each with the identity keys that make sense for it.
# `author` belongs on every document; `institute` is the speaker's affiliation on
# the slides, and emitting it into the book would put an affiliation line on a
# book title page that never had one.
YAML_TARGETS: dict[Path, tuple[str, ...]] = {
    REPO_ROOT / "md2pdfLib/pandoc/base.yml": (),
    REPO_ROOT / "md2pdfLib/presentation/pandoc/metadata.yml": ("institute",),
    REPO_ROOT / "md2pdfLib/example/pandoc/metadata.yml": (),
}

CSS_START = "/* generated:brand-tokens:start */"
CSS_END = "/* generated:brand-tokens:end */"
YAML_START = "# generated:brand:start"
YAML_END = "# generated:brand:end"
# Pandoc metadata keys owned by brand.json. Any of these written by hand
# outside the generated block is removed, so a document cannot quietly
# re-specify the brand font or link colour.
MANAGED_YAML_KEYS = (
    "author",
    "institute",
    "mainfont",
    "monofont",
    "monofontoptions",
    "monofontfallback",
    "linkcolor",
    "urlcolor",
    "citecolor",
)
NOTE = "GENERATED from style/brand.json by style/generate_style.py -- do not edit by hand."


def _resolve_group(group: dict[str, str], fallback: dict[str, str] | None = None) -> dict[str, str]:
    """Resolve ``@alias`` values against the group, then *fallback*.

    Keeps a literal from being written twice in brand.json: `"text_on_accent":
    "@white"` means "the same colour as white", not "a copy of #ffffff".
    """
    resolved: dict[str, str] = {}
    for key, value in group.items():
        seen = [key]
        while isinstance(value, str) and value.startswith("@"):
            target = value[1:]
            if target in seen:
                raise SystemExit(f"Alias cycle in brand.json: {' -> '.join(seen)} -> {target}")
            seen.append(target)
            if target in group:
                value = group[target]
            elif fallback and target in fallback:
                value = fallback[target]
            else:
                raise SystemExit(f"brand.json: '{key}' aliases unknown token '@{target}'")
        resolved[key] = value
    return resolved


def resolve_brand(raw: dict) -> dict:
    """Return *raw* with every ``@alias`` replaced by its literal value.

    The ``render_*`` functions require resolved input -- an unresolved dict
    would emit a literal ``@accent`` into the CSS. Idempotent, so resolving
    twice is harmless.
    """
    colors = _resolve_group(raw["colors"])
    return {
        **raw,
        "colors": colors,
        "colors_dark": _resolve_group(raw["colors_dark"], fallback=colors),
        "syntax": _resolve_group(raw["syntax"]),
        "syntax_dark": _resolve_group(raw["syntax_dark"]),
    }


def load_brand() -> dict:
    """Load brand.json with every ``@alias`` resolved to its literal value."""
    return resolve_brand(json.loads(BRAND_JSON.read_text(encoding="utf-8")))


def _hex(value: str) -> str:
    return value.lstrip("#").upper()


def render_latex(brand: dict) -> str:
    c = brand["colors"]
    sd = brand["syntax_dark"]
    return (
        "\n".join(
            [
                f"% {NOTE}",
                "% Assumes xcolor is already loaded by the document/class.",
                f"\\definecolor{{brandAccent}}{{HTML}}{{{_hex(c['accent'])}}}",
                f"\\definecolor{{brandAccentStrong}}{{HTML}}{{{_hex(c['accent_strong'])}}}",
                f"\\definecolor{{brandAccentSoft}}{{HTML}}{{{_hex(c['accent_soft'])}}}",
                f"\\definecolor{{brandAccentDeep}}{{HTML}}{{{_hex(c['accent_deep'])}}}",
                f"\\definecolor{{brandTextMain}}{{HTML}}{{{_hex(c['text_main'])}}}",
                f"\\definecolor{{brandLink}}{{HTML}}{{{_hex(c['link'])}}}",
                "% Dark syntax background -- the brand code-block bg for all documents.",
                f"\\definecolor{{brandSyntaxBg}}{{HTML}}{{{_hex(sd['bg'])}}}",
                "% Backwards-compatible aliases used across the documents:",
                "\\colorlet{greenAccent}{brandAccent}",
                "\\colorlet{myGreenAccent}{brandAccent}",
                "\\colorlet{basecolor}{brandAccent}",
                "\\colorlet{linkcolor}{brandLink}",
                "\\colorlet{shadecolor}{brandSyntaxBg}",
            ]
        )
        + "\n"
    )


def render_latex_identity(brand: dict) -> str:
    r"""Render the identity as LaTeX macros.

    ``\providecommand`` throughout, for two reasons: the file is safe to
    ``\input`` more than once, and a document that genuinely needs a different
    value (a CV profile tailored to one application, say) can still define it
    first and win.

    The ``\my*`` and ``\githubBase`` names are the ones bookclass.cls and the
    beamer header already used when they carried these literals themselves, so
    they keep working -- they are just no longer the place the value lives.
    """
    identity = brand["identity"]
    # (macro name, identity key) -- one \providecommand each, in this order.
    macros = (
        ("brandName", "name"),
        ("brandFirstName", "first_name"),
        ("brandLastName", "last_name"),
        ("brandEmail", "email"),
        ("brandContactEmail", "contact_email"),
        ("brandUrl", "url"),
        ("brandUrlDisplay", "url_display"),
        ("brandGithub", "github"),
        ("brandGithubUrl", "github_url"),
        ("brandGithubHost", "github_host"),
        # Social handles the CV links. They were typed into data/cv/cv.tex, and
        # the LinkedIn one is the author's name in hyphenated form -- an
        # identity value in the one spelling a whole-string scan cannot see.
        ("brandLinkedin", "linkedin"),
        ("brandYoutube", "youtube"),
        ("brandInstitute", "institute"),
    )
    # The names bookclass.cls and the beamer header already used, kept as
    # aliases so neither has to change the macro it renders.
    aliases = (
        ("myname", "brandName"),
        ("myauthor", "brandName"),
        ("myurl", "brandUrlDisplay"),
        ("githubBase", "brandGithubUrl"),
    )
    lines = [
        f"% {NOTE}",
        r"% \providecommand throughout: safe to \input twice, and a document that",
        "% needs a different value can still define it first and win.",
        *[rf"\providecommand{{\{macro}}}{{{identity[key]}}}" for macro, key in macros],
        "% Names the book class and the beamer header already used:",
        *[rf"\providecommand{{\{alias}}}{{\{target}}}" for alias, target in aliases],
    ]
    return "\n".join(lines) + "\n"


def render_latex_fonts(brand: dict) -> str:
    font = brand["fonts"]["main"]
    mono = brand["fonts"]["mono"]
    mono_opts = ",".join(brand["fonts"]["mono_options"])
    return (
        "\n".join(
            [
                f"% {NOTE}",
                "% Assumes fontspec is already loaded by the document/class.",
                "% \\providecommand keeps this file safe to \\input more than once.",
                f"\\providecommand{{\\brandMainFont}}{{{font}}}",
                f"\\providecommand{{\\brandMonoFont}}{{{mono}}}",
                f"\\providecommand{{\\brandSetMainFont}}{{\\setmainfont{{{font}}}}}",
                f"\\providecommand{{\\brandSetMonoFont}}{{\\setmonofont[{mono_opts}]{{{mono}}}}}",
            ]
        )
        + "\n"
    )


def _css_var(name: str, prefix: str = "--brand-") -> str:
    """`accent_strong` -> `--brand-accent-strong`."""
    return prefix + name.replace("_", "-")


def render_css_block(brand: dict) -> str:
    """Render every brand token as a CSS custom property.

    Dark tokens get their own ``--brand-dark-*`` names rather than shadowing the
    light ones inside a ``[data-theme="dark"]`` block: shadowing would silently
    retint every existing ``var(--brand-*)`` use in dark mode.
    """
    fonts = brand["fonts"]
    lines = [
        CSS_START,
        f"/* {NOTE} */",
        f"@import url('https://fonts.googleapis.com/css2?family={fonts['main']}"
        f":wght@{fonts['main_weights']}&display=swap');",
        "",
        ":root {",
        f"  --brand-font-main: '{fonts['main']}', sans-serif;",
        # fonts.mono is deliberately not emitted: it names a TeX font (Latin
        # Modern Mono) that no browser has, so the web keeps the generic
        # monospace stack.
        "",
    ]
    lines += [f"  {_css_var(k)}: {v};" for k, v in brand["colors"].items()]
    lines += ["", "  /* dark-mode palette */"]
    lines += [f"  {_css_var(k, '--brand-dark-')}: {v};" for k, v in brand["colors_dark"].items()]
    lines += ["}", CSS_END]
    return "\n".join(lines)


# Pandoc/KDE highlight token -> (palette key, bold, italic). The emphasis is
# structural and identical in both palettes, so it lives here rather than in
# brand.json, which stays a pure colour/font file.
SYNTAX_TOKENS: dict[str, tuple[str | None, bool, bool]] = {
    "Alert": ("error", True, False),
    "Annotation": ("comment", False, True),
    "Attribute": ("attribute", False, False),
    "BaseN": ("constant", False, False),
    "BuiltIn": ("constant", False, False),
    "Char": ("string", False, False),
    "Comment": ("comment", False, True),
    "CommentVar": ("comment", True, True),
    "Constant": ("constant", False, False),
    "ControlFlow": ("keyword", True, False),
    "DataType": ("type", False, False),
    "DecVal": ("constant", False, False),
    "Documentation": ("comment", False, True),
    "Error": ("error", True, False),
    "Extension": (None, False, False),
    "Float": ("float", False, False),
    "Function": ("function", False, False),
    "Import": ("keyword", False, False),
    "Information": ("comment", True, True),
    "Keyword": ("keyword", True, False),
    "Operator": ("keyword", False, False),
    "Other": ("fg", False, False),
    "Preprocessor": ("preprocessor", False, False),
    "SpecialChar": ("constant", False, False),
    "SpecialString": ("string", False, False),
    "String": ("string", False, False),
    "Variable": ("fg", False, False),
    "VerbatimString": ("string", False, False),
    "Warning": ("warning", True, True),
}

# Pygments token -> palette key. Same palette as SYNTAX_TOKENS above, so a code
# block on the website matches the same code block in the book.
PYGMENTS_TOKENS: list[tuple[str, str, str]] = [
    # (Pygments token, palette key, extra emphasis)
    ("Text", "fg", ""),
    ("Comment", "comment", "italic "),
    ("Comment.Preproc", "preprocessor", ""),
    ("Comment.Special", "comment", "bold italic "),
    ("Keyword", "keyword", "bold "),
    ("Keyword.Constant", "constant", ""),
    ("Keyword.Type", "type", ""),
    ("Operator", "keyword", ""),
    ("Operator.Word", "keyword", "bold "),
    ("Name.Builtin", "constant", ""),
    ("Name.Function", "function", ""),
    ("Name.Class", "type", ""),
    ("Name.Decorator", "preprocessor", ""),
    ("Name.Exception", "error", ""),
    ("Name.Attribute", "attribute", ""),
    ("Name.Tag", "keyword", ""),
    ("Name.Variable", "fg", ""),
    ("Name.Constant", "constant", ""),
    ("String", "string", ""),
    ("String.Escape", "constant", ""),
    ("Number", "constant", ""),
    ("Number.Float", "float", ""),
    ("Generic.Deleted", "error", ""),
    ("Generic.Inserted", "attribute", ""),
    ("Generic.Emph", "fg", "italic "),
    ("Generic.Strong", "fg", "bold "),
    ("Generic.Heading", "function", "bold "),
    ("Error", "error", "bold "),
]


def render_syntax_theme(palette: dict) -> str:
    """Render a Pandoc (KDE) highlight theme from a syntax palette."""
    styles: dict[str, dict] = {}
    for token, (key, bold, italic) in sorted(SYNTAX_TOKENS.items()):
        styles[token] = {
            "text-color": palette[key] if key else None,
            "background-color": palette["error_bg"] if token == "Error" else None,
            "bold": bold,
            "italic": italic,
            "underline": False,
        }
    payload = {
        "text-color": palette["fg"],
        "background-color": palette["bg"],
        "line-number-color": palette["line_number"],
        "line-number-background-color": palette["line_number_bg"],
        "text-styles": styles,
    }
    return json.dumps(payload, indent=4) + "\n"


def _pygments_style_class(class_name: str, style_name: str, palette: dict) -> list[str]:
    lines = [
        f"class {class_name}(Style):",
        f'    """Kataglyphis {style_name} code highlighting."""',
        "",
        f'    name = "{style_name}"',
        f'    background_color = "{palette["bg"]}"',
        f'    highlight_color = "{palette["error_bg"]}"',
        f'    line_number_color = "{palette["line_number"]}"',
        f'    line_number_background_color = "{palette["line_number_bg"]}"',
        "",
        "    styles = {",
    ]
    for token, key, emphasis in PYGMENTS_TOKENS:
        lines.append(f'        {token}: "{emphasis}{palette[key]}",')
    lines += ["    }", ""]
    return lines


def render_pygments_module(brand: dict) -> str:
    """Render the Pygments styles that give the website the book's code colours."""
    tokens = sorted({t.split(".")[0] for t, _, _ in PYGMENTS_TOKENS})
    lines = [
        f'"""{NOTE}',
        "",
        "Pygments styles carrying the Kataglyphis code palette, so code blocks on",
        "the docs website match the book and the slides. Registered as the",
        '"kataglyphis-light" / "kataglyphis-dark" Pygments styles via entry points.',
        '"""',
        "",
        "from pygments.style import Style",
        "from pygments.token import (",
        *[f"    {t}," for t in tokens],
        ")",
        "",
        "",
    ]
    lines += _pygments_style_class("KataglyphisLightStyle", "kataglyphis-light", brand["syntax"])
    lines += [
        "",
    ]
    lines += _pygments_style_class("KataglyphisDarkStyle", "kataglyphis-dark", brand["syntax_dark"])
    return "\n".join(lines)


def render_brand_css(brand: dict) -> str:
    """Standalone token stylesheet, for web projects outside the Sphinx theme."""
    return (
        "\n".join(
            [
                "/* Standalone Kataglyphis brand tokens. Link this and use the",
                "   custom properties -- never copy the values:",
                '     <link rel="stylesheet" href="brand.css">',
                "     .thing { color: var(--brand-accent); }",
                "   Consumed by the Flutter site; the Sphinx theme has the same",
                "   tokens generated into its own custom.css. */",
                render_css_block(brand).replace(CSS_START + "\n", "").replace("\n" + CSS_END, ""),
            ]
        )
        + "\n"
    )


# Dartdoc ships its own palette in static-assets/styles.css and exposes it as
# `--main-*` custom properties on `.light-theme` / `.dark-theme`.
DARTDOC_CSS_START = "/* Kataglyphis brand overrides for Dartdoc START */"
DARTDOC_CSS_END = "/* Kataglyphis brand overrides for Dartdoc END */"

# (css variable, brand section, token). The section is named per row so a dark
# block can still reach a light token -- the mint `accent` is the hover colour
# in both themes, and writing it twice is what brand.json exists to prevent.
DartdocVars = tuple[tuple[str, str, str], ...]

DARTDOC_LIGHT_VARS: DartdocVars = (
    ("--main-bg-color", "colors", "surface_gradient_from"),
    ("--main-header-color", "colors", "white"),
    ("--main-sidebar-color", "colors", "text_main"),
    ("--main-text-color", "colors", "text_main"),
    ("--main-search-bar", "colors", "white"),
    ("--main-footer-background", "colors", "accent_deep"),
    ("--main-hyperlinks-color", "colors", "link"),
    ("--main-inset-bgColor", "colors", "white"),
    ("--main-inset-borderColor", "colors", "surface_border"),
    ("--main-code-bg", "syntax", "bg"),
    ("--main-keyword-color", "syntax", "keyword"),
    ("--main-tag-color", "syntax", "type"),
    ("--main-section-color", "colors", "link_active"),
    ("--main-comment-color", "syntax", "comment"),
    ("--main-var-color", "syntax", "fg"),
    ("--main-string-color", "syntax", "string"),
    ("--main-icon-color", "colors", "text_main"),
    ("--kg-surface", "colors", "white"),
    ("--kg-muted-surface", "colors", "surface_soft"),
    ("--kg-border", "colors", "surface_border"),
    ("--kg-table-stripe", "colors", "surface_gradient_to"),
    ("--kg-code-border", "colors", "surface_border"),
    ("--kg-chip-bg", "colors", "accent_soft"),
    ("--kg-chip-fg", "colors", "accent_deep"),
    ("--kg-hover", "colors", "accent_strong"),
    ("--kg-scrollbar", "colors", "surface_border"),
    ("--kg-scrollbar-hover", "colors", "accent_strong"),
    ("--kg-shadow-tint", "colors", "text_main"),
)

DARTDOC_DARK_VARS: DartdocVars = (
    ("--main-bg-color", "colors_dark", "surface_gradient_from"),
    ("--main-header-color", "colors_dark", "surface_gradient_to"),
    ("--main-sidebar-color", "colors_dark", "sidebar_link"),
    ("--main-text-color", "colors_dark", "text_base"),
    ("--main-search-bar", "colors_dark", "code_bg"),
    ("--main-footer-background", "colors_dark", "surface_gradient_to"),
    ("--main-hyperlinks-color", "colors_dark", "link"),
    ("--main-inset-bgColor", "colors_dark", "code_bg"),
    ("--main-inset-borderColor", "colors_dark", "surface_border"),
    ("--main-code-bg", "syntax_dark", "bg"),
    ("--main-keyword-color", "syntax_dark", "keyword"),
    ("--main-tag-color", "syntax_dark", "type"),
    ("--main-section-color", "colors_dark", "link_hover"),
    ("--main-comment-color", "syntax_dark", "comment"),
    ("--main-var-color", "syntax_dark", "fg"),
    ("--main-string-color", "syntax_dark", "string"),
    ("--main-icon-color", "colors_dark", "text_base"),
    ("--kg-surface", "colors_dark", "surface_gradient_from"),
    ("--kg-muted-surface", "colors_dark", "quote_bg"),
    ("--kg-border", "colors_dark", "surface_border"),
    ("--kg-table-stripe", "colors_dark", "table_stripe_bg"),
    ("--kg-code-border", "colors_dark", "code_border"),
    ("--kg-chip-bg", "colors_dark", "sidebar_link_active_bg"),
    ("--kg-chip-fg", "colors_dark", "sidebar_link_active"),
    ("--kg-hover", "colors", "accent"),
    ("--kg-scrollbar", "colors_dark", "text_muted"),
    ("--kg-scrollbar-hover", "colors_dark", "sidebar_link_hover"),
    ("--kg-shadow-tint", "colors", "black"),
)

# Geometry only. Every colour below is a var() resolved from the two generated
# theme blocks, so no hex can be introduced here without the generator noticing.
DARTDOC_LAYOUT_CSS = """:root {
  --kg-radius-sm: 8px;
  --kg-radius-md: 12px;
  --kg-radius-lg: 16px;
  --kg-transition: 160ms ease;
  --kg-reading-width: 96ch;
  /* Custom properties substitute lazily, so these pick up the theme's tint. */
  --kg-shadow-soft: 0 8px 28px color-mix(in srgb, var(--kg-shadow-tint) 12%, transparent);
  --kg-shadow-strong: 0 16px 42px color-mix(in srgb, var(--kg-shadow-tint) 26%, transparent);
}

.light-theme a,
.light-theme .breadcrumbs li a,
.light-theme .signature a,
.light-theme .feature,
.dark-theme a,
.dark-theme .breadcrumbs li a,
.dark-theme .signature a,
.dark-theme .feature {
  color: var(--main-hyperlinks-color);
}

.light-theme a:hover,
.light-theme .feature:hover,
.light-theme #theme-button:hover,
.light-theme #sidenav-left-toggle:hover,
.dark-theme a:hover,
.dark-theme .feature:hover,
.dark-theme #theme-button:hover,
.dark-theme #sidenav-left-toggle:hover {
  color: var(--kg-hover);
}

html {
  scroll-behavior: smooth;
}

body {
  background: linear-gradient(180deg, var(--main-bg-color) 0%, var(--kg-muted-surface) 100%);
  font-family: var(--kg-font-main);
}

header {
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--kg-border);
  box-shadow: var(--kg-shadow-soft);
}

.main-content {
  padding: 24px 32px 20px 32px;
  overflow-x: auto;
}

.container,
#dartdoc-main-content {
  max-width: min(100%, 1540px);
  margin: 0 auto;
}

.sidebar-offcanvas-left {
  border-right: 1px solid var(--kg-border);
  background-color: var(--kg-surface);
  flex: 0 0 clamp(280px, 22vw, 360px);
  padding: 22px 18px 18px 24px;
  margin-right: 8px;
}

.sidebar-offcanvas-right {
  border-left: 1px solid var(--kg-border);
  flex: 0 0 clamp(210px, 16vw, 280px);
  padding: 22px 18px 18px 16px;
}

.sidebar h5 {
  letter-spacing: 0.03em;
  margin-bottom: 12px;
}

.sidebar ol li.section-title {
  font-size: 16px;
  font-weight: 600;
  text-transform: none;
}

.sidebar ol li a {
  border-radius: var(--kg-radius-sm);
  display: block;
  padding: 4px 10px;
  transition:
    background-color var(--kg-transition),
    color var(--kg-transition),
    transform var(--kg-transition);
}

.sidebar ol li a:hover {
  background: var(--kg-muted-surface);
  transform: translateX(2px);
}

#sidebar-nav {
  border-bottom: 1px solid var(--kg-border);
  margin-bottom: 14px;
  padding-bottom: 12px;
}

#sidebar-nav .self-crumb {
  background: var(--kg-muted-surface);
  border-left: 3px solid var(--main-hyperlinks-color);
  border-radius: var(--kg-radius-sm);
  font-weight: 600;
  line-height: 1.35;
  padding: 6px 10px;
}

.sidebar ol li.section-subitem {
  margin-left: 8px;
}

.sidebar ol li.kg-md-nav-section {
  margin-top: 12px;
}

.sidebar ol li.kg-md-nav-item a {
  font-size: 13px;
}

.kg-guide-content {
  max-width: min(980px, 100%);
}

.kg-guide-content blockquote {
  border-left: 3px solid var(--main-hyperlinks-color);
  margin: 10px 0;
  padding: 6px 12px;
  background: var(--kg-muted-surface);
}

.kg-guide-content pre {
  margin: 10px 0;
}

.kg-guide-toc {
  margin-top: 10px;
}

.kg-guide-toc li a {
  display: block;
}

.markdown.desc {
  max-width: min(var(--kg-reading-width), 100%);
}

.summary,
section.desc,
.main-content > .breadcrumbs {
  margin-bottom: 22px;
}

h1,
h2,
h3,
h4,
h5,
h6 {
  line-height: 1.25;
}

h1 {
  font-weight: 700;
  letter-spacing: -0.02em;
}

h2 {
  font-weight: 650;
  margin-top: 1.6em;
  margin-bottom: 0.55em;
}

h3 {
  font-weight: 600;
  margin-top: 1.35em;
  margin-bottom: 0.45em;
}

p,
li,
dd,
td,
th {
  line-height: 1.6;
}

section,
div.summary,
dl,
table {
  background: var(--kg-surface);
  border: 1px solid var(--kg-border);
  border-radius: var(--kg-radius-md);
}

section,
div.summary,
dl {
  padding: 14px 16px;
  box-shadow: var(--kg-shadow-soft);
}

section#setter,
div#setter {
  border-top: 1px solid var(--kg-border);
  padding-top: 14px;
}

.feature {
  border: 1px solid transparent;
  background: var(--kg-chip-bg);
  color: var(--kg-chip-fg);
  border-radius: 999px;
  font-weight: 600;
  padding: 2px 10px;
}

.tt-wrapper .typeahead {
  border: 1px solid var(--kg-border);
  border-radius: 999px;
  box-shadow: inset 0 1px 0 color-mix(in srgb, var(--main-text-color) 12%, transparent);
  transition:
    border-color var(--kg-transition),
    box-shadow var(--kg-transition);
}

.tt-wrapper .typeahead:focus {
  border-color: var(--main-hyperlinks-color);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--main-hyperlinks-color) 20%, transparent);
}

.tt-wrapper .tt-menu {
  border-radius: var(--kg-radius-md);
  border: 1px solid var(--kg-border);
  background: var(--kg-surface);
  box-shadow: var(--kg-shadow-strong);
}

#dartdoc-sidebar-right {
  background: color-mix(in srgb, var(--kg-surface) 86%, var(--kg-muted-surface));
}

#dartdoc-sidebar-right .section-title {
  font-size: 14px;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

pre,
.hljs {
  border: 1px solid var(--kg-code-border);
  background: var(--main-code-bg);
  border-radius: var(--kg-radius-md);
}

pre {
  padding: 12px;
  overflow-x: auto;
}

code {
  border-radius: 6px;
}

table {
  border-collapse: separate;
  border-spacing: 0;
  overflow: hidden;
}

table,
th,
td {
  border-color: var(--kg-border);
}

th {
  background: var(--kg-muted-surface);
}

tr:nth-child(2n) {
  background-color: var(--kg-table-stripe);
}

footer {
  border-top: 1px solid var(--kg-border);
}

.kg-doc-footer-links {
  margin-top: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
}

.kg-doc-footer-links strong {
  color: var(--main-text-color);
  margin-right: 6px;
}

.kg-doc-footer-links a {
  text-decoration: none;
  border: 1px solid var(--kg-border);
  background: var(--kg-muted-surface);
  border-radius: 999px;
  padding: 3px 10px;
}

.kg-doc-footer-links a:hover {
  background: var(--kg-chip-bg);
  color: var(--kg-chip-fg);
}

::-webkit-scrollbar {
  width: 10px;
  height: 10px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: var(--kg-scrollbar);
  border-radius: 999px;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--kg-scrollbar-hover);
}

@media (max-width: 992px) {
  .main-content {
    padding: 18px;
  }

  .sidebar-offcanvas-left,
  .sidebar-offcanvas-right {
    padding: 16px 12px;
  }

  section,
  div.summary,
  dl {
    padding: 12px;
  }
}

@media (max-width: 840px) {
  .sidebar-offcanvas-left {
    border: 1px solid var(--kg-border);
    border-radius: var(--kg-radius-lg);
    box-shadow: var(--kg-shadow-strong);
    width: min(360px, calc(100% - 20px));
    max-width: min(360px, calc(100% - 20px));
  }

  .tt-wrapper .typeahead {
    border-radius: var(--kg-radius-md);
  }
}
"""


def _dartdoc_theme_block(brand: dict, selector: str, variables: DartdocVars) -> str:
    """Render one ``.light-theme``/``.dark-theme`` block from the brand tokens."""
    lines = [f"{selector} {{"]
    for name, section, token in variables:
        group = brand[section]
        if token not in group:
            raise SystemExit(f"brand.json: '{section}' has no '{token}' for {name}")
        lines.append(f"  {name}: {group[token]};")
    lines.append("}")
    return "\n".join(lines)


def render_dartdoc_css(brand: dict) -> str:
    """Render the Dartdoc theme sheet -- the brand, for `dart doc` output.

    `dart doc` has no theme mechanism; the only hook is appending to the
    generated ``static-assets/styles.css``, which ContainerHub's
    ``linux/scripts/lib/dartdoc-build.sh`` does with this file. Both marker
    lines are load-bearing: that script truncates a previous append at the START
    line, so re-running a docs build cannot stack copies.
    """
    fonts = brand["fonts"]
    root_block = f":root {{\n  --kg-font-main: '{fonts['main']}', sans-serif;\n}}"
    return (
        "\n".join(
            [
                DARTDOC_CSS_START,
                f"/* {NOTE} */",
                f"@import url('https://fonts.googleapis.com/css2?family={fonts['main']}"
                f":wght@{fonts['main_weights']}&display=swap');",
                "",
                root_block,
                "",
                _dartdoc_theme_block(brand, ".light-theme", DARTDOC_LIGHT_VARS),
                "",
                _dartdoc_theme_block(brand, ".dark-theme", DARTDOC_DARK_VARS),
                "",
                DARTDOC_LAYOUT_CSS.rstrip("\n"),
                DARTDOC_CSS_END,
            ]
        )
        + "\n"
    )


def render_tokens_json(brand: dict) -> str:
    """brand.json with aliases resolved -- the read-me-from-anywhere artifact.

    Every brand section, including the syntax palettes: this file is the only
    way a consumer that is neither LaTeX nor Sphinx can read the brand, and it
    used to omit `syntax`/`syntax_dark` while claiming to be brand.json
    resolved -- so such a consumer could not match the book's code colours even
    though they are part of the brand.
    """
    payload = {
        "_comment": NOTE + " Read this file (not brand.json) from other applications.",
        "name": brand["name"],
        "colors": brand["colors"],
        "colors_dark": brand["colors_dark"],
        "syntax": brand["syntax"],
        "syntax_dark": brand["syntax_dark"],
        "fonts": brand["fonts"],
        # So a Sphinx conf.py or any other consumer can read the author and the
        # URLs instead of retyping them: `brand()["identity"]["name"]`.
        "identity": brand["identity"],
    }
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def render_yaml_block(brand: dict, extra_keys: tuple[str, ...] = ()) -> str:
    """Render the Pandoc metadata keys that brand.json owns.

    ``linkcolor``/``urlcolor``/``citecolor`` name the LaTeX colour defined by
    brand-colors.tex rather than repeating the hex, so the value still lives in
    exactly one place. Pandoc turns ``colorlinks`` on implicitly once any of
    them is set.

    Args:
        brand: The resolved brand.
        extra_keys: Identity keys this particular document should also carry,
            beyond ``author`` -- ``institute`` for the slides. Emitting those
            everywhere would put an affiliation on documents that never had one.
    """
    identity = brand["identity"]
    return "\n".join(
        [
            YAML_START,
            f"# {NOTE}",
            f"author: {identity['name']}",
            *[f"{key}: {identity[key]}" for key in extra_keys],
            f"mainfont: {brand['fonts']['main']}",
            f"monofont: {brand['fonts']['mono']}",
            "monofontoptions:",
            *[f"  - {opt}" for opt in brand["fonts"]["mono_options"]],
            "monofontfallback:",
            *[f"  - {fb}" for fb in brand["fonts"]["mono_fallback"]],
            "linkcolor: brandLink",
            "urlcolor: brandLink",
            "citecolor: brandLink",
            YAML_END,
        ]
    )


def _strip_managed_keys_outside_block(text: str) -> str:
    """Drop hand-written copies of the keys the generated block owns."""
    start = text.index(YAML_START)
    end = text.index(YAML_END) + len(YAML_END)
    stray = re.compile(r"^(?:" + "|".join(MANAGED_YAML_KEYS) + r"):.*\n?", re.MULTILINE)
    return stray.sub("", text[:start]) + text[start:end] + stray.sub("", text[end:])


def apply_yaml_block(text: str, block: str) -> str:
    """Return *text* with the generated brand block inserted/updated."""
    marker = re.compile(re.escape(YAML_START) + r".*?" + re.escape(YAML_END), re.DOTALL)
    if marker.search(text):
        text = marker.sub(block, text)
    else:
        # First run: put the block where the hand-written `mainfont:` line was.
        mainfont = re.compile(r"^mainfont:.*$", re.MULTILINE)
        if not mainfont.search(text):
            raise SystemExit(f"No `mainfont:` key or generated marker to update in {text[:40]!r}")
        text = mainfont.sub(block.replace("\\", "\\\\"), text, count=1)
    return _strip_managed_keys_outside_block(text)


def apply_css_block(text: str, block: str) -> str:
    """Return *text* with the brand-token block inserted/updated."""
    marker = re.compile(re.escape(CSS_START) + r".*?" + re.escape(CSS_END), re.DOTALL)
    if marker.search(text):
        return marker.sub(block, text)
    # First run: replace the leading unmarked `:root { ... }` brand block.
    root = re.compile(r":root\s*\{[^}]*\}")
    if root.search(text):
        return root.sub(block, text, count=1)
    return block + "\n\n" + text


def desired_outputs() -> dict[Path, str]:
    brand = load_brand()
    outputs: dict[Path, str] = {
        STY_PATH: render_latex(brand),
        FONTS_PATH: render_latex_fonts(brand),
        IDENTITY_PATH: render_latex_identity(brand),
        SYNTAX_THEME_DARK: render_syntax_theme(brand["syntax_dark"]),
        PYGMENTS_MODULE: render_pygments_module(brand),
        BRAND_CSS: render_brand_css(brand),
        DARTDOC_CSS: render_dartdoc_css(brand),
    }
    tokens = render_tokens_json(brand)
    for target in TOKENS_TARGETS:
        outputs[target] = tokens
    css_block = render_css_block(brand)
    for css in CSS_TARGETS:
        current = css.read_text(encoding="utf-8") if css.exists() else ""
        outputs[css] = apply_css_block(current, css_block)
    theme_css = outputs[CSS_TARGETS[0]]
    for target in CSS_COPY_TARGETS:
        outputs[target] = theme_css
    for yml, extra_keys in YAML_TARGETS.items():
        block = render_yaml_block(brand, extra_keys)
        outputs[yml] = apply_yaml_block(yml.read_text(encoding="utf-8"), block)
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate brand-style files from style/brand.json."
    )
    parser.add_argument("--check", action="store_true", help="Fail if derived files are stale.")
    parser.add_argument("--write", action="store_true", help="Regenerate derived files in place.")
    args = parser.parse_args()

    outputs = desired_outputs()

    if args.check or not args.write:
        stale = [
            p for p, content in outputs.items() if not p.exists() or p.read_text("utf-8") != content
        ]
        if stale:
            print("Brand style files are out of date:", file=sys.stderr)
            for p in stale:
                print(f"- {p.relative_to(REPO_ROOT)}", file=sys.stderr)
            print("Run: python style/generate_style.py --write", file=sys.stderr)
            return 1
        print("Brand style files are up to date.")
        return 0

    changed = []
    for p, content in outputs.items():
        if not p.exists() or p.read_text("utf-8") != content:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
            changed.append(p)
    if changed:
        print("Updated brand style files:")
        for p in changed:
            print(f"- {p.relative_to(REPO_ROOT)}")
    else:
        print("Brand style files already up to date.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
