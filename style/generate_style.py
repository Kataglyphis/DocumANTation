#!/usr/bin/env python3
"""Render every brand consumer from style/brand.json; --check fails on drift, --write fixes it."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BRAND_JSON = REPO_ROOT / "style" / "brand.json"
# Resolved tokens at a stable repo path for non-Python readers and inside the package for pip.
TOKENS_TARGETS = [
    REPO_ROOT / "style" / "brand.tokens.json",
    REPO_ROOT / "sphinx-kataglyphis-theme/sphinx_kataglyphis/brand.tokens.json",
    # The build container mounts only md2pdfLib/ and data/, so the pptx builder needs a copy.
    REPO_ROOT / "md2pdfLib" / "style" / "brand.tokens.json",
]

STY_PATH = REPO_ROOT / "md2pdfLib" / "style" / "brand-colors.tex"
FONTS_PATH = REPO_ROOT / "md2pdfLib" / "style" / "brand-fonts.tex"
# On TEXINPUTS, so any document or class can \input{brand-identity.tex} by name.
IDENTITY_PATH = REPO_ROOT / "md2pdfLib" / "style" / "brand-identity.tex"
# The dark palette drives every code block: book, slides, pptx and web.
SYNTAX_THEME_DARK = REPO_ROOT / "md2pdfLib/themes/pygments.theme"
PYGMENTS_MODULE = REPO_ROOT / "sphinx-kataglyphis-theme/sphinx_kataglyphis/highlight.py"
# Standalone token sheet for non-Sphinx web projects (the Flutter site).
BRAND_CSS = REPO_ROOT / "style" / "brand.css"
# Appended to `dart doc`'s styles.css by ANTfrastructure's linux/scripts/lib/dartdoc-build.sh.
DARTDOC_CSS = REPO_ROOT / "style" / "dartdoc.css"
# The packaged copy, so a project with only the released wheel reaches the same sheet.
DARTDOC_CSS_PACKAGED = REPO_ROOT / "sphinx-kataglyphis-theme/sphinx_kataglyphis/dartdoc.css"
# The one web stylesheet, shipped by the theme package; do not add a second target.
CSS_TARGETS = [
    REPO_ROOT / "sphinx-kataglyphis-theme/sphinx_kataglyphis/_static/css/custom.css",
]

# Identity keys per document: institute belongs on the slides, not on the book's title page.
YAML_TARGETS: dict[Path, tuple[str, ...]] = {
    REPO_ROOT / "md2pdfLib/pandoc/base.yml": (),
    REPO_ROOT / "md2pdfLib/presentation/pandoc/metadata.yml": ("institute",),
    REPO_ROOT / "md2pdfLib/example/pandoc/metadata.yml": (),
}

CSS_START = "/* generated:brand-tokens:start */"
CSS_END = "/* generated:brand-tokens:end */"
YAML_START = "# generated:brand:start"
YAML_END = "# generated:brand:end"
# Keys brand.json owns; hand-written copies outside the generated block are removed.
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
    """Resolve ``@alias`` values against the group, then *fallback*."""
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
    """Return *raw* with every ``@alias`` resolved, as render_* needs; idempotent."""
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
    r"""Render the identity as \providecommand macros, which a document may define first."""
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
        # LinkedIn's handle hyphenates the name, a spelling whole-string scans miss.
        ("brandLinkedin", "linkedin"),
        ("brandYoutube", "youtube"),
        ("brandInstitute", "institute"),
    )
    # Names bookclass.cls and the beamer header already use, kept as aliases.
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
    """Render every token as a CSS property; dark ones get --brand-dark-* rather than shadowing."""
    fonts = brand["fonts"]
    lines = [
        CSS_START,
        f"/* {NOTE} */",
        f"@import url('https://fonts.googleapis.com/css2?family={fonts['main']}"
        f":wght@{fonts['main_weights']}&display=swap');",
        "",
        ":root {",
        f"  --brand-font-main: '{fonts['main']}', sans-serif;",
        # No fonts.mono: it names a TeX font no browser has, so the web keeps generic monospace.
        "",
    ]
    lines += [f"  {_css_var(k)}: {v};" for k, v in brand["colors"].items()]
    lines += ["", "  /* dark-mode palette */"]
    lines += [f"  {_css_var(k, '--brand-dark-')}: {v};" for k, v in brand["colors_dark"].items()]
    lines += ["}", CSS_END]
    return "\n".join(lines)


# Pandoc/KDE token -> (palette key, bold, italic); structural emphasis stays out of brand.json.
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

# Pygments token -> palette key, the palette SYNTAX_TOKENS uses, so web and book code agree.
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


# Dartdoc exposes its palette as --main-* properties on .light-theme / .dark-theme.
DARTDOC_CSS_START = "/* Kataglyphis brand overrides for Dartdoc START */"
DARTDOC_CSS_END = "/* Kataglyphis brand overrides for Dartdoc END */"

# (css variable, brand section, token); a per-row section lets a dark block reach a light token.
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

# Geometry only: every colour in it is a var() from the two generated theme blocks.
DARTDOC_LAYOUT_CSS = (REPO_ROOT / "style" / "dartdoc-layout.css").read_text(encoding="utf-8")


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
    """The Dartdoc theme sheet; dartdoc-build.sh truncates re-runs at its START marker."""
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
    """brand.json with aliases resolved and every section included, readable from anywhere."""
    payload = {
        "_comment": NOTE + " Read this file (not brand.json) from other applications.",
        "name": brand["name"],
        "colors": brand["colors"],
        "colors_dark": brand["colors_dark"],
        "syntax": brand["syntax"],
        "syntax_dark": brand["syntax_dark"],
        "fonts": brand["fonts"],
        # So any consumer reads the author and URLs instead of retyping them.
        "identity": brand["identity"],
    }
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def render_yaml_block(brand: dict, extra_keys: tuple[str, ...] = ()) -> str:
    """Render the Pandoc keys brand.json owns, plus this document's identity *extra_keys*."""
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
        DARTDOC_CSS_PACKAGED: render_dartdoc_css(brand),
    }
    tokens = render_tokens_json(brand)
    for target in TOKENS_TARGETS:
        outputs[target] = tokens
    css_block = render_css_block(brand)
    for css in CSS_TARGETS:
        current = css.read_text(encoding="utf-8") if css.exists() else ""
        outputs[css] = apply_css_block(current, css_block)
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
