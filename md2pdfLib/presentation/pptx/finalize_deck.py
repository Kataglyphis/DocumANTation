"""Re-attach layout media that pandoc drops from an emitted deck.

Pandoc copies slide layouts and their relationship parts verbatim from the
reference deck, but rebuilds ppt/media/ only from what the *slides* embed --
media referenced solely by a layout (the brand title background) is silently
left behind, so the layout's image relationship dangles and the title slide
loses its background depending on the viewer's tolerance for broken refs.

This step runs right after pandoc and writes the missing part back in. It only
knows the media the reference build put there (make_reference.py's constants),
so an unexpected dangling reference still fails loudly in verify_brand.py's
integrity check rather than being papered over here.

Usage:
    python md2pdfLib/presentation/pptx/finalize_deck.py <deck.pptx>
"""

from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path

try:  # imported as a package module (tests)
    from md2pdfLib.presentation.pptx.make_reference import TITLE_BG_IMAGE, TITLE_BG_MEDIA
except ImportError:  # run as a script from its own directory (the build)
    from make_reference import TITLE_BG_IMAGE, TITLE_BG_MEDIA


def missing_layout_media(deck: Path) -> set[str]:
    """Media targets referenced from layout rels but absent from the archive."""
    missing: set[str] = set()
    with zipfile.ZipFile(deck) as z:
        names = set(z.namelist())
        for name in names:
            if not re.fullmatch(r"ppt/slideLayouts/_rels/slideLayout\d+\.xml\.rels", name):
                continue
            for target in re.findall(r'Target="\.\./media/([^"]+)"', z.read(name).decode()):
                if f"ppt/media/{target}" not in names:
                    missing.add(f"ppt/media/{target}")
    return missing


def finalize(deck: Path) -> list[str]:
    """Inject known missing layout media; return what was added."""
    known = {TITLE_BG_MEDIA: TITLE_BG_IMAGE}
    added: list[str] = []
    for part in sorted(missing_layout_media(deck)):
        source = known.get(part)
        if source is None:
            # Not ours to fix -- leave it for the integrity gate to report.
            continue
        with zipfile.ZipFile(deck, "a", zipfile.ZIP_DEFLATED) as z:
            z.writestr(part, source.read_bytes())
        added.append(part)
    return added


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: {Path(sys.argv[0]).name} <deck.pptx>", file=sys.stderr)
        sys.exit(2)
    deck = Path(sys.argv[1])
    if not deck.is_file():
        print(f"Error: no such deck: {deck}", file=sys.stderr)
        sys.exit(1)
    added = finalize(deck)
    if added:
        print(f"{deck.name}: re-attached layout media: {', '.join(added)}")
    else:
        print(f"{deck.name}: no layout media missing.")


if __name__ == "__main__":
    main()
