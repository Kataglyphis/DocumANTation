#!/usr/bin/env python3
"""Generate derived brand-style files from the single source of truth.

``style/brand.json`` holds the canonical brand tokens (colors, fonts). This
script renders the LaTeX and CSS consumers from it so the style is defined
exactly once and stays identical everywhere:

- LaTeX:  md2pdfLib/style/brand-colors.tex  (\\definecolor + aliases)
- LaTeX:  md2pdfLib/style/brand-fonts.tex   (\\brandMainFont + \\brandSetMainFont)
- CSS:    the ``:root`` brand-token block inside each themed custom.css,
          maintained between generated markers.
- YAML:   the ``mainfont:`` key in each Pandoc metadata file (Pandoc reads YAML,
          not LaTeX, so the value is generated in place between markers).

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

STY_PATH = REPO_ROOT / "md2pdfLib" / "style" / "brand-colors.tex"
FONTS_PATH = REPO_ROOT / "md2pdfLib" / "style" / "brand-fonts.tex"
CSS_TARGETS = [
    REPO_ROOT / "sphinx-kataglyphis-theme/sphinx_kataglyphis/_static/css/custom.css",
    REPO_ROOT / "docs-tooling/source_templates/sphinx-book/custom.css",
]

YAML_TARGETS = [
    REPO_ROOT / "md2pdfLib/pandoc/base.yml",
    REPO_ROOT / "md2pdfLib/presentation/pandoc/metadata.yml",
]

CSS_START = "/* generated:brand-tokens:start */"
CSS_END = "/* generated:brand-tokens:end */"
YAML_START = "# generated:brand-font:start"
YAML_END = "# generated:brand-font:end"
NOTE = "GENERATED from style/brand.json by style/generate_style.py -- do not edit by hand."


def load_brand() -> dict:
    return json.loads(BRAND_JSON.read_text(encoding="utf-8"))


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
                "% Backwards-compatible aliases used across the documents:",
                "\\colorlet{greenAccent}{brandAccent}",
                "\\colorlet{myGreenAccent}{brandAccent}",
                "\\colorlet{basecolor}{brandAccent}",
            ]
        )
        + "\n"
    )


def render_latex_fonts(brand: dict) -> str:
    font = brand["fonts"]["main"]
    return (
        "\n".join(
            [
                f"% {NOTE}",
                "% Assumes fontspec is already loaded by the document/class.",
                "% \\providecommand keeps this file safe to \\input more than once.",
                f"\\providecommand{{\\brandMainFont}}{{{font}}}",
                f"\\providecommand{{\\brandSetMainFont}}{{\\setmainfont{{{font}}}}}",
            ]
        )
        + "\n"
    )


def render_css_block(brand: dict) -> str:
    c = brand["colors"]
    return "\n".join(
        [
            CSS_START,
            f"/* {NOTE} */",
            ":root {",
            f"  --brand-accent: {c['accent']};",
            f"  --brand-accent-strong: {c['accent_strong']};",
            f"  --brand-accent-soft: {c['accent_soft']};",
            f"  --text-main: {c['text_main']};",
            f"  --surface-soft: {c['surface_soft']};",
            f"  --surface-border: {c['surface_border']};",
            f"  --brand-font-main: '{brand['fonts']['main']}', sans-serif;",
            "}",
            CSS_END,
        ]
    )


def render_yaml_block(brand: dict) -> str:
    return "\n".join(
        [
            YAML_START,
            f"# {NOTE}",
            f"mainfont: {brand['fonts']['main']}",
            YAML_END,
        ]
    )


def apply_yaml_block(text: str, block: str) -> str:
    """Return *text* with the generated ``mainfont:`` block inserted/updated."""
    marker = re.compile(re.escape(YAML_START) + r".*?" + re.escape(YAML_END), re.DOTALL)
    if marker.search(text):
        return marker.sub(block, text)
    # First run: replace the existing hand-written `mainfont:` line.
    mainfont = re.compile(r"^mainfont:.*$", re.MULTILINE)
    if mainfont.search(text):
        return mainfont.sub(block, text, count=1)
    raise SystemExit(f"No `mainfont:` key or generated marker found to update in {text[:40]!r}")


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
    }
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
