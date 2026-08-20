"""Fail the build if a generated pptx is not on-brand.

The strict gate reads pandoc's log, so it catches what pandoc *complains*
about. It cannot catch a deck that builds perfectly and looks wrong -- if
pandoc stopped honouring --reference-doc, or --syntax-highlighting was
dropped, every existing check would still pass while the deck came out stock
Office blue. That is exactly how this repo's docs site lost the shared code
palette without a single failure, and how 81 missing glyphs shipped.

So check the artifact itself: every colour in the theme and on the slides must
be a value from brand.tokens.json, and the theme's font slots must name the
brand font. make_reference.py patches both, and its patching is unit-tested,
but that only proves the reference deck was built right -- this is the check
that the deck pandoc actually emitted kept them.

Usage:
    python md2pdfLib/presentation/pptx/verify_brand.py <deck.pptx>
"""

from __future__ import annotations

import re
import sys
import zipfile
from collections.abc import Callable
from pathlib import Path
from xml.etree import ElementTree

# Import as a package module even when run as a script by path -- see the note
# in fit_titles.py.
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from md2pdfLib.presentation.pptx.pptx_common import (  # noqa: E402
    SLIDE_RE,
    THEME_RE,
    brand_tokens,
    dangling_layout_media,
)

_SRGB_RE = re.compile(r'srgbClr val="([0-9A-Fa-f]{6})"')
# The two theme font slots make_reference.py patches: major is headings, minor
# is body. Matched the same way it writes them.
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
            raise SystemExit(f"Error: {deck} contains no theme or slide parts.")
        for name in parts:
            used = {c.upper() for c in _SRGB_RE.findall(z.read(name).decode("utf-8", "ignore"))}
            if stray := used - allowed:
                offenders[name] = stray
    return offenders


def off_brand_fonts(deck: Path, expected: str) -> dict[str, set[str]]:
    """Return {theme part: font slots naming something other than *expected*}.

    A deck whose theme reverted to Calibri renders in Calibri no matter how
    correct its colours are, and the colour scan above would pass it.
    """
    offenders: dict[str, set[str]] = {}
    with zipfile.ZipFile(deck) as z:
        themes = [n for n in z.namelist() if THEME_RE.fullmatch(n)]
        if not themes:
            raise SystemExit(f"Error: {deck} contains no theme part.")
        for name in themes:
            found = _FONT_RE.findall(z.read(name).decode("utf-8", "ignore"))
            if not found:
                offenders[name] = {"(no majorFont/minorFont latin typeface)"}
                continue
            if stray := {f"{role}={face or '(empty)'}" for role, face in found if face != expected}:
                offenders[name] = stray
    return offenders


def malformed_parts(deck: Path) -> dict[str, str]:
    """Return {part: parse error} for every XML part that is not well-formed.

    PowerPoint refuses to open a deck with a malformed part until it has
    "repaired" it, which silently drops content. Every other check in this
    module scans with regexes, and a regex matches broken markup just as
    happily as valid markup -- so none of them notice. finalize_deck.py
    rewrites slide XML by hand (promoting mc:Choice content out of its
    wrapper), and that is exactly the kind of edit that can orphan a namespace
    prefix, so the emitted deck gets parsed here before it is called good.
    """
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


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: {Path(sys.argv[0]).name} <deck.pptx>", file=sys.stderr)
        sys.exit(2)
    deck = Path(sys.argv[1])
    if not deck.is_file():
        print(f"Error: no such deck: {deck}", file=sys.stderr)
        sys.exit(1)

    brand = brand_tokens()
    expected_font = brand["fonts"]["main"]

    # Every check runs before exiting, so one build reports every way the deck
    # is off-brand rather than only the first. Each reports {part: details}, so
    # one printer serves all of them.
    #
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

    failed = False
    for check, header, remedy in checks:
        if offenders := check():
            _report(header, offenders, remedy)
            failed = True

    if failed:
        sys.exit(1)
    print(f"{deck.name}: well-formed; every colour is a brand value; fonts are {expected_font}.")


if __name__ == "__main__":
    main()
