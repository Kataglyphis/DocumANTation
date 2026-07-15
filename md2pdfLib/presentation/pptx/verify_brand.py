"""Fail the build if a generated pptx is not on-brand.

The strict gate reads pandoc's log, so it catches what pandoc *complains*
about. It cannot catch a deck that builds perfectly and looks wrong -- if
pandoc stopped honouring --reference-doc, or --syntax-highlighting was
dropped, every existing check would still pass while the deck came out stock
Office blue. That is exactly how this repo's docs site lost the shared code
palette without a single failure, and how 81 missing glyphs shipped.

So check the artifact itself: every colour in the theme and on the slides must
be a value from brand.tokens.json.

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


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: {Path(sys.argv[0]).name} <deck.pptx>", file=sys.stderr)
        sys.exit(2)
    deck = Path(sys.argv[1])
    if not deck.is_file():
        print(f"Error: no such deck: {deck}", file=sys.stderr)
        sys.exit(1)

    brand = json.loads(BRAND_TOKENS.read_text("utf-8"))
    offenders = off_brand_colors(deck, brand_hexes(brand))
    if offenders:
        print(f"Error: {deck} uses colours that are not in the brand:", file=sys.stderr)
        for part, stray in sorted(offenders.items()):
            print(f"  {part}: {', '.join('#' + c for c in sorted(stray))}", file=sys.stderr)
        print("Every colour must come from style/brand.json.", file=sys.stderr)
        sys.exit(1)
    print(f"{deck.name}: every colour is a brand value.")


if __name__ == "__main__":
    main()
