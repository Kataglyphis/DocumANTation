#!/usr/bin/env python3
"""Generate derived brand-style files from the single source of truth.

``style/brand.json`` holds the canonical brand tokens (colors, fonts). This
script renders the LaTeX and CSS consumers from it so the style is defined
exactly once and stays identical everywhere:

- LaTeX:  md2pdfLib/style/brand-colors.tex  (\\definecolor + aliases)
- LaTeX:  md2pdfLib/style/brand-fonts.tex   (\\brandMainFont + \\brandSetMainFont)
- CSS:    the token block inside the theme's custom.css, maintained between
          generated markers. That file is the only web stylesheet -- the theme
          package ships it, so consuming repos install it instead of copying it.
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
]

STY_PATH = REPO_ROOT / "md2pdfLib" / "style" / "brand-colors.tex"
FONTS_PATH = REPO_ROOT / "md2pdfLib" / "style" / "brand-fonts.tex"
# Code highlighting: the same palette drives Pandoc (PDFs) and Pygments (web).
SYNTAX_THEME_LIGHT = REPO_ROOT / "md2pdfLib/themes/pygments-print.theme"
SYNTAX_THEME_DARK = REPO_ROOT / "md2pdfLib/themes/pygments.theme"
PYGMENTS_MODULE = REPO_ROOT / "sphinx-kataglyphis-theme/sphinx_kataglyphis/highlight.py"
# Standalone token stylesheet for web projects that are not Sphinx (the
# Flutter site): a plain <link> away from the same brand, no build step.
BRAND_CSS = REPO_ROOT / "style" / "brand.css"
# The web style lives in exactly one file: the theme package ships it and
# setup_theme() puts it on html_static_path, so every consuming repo gets the
# same CSS without copying it. Do not add a second target here.
CSS_TARGETS = [
    REPO_ROOT / "sphinx-kataglyphis-theme/sphinx_kataglyphis/_static/css/custom.css",
]

YAML_TARGETS = [
    REPO_ROOT / "md2pdfLib/pandoc/base.yml",
    REPO_ROOT / "md2pdfLib/presentation/pandoc/metadata.yml",
]

CSS_START = "/* generated:brand-tokens:start */"
CSS_END = "/* generated:brand-tokens:end */"
YAML_START = "# generated:brand:start"
YAML_END = "# generated:brand:end"
# Pandoc metadata keys owned by brand.json. Any of these written by hand
# outside the generated block is removed, so a document cannot quietly
# re-specify the brand font or link colour.
MANAGED_YAML_KEYS = (
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
    return (
        "\n".join(
            [
                f"% {NOTE}",
                "% Assumes xcolor is already loaded by the document/class.",
                f"\\definecolor{{brandAccent}}{{HTML}}{{{_hex(c['accent'])}}}",
                f"\\definecolor{{brandAccentStrong}}{{HTML}}{{{_hex(c['accent_strong'])}}}",
                f"\\definecolor{{brandAccentSoft}}{{HTML}}{{{_hex(c['accent_soft'])}}}",
                f"\\definecolor{{brandTextMain}}{{HTML}}{{{_hex(c['text_main'])}}}",
                f"\\definecolor{{brandLink}}{{HTML}}{{{_hex(c['link'])}}}",
                "% Backwards-compatible aliases used across the documents:",
                "\\colorlet{greenAccent}{brandAccent}",
                "\\colorlet{myGreenAccent}{brandAccent}",
                "\\colorlet{basecolor}{brandAccent}",
                "\\colorlet{linkcolor}{brandLink}",
            ]
        )
        + "\n"
    )


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
    }
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def render_yaml_block(brand: dict) -> str:
    """Render the Pandoc metadata keys that brand.json owns.

    ``linkcolor``/``urlcolor``/``citecolor`` name the LaTeX colour defined by
    brand-colors.tex rather than repeating the hex, so the value still lives in
    exactly one place. Pandoc turns ``colorlinks`` on implicitly once any of
    them is set.
    """
    return "\n".join(
        [
            YAML_START,
            f"# {NOTE}",
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
        SYNTAX_THEME_LIGHT: render_syntax_theme(brand["syntax"]),
        SYNTAX_THEME_DARK: render_syntax_theme(brand["syntax_dark"]),
        PYGMENTS_MODULE: render_pygments_module(brand),
        BRAND_CSS: render_brand_css(brand),
    }
    tokens = render_tokens_json(brand)
    for target in TOKENS_TARGETS:
        outputs[target] = tokens
    css_block = render_css_block(brand)
    for css in CSS_TARGETS:
        current = css.read_text(encoding="utf-8") if css.exists() else ""
        outputs[css] = apply_css_block(current, css_block)
    yaml_block = render_yaml_block(brand)
    for yml in YAML_TARGETS:
        outputs[yml] = apply_yaml_block(yml.read_text(encoding="utf-8"), yaml_block)
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
