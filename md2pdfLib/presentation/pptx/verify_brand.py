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

import json
import re
import sys
import zipfile
from pathlib import Path

MD2PDF_ROOT = Path(__file__).resolve().parents[2]
BRAND_TOKENS = MD2PDF_ROOT / "style" / "brand.tokens.json"

_SRGB_RE = re.compile(r'srgbClr val="([0-9A-Fa-f]{6})"')
_THEME_RE = re.compile(r"ppt/theme/theme\d+\.xml")
_SLIDE_RE = re.compile(r"ppt/slides/slide\d+\.xml")
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
        parts = [n for n in z.namelist() if _THEME_RE.fullmatch(n) or _SLIDE_RE.fullmatch(n)]
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
        themes = [n for n in z.namelist() if _THEME_RE.fullmatch(n)]
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


def dangling_layout_media(deck: Path) -> dict[str, set[str]]:
    """{layout rels part: media targets that do not exist in the archive}.

    Pandoc drops media that only layouts reference (finalize_deck.py puts the
    known ones back); anything still dangling means a layout's image -- the
    title background -- will not render. That is an off-brand deck even though
    every colour checks out.
    """
    offenders: dict[str, set[str]] = {}
    with zipfile.ZipFile(deck) as z:
        names = set(z.namelist())
        for name in names:
            if not re.fullmatch(r"ppt/slideLayouts/_rels/slideLayout\d+\.xml\.rels", name):
                continue
            missing = {
                t
                for t in re.findall(r'Target="\.\./media/([^"]+)"', z.read(name).decode())
                if f"ppt/media/{t}" not in names
            }
            if missing:
                offenders[name] = missing
    return offenders


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: {Path(sys.argv[0]).name} <deck.pptx>", file=sys.stderr)
        sys.exit(2)
    deck = Path(sys.argv[1])
    if not deck.is_file():
        print(f"Error: no such deck: {deck}", file=sys.stderr)
        sys.exit(1)

    brand = json.loads(BRAND_TOKENS.read_text("utf-8"))
    failed = False

    if offenders := off_brand_colors(deck, brand_hexes(brand)):
        print(f"Error: {deck} uses colours that are not in the brand:", file=sys.stderr)
        for part, stray in sorted(offenders.items()):
            print(f"  {part}: {', '.join('#' + c for c in sorted(stray))}", file=sys.stderr)
        print("Every colour must come from style/brand.json.", file=sys.stderr)
        failed = True

    expected_font = brand["fonts"]["main"]
    if bad_fonts := off_brand_fonts(deck, expected_font):
        print(f"Error: {deck} theme fonts are not the brand font:", file=sys.stderr)
        for part, stray in sorted(bad_fonts.items()):
            print(f"  {part}: {', '.join(sorted(stray))}", file=sys.stderr)
        print(f"Both font slots must name {expected_font} (style/brand.json).", file=sys.stderr)
        failed = True

    if dangling := dangling_layout_media(deck):
        print(f"Error: {deck} has layout image references with no media part:", file=sys.stderr)
        for part, targets in sorted(dangling.items()):
            print(f"  {part}: {', '.join(sorted(targets))}", file=sys.stderr)
        print("Run finalize_deck.py after pandoc, or update it for this media.", file=sys.stderr)
        failed = True

    # Both checks run before exiting, so one build reports every way the deck
    # is off-brand rather than only the first.
    if failed:
        sys.exit(1)
    print(f"{deck.name}: every colour is a brand value; fonts are {expected_font}.")


if __name__ == "__main__":
    main()
