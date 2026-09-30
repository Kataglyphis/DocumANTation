"""Fail the build unless the emitted deck itself is on-brand; pandoc's log cannot show that."""

from __future__ import annotations

import re
import sys
import zipfile
from collections.abc import Callable
from pathlib import Path
from xml.etree import ElementTree

# Import as a package module even when run by path; see fit_titles.py.
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from md2pdfLib.presentation.pptx.pptx_common import (  # noqa: E402
    SLIDE_RE,
    THEME_RE,
    brand_tokens,
    dangling_layout_media,
    run_cli,
)


class BrandCheckError(Exception):
    """Raised when the emitted deck is off-brand, malformed, or has nothing to check."""


_SRGB_RE = re.compile(r'srgbClr val="([0-9A-Fa-f]{6})"')
# The two slots make_reference.py patches (major headings, minor body), matched as it writes them.
_FONT_RE = re.compile(r'<a:(majorFont|minorFont)>\s*<a:latin typeface="([^"]*)"')


def brand_hexes(brand: dict) -> set[str]:
    """Every colour the brand defines, as bare uppercase hex."""
    return {
        value.lstrip("#").upper()
        for section in ("colors", "colors_dark", "syntax", "syntax_dark")
        for value in brand[section].values()
    }


def off_brand_colors(deck: Path, allowed: set[str]) -> dict[str, set[str]]:
    """Return {part: colours that are not brand values}, empty when all good."""
    offenders: dict[str, set[str]] = {}
    with zipfile.ZipFile(deck) as z:
        parts = [n for n in z.namelist() if THEME_RE.fullmatch(n) or SLIDE_RE.fullmatch(n)]
        if not parts:
            raise BrandCheckError(f"{deck} contains no theme or slide parts.")
        for name in parts:
            used = {c.upper() for c in _SRGB_RE.findall(z.read(name).decode("utf-8", "ignore"))}
            if stray := used - allowed:
                offenders[name] = stray
    return offenders


def off_brand_fonts(deck: Path, expected: str) -> dict[str, set[str]]:
    """Return {theme part: font slots naming something other than *expected*}."""
    offenders: dict[str, set[str]] = {}
    with zipfile.ZipFile(deck) as z:
        themes = [n for n in z.namelist() if THEME_RE.fullmatch(n)]
        if not themes:
            raise BrandCheckError(f"{deck} contains no theme part.")
        for name in themes:
            found = _FONT_RE.findall(z.read(name).decode("utf-8", "ignore"))
            if not found:
                offenders[name] = {"(no majorFont/minorFont latin typeface)"}
                continue
            if stray := {f"{role}={face or '(empty)'}" for role, face in found if face != expected}:
                offenders[name] = stray
    return offenders


def malformed_parts(deck: Path) -> dict[str, str]:
    """Return {part: parse error} for each malformed XML part; the regex checks cannot tell."""
    offenders: dict[str, str] = {}
    with zipfile.ZipFile(deck) as z:
        for name in z.namelist():
            if not name.endswith((".xml", ".rels")):
                continue
            try:
                ElementTree.fromstring(z.read(name))
            except ElementTree.ParseError as exc:
                offenders[name] = str(exc)
    return offenders


def _report(header: str, offenders: dict[str, set[str]], remedy: str) -> None:
    """Print one failed check: what is wrong, where, and what to do about it."""
    print(f"Error: {header}", file=sys.stderr)
    for part, details in sorted(offenders.items()):
        print(f"  {part}: {', '.join(sorted(details))}", file=sys.stderr)
    print(remedy, file=sys.stderr)


def check_deck(deck: Path) -> str:
    """Run every brand check before raising BrandCheckError, so one build reports all failures."""
    brand = brand_tokens()
    expected_font = brand["fonts"]["main"]

    checks: list[tuple[Callable[[], dict[str, set[str]]], str, str]] = [
        (
            lambda: {part: {err} for part, err in malformed_parts(deck).items()},
            f"{deck} has XML parts that are not well-formed:",
            "PowerPoint will not open this deck without repairing it.",
        ),
        (
            lambda: {
                part: {"#" + c for c in stray}
                for part, stray in off_brand_colors(deck, brand_hexes(brand)).items()
            },
            f"{deck} uses colours that are not in the brand:",
            "Every colour must come from style/brand.json.",
        ),
        (
            lambda: off_brand_fonts(deck, expected_font),
            f"{deck} theme fonts are not the brand font:",
            f"Both font slots must name {expected_font} (style/brand.json).",
        ),
        (
            lambda: dangling_layout_media(deck),
            f"{deck} has layout image references with no media part:",
            "Run finalize_deck.py after pandoc, or update it for this media.",
        ),
    ]

    failed = 0
    for check, header, remedy in checks:
        if offenders := check():
            _report(header, offenders, remedy)
            failed += 1
    if failed:
        raise BrandCheckError(
            f"{deck.name} failed {failed} of {len(checks)} brand checks (reported above)."
        )

    return f"{deck.name}: well-formed; every colour is a brand value; fonts are {expected_font}."


def main() -> None:
    run_cli(check_deck, errors=(BrandCheckError,))


if __name__ == "__main__":
    main()
