"""Build a brand-themed pandoc reference.pptx from style/brand.json.

PowerPoint decks get their colours and fonts from a *reference document*, which
is a binary .pptx. Committing one would put brand values in a file nothing can
diff, nothing can drift-check, and no one can review -- the exact failure this
repo's generated-from-brand.json pipeline exists to prevent, and the same shape
as the stylesheet forks that silently rotted here before.

So build it instead: take pandoc's own default reference.pptx, patch the Office
theme's colour scheme and fonts with the brand, and write the result to the
build directory. It is a build artifact, never committed, regenerated on every
build, and every value in it comes from brand.tokens.json.

Usage:
    python md2pdfLib/presentation/pptx/make_reference.py <output.pptx>
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

MD2PDF_ROOT = Path(__file__).resolve().parents[2]
BRAND_TOKENS = MD2PDF_ROOT / "style" / "brand.tokens.json"


class ReferenceBuildError(Exception):
    """Raised when the branded reference deck cannot be produced."""


def brand_theme_colors(brand: dict) -> dict[str, str]:
    """Map brand tokens onto the twelve Office theme colour slots.

    Office fixes the slot names, so this mapping is the one place the brand
    meets PowerPoint's vocabulary. accent1 is what shapes and headings pick up
    by default, so it gets the brand accent.
    """
    colors = brand["colors"]
    return {
        "dk1": colors["text_main"],
        "lt1": colors["white"],
        "dk2": colors["accent_deep"],
        "lt2": colors["surface_soft"],
        "accent1": colors["accent"],
        "accent2": colors["accent_strong"],
        "accent3": colors["accent_deep"],
        "accent4": colors["link"],
        "accent5": colors["link_hover"],
        "accent6": colors["accent_soft"],
        "hlink": colors["link"],
        "folHlink": colors["link_active"],
    }


def _hex(value: str) -> str:
    """'#6af0ad' -> '6AF0AD'. OOXML wants bare uppercase hex."""
    return value.lstrip("#").upper()


def patch_theme_xml(xml: str, colors: dict[str, str], font: str) -> str:
    """Return *xml* with the brand's colours and font substituted in.

    Raises if a slot is missing rather than quietly leaving an Office default
    in place: a deck that is silently half-brand is worse than a failed build.
    """
    for slot, value in colors.items():
        # dk1/lt1 ship as <a:sysClr val="windowText" .../>, the rest as
        # <a:srgbClr val="1F497D"/>. Replace whichever is inside the slot with a
        # literal brand colour, so all twelve slots are brand-defined.
        pattern = re.compile(rf"(<a:{slot}>)\s*<a:(?:sysClr|srgbClr)\b[^/]*?/>\s*(</a:{slot}>)")
        xml, count = pattern.subn(rf'\1<a:srgbClr val="{_hex(value)}"/>\2', xml)
        if count != 1:
            raise ReferenceBuildError(
                f"Expected exactly one <a:{slot}> colour slot in the theme, found {count}. "
                "Pandoc's default reference.pptx layout changed; update this patcher."
            )

    for role in ("majorFont", "minorFont"):
        pattern = re.compile(rf'(<a:{role}>\s*<a:latin typeface=")[^"]*(")')
        xml, count = pattern.subn(rf"\1{font}\2", xml)
        if count != 1:
            raise ReferenceBuildError(
                f"Expected exactly one <a:{role}> latin typeface, found {count}."
            )

    return xml


def default_reference_pptx(dest: Path) -> None:
    """Ask pandoc for its own default reference deck."""
    try:
        data = subprocess.run(
            ["pandoc", "--print-default-data-file", "reference.pptx"],
            check=True,
            capture_output=True,
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        raise ReferenceBuildError(f"Could not read pandoc's default reference.pptx: {exc}") from exc
    dest.write_bytes(data)


def build_reference(output: Path, brand: dict | None = None) -> Path:
    """Write a brand-themed reference deck to *output* and return it."""
    brand = brand if brand is not None else json.loads(BRAND_TOKENS.read_text("utf-8"))
    colors = brand_theme_colors(brand)
    font = brand["fonts"]["main"]

    output.parent.mkdir(parents=True, exist_ok=True)
    source = output.with_suffix(".default.pptx")
    default_reference_pptx(source)

    patched = 0
    try:
        with (
            zipfile.ZipFile(source) as src,
            zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as out,
        ):
            for item in src.infolist():
                payload = src.read(item.filename)
                # Every theme part, not just theme1: the notes master carries its
                # own, and a deck whose notes are off-brand is still off-brand.
                if re.fullmatch(r"ppt/theme/theme\d+\.xml", item.filename):
                    payload = patch_theme_xml(payload.decode("utf-8"), colors, font).encode("utf-8")
                    patched += 1
                out.writestr(item, payload)
    finally:
        source.unlink(missing_ok=True)

    if not patched:
        raise ReferenceBuildError("No ppt/theme/*.xml found in pandoc's reference.pptx.")
    return output


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: {Path(sys.argv[0]).name} <output.pptx>", file=sys.stderr)
        sys.exit(2)
    if shutil.which("pandoc") is None:
        print("Error: pandoc is not on PATH.", file=sys.stderr)
        sys.exit(1)
    try:
        out = build_reference(Path(sys.argv[1]).resolve())
    except ReferenceBuildError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    print(f"Wrote brand-themed reference deck: {out}")


if __name__ == "__main__":
    main()
