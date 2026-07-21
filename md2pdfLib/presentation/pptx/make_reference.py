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

# The beamer title page draws over this image (presets.py passes it as
# titlegraphic); the pptx title layout uses the same asset so the two decks
# open identically. Resolved relative to the md2pdf root's parent so it works
# on the host checkout and inside the container (where /data is a sibling
# mount of /md2pdfLib).
TITLE_BG_IMAGE = MD2PDF_ROOT.parent / "data/presentation/images/title-background.jpg"
TITLE_BG_REL_ID = "rIdBrandTitleBg"
TITLE_BG_MEDIA = "ppt/media/brandTitleBg.jpg"
# The asset is portrait (1800x4000); a 16:9 slide shows its middle band.
# OOXML srcRect crops in thousandths of a percent: keep 1800*(9/16)=1012.5px
# of 4000 -> crop (4000-1012.5)/2/4000 = 37.34% top and bottom. A test
# recomputes this from the image file, so the constant cannot drift.
TITLE_BG_SRCRECT = 37344

# Layouts that get the accent separator bar under the title -- the pptx
# equivalent of the beamer theme's accent `separator` rule.
SEPARATOR_LAYOUTS = (
    "Title and Content",
    "Two Content",
    "Comparison",
    "Title Only",
    "Content with Caption",
)
SEPARATOR_HEIGHT_EMU = 27432  # 0.03in, ~2.2pt -- a rule, not a banner


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


def _layout_name(xml: str) -> str | None:
    m = re.search(r'<p:cSld name="([^"]+)"', xml)
    return m.group(1) if m else None


def _insert_bg(xml: str, bg: str) -> str:
    """Insert a <p:bg> as the first child of <p:cSld> (schema-required slot)."""
    new, count = re.subn(r"(<p:cSld[^>]*>)", rf"\1{bg}", xml, count=1)
    if count != 1:
        raise ReferenceBuildError("Layout has no <p:cSld> element to carry a background.")
    return new


def _sp_span(xml: str, ph_type: str) -> tuple[int, int]:
    """Return (start, end) of the <p:sp> block holding placeholder *ph_type*."""
    for m in re.finditer(r"<p:sp>.*?</p:sp>", xml, re.S):
        if f'<p:ph type="{ph_type}"' in m.group(0):
            return m.span()
    raise ReferenceBuildError(f'Layout has no "{ph_type}" placeholder to patch.')


def _fill_placeholder(xml: str, ph_type: str, fill: str) -> str:
    """Give a placeholder shape a fill, appended at the end of its <p:spPr>."""
    start, end = _sp_span(xml, ph_type)
    block = xml[start:end]
    # Appending before </p:spPr> keeps the schema's element order only when
    # nothing that must follow a fill is present -- refuse rather than emit an
    # invalid part PowerPoint would repair (or drop) silently.
    if "<a:ln" in block.split("</p:spPr>")[0].rsplit("<p:spPr", 1)[-1]:
        raise ReferenceBuildError(f'"{ph_type}" spPr carries an outline; patcher needs updating.')
    patched, count = re.subn(r"</p:spPr>", f"{fill}</p:spPr>", block, count=1)
    if count != 1:
        raise ReferenceBuildError(f'"{ph_type}" has no closed <p:spPr> to receive a fill.')
    return xml[:start] + patched + xml[end:]


def _color_placeholder_text(xml: str, ph_type: str, scheme: str) -> str:
    """Force a placeholder's level-1 text colour via its list style."""
    start, end = _sp_span(xml, ph_type)
    block = xml[start:end]
    lvl = (
        f'<a:lvl1pPr><a:defRPr><a:solidFill><a:schemeClr val="{scheme}"/>'
        "</a:solidFill></a:defRPr></a:lvl1pPr>"
    )
    if "<a:lstStyle/>" in block:
        patched = block.replace("<a:lstStyle/>", f"<a:lstStyle>{lvl}</a:lstStyle>", 1)
    elif "<a:lstStyle>" in block:
        patched = block.replace("<a:lstStyle>", f"<a:lstStyle>{lvl}", 1)
    else:
        raise ReferenceBuildError(f'"{ph_type}" has no <a:lstStyle> to colour.')
    return xml[:start] + patched + xml[end:]


def _title_geometry(layout_xml: str, master_xml: str) -> tuple[int, int, int, int]:
    """(x, y, cx, cy) of the title placeholder, falling back to the master.

    Content layouts inherit the title box from the slide master, so their own
    title <p:sp> often carries no <a:xfrm>.
    """
    for xml in (layout_xml, master_xml):
        try:
            start, end = _sp_span(xml, "title")
        except ReferenceBuildError:
            continue
        m = re.search(
            r'<a:off x="(-?\d+)" y="(-?\d+)"/><a:ext cx="(\d+)" cy="(\d+)"/>', xml[start:end]
        )
        if m:
            x, y, cx, cy = (int(v) for v in m.groups())
            return x, y, cx, cy
    raise ReferenceBuildError("No title geometry found in layout or master.")


def patch_title_slide_layout(xml: str) -> str:
    """The beamer title page, in OOXML: brand image behind, soft box under the text.

    The title info box mirrors the beamer theme's `title info box`
    (bg=accent!6!white): accent6 is the brand's accent_soft, so the same tint
    comes from the theme's own colour scheme rather than a literal.
    """
    bg = (
        "<p:bg><p:bgPr>"
        f'<a:blipFill rotWithShape="1"><a:blip r:embed="{TITLE_BG_REL_ID}"/>'
        f'<a:srcRect t="{TITLE_BG_SRCRECT}" b="{TITLE_BG_SRCRECT}"/>'
        "<a:stretch><a:fillRect/></a:stretch></a:blipFill>"
        "<a:effectLst/></p:bgPr></p:bg>"
    )
    xml = _insert_bg(xml, bg)
    soft = (
        '<a:solidFill><a:schemeClr val="accent6"><a:alpha val="92000"/></a:schemeClr></a:solidFill>'
    )
    for ph in ("ctrTitle", "subTitle"):
        xml = _fill_placeholder(xml, ph, soft)
    return xml


def patch_section_header_layout(xml: str) -> str:
    """Section pages go accent-on-dark, like the beamer theme's section slides
    (`section number projected` is accent on black)."""
    bg = (
        '<p:bg><p:bgPr><a:solidFill><a:schemeClr val="dk1"/></a:solidFill>'
        "<a:effectLst/></p:bgPr></p:bg>"
    )
    xml = _insert_bg(xml, bg)
    xml = _color_placeholder_text(xml, "title", "accent1")
    xml = _color_placeholder_text(xml, "body", "lt2")
    return xml


def patch_content_layout(xml: str, master_xml: str, shape_id: int) -> str:
    """Draw the accent separator rule under the title, beamer-style."""
    x, y, cx, cy = _title_geometry(xml, master_xml)
    bar = (
        f'<p:sp><p:nvSpPr><p:cNvPr id="{shape_id}" name="Brand Separator"/>'
        '<p:cNvSpPr/><p:nvPr userDrawn="1"/></p:nvSpPr>'
        f'<p:spPr><a:xfrm><a:off x="{x}" y="{y + cy}"/>'
        f'<a:ext cx="{cx}" cy="{SEPARATOR_HEIGHT_EMU}"/></a:xfrm>'
        '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
        '<a:solidFill><a:schemeClr val="accent1"/></a:solidFill>'
        "<a:ln><a:noFill/></a:ln></p:spPr>"
        "<p:txBody><a:bodyPr/><a:lstStyle/><a:p/></p:txBody></p:sp>"
    )
    new, count = re.subn(r"</p:spTree>", f"{bar}</p:spTree>", xml, count=1)
    if count != 1:
        raise ReferenceBuildError("Layout has no <p:spTree> to receive the separator.")
    return new


def _register_media(content_types: str, rels: str) -> tuple[str, str]:
    """Declare the jpg media type and the title layout's image relationship."""
    if 'Extension="jpg"' not in content_types:
        decl = '<Default Extension="jpg" ContentType="image/jpeg"/>'
        content_types, count = re.subn(r"</Types>", f"{decl}</Types>", content_types, count=1)
        if count != 1:
            raise ReferenceBuildError("[Content_Types].xml has no </Types> close tag.")
    rel = (
        f'<Relationship Id="{TITLE_BG_REL_ID}" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" '
        f'Target="../media/{TITLE_BG_MEDIA.rsplit("/", 1)[-1]}"/>'
    )
    rels, count = re.subn(r"</Relationships>", f"{rel}</Relationships>", rels, count=1)
    if count != 1:
        raise ReferenceBuildError("Title layout rels part has no </Relationships> close tag.")
    return content_types, rels


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

    themes_patched = 0
    try:
        with zipfile.ZipFile(source) as src:
            parts: dict[str, bytes] = {i.filename: src.read(i.filename) for i in src.infolist()}
    finally:
        source.unlink(missing_ok=True)

    # -- theme colours + fonts (every theme part: the notes master has its own)
    for name in parts:
        if re.fullmatch(r"ppt/theme/theme\d+\.xml", name):
            parts[name] = patch_theme_xml(parts[name].decode("utf-8"), colors, font).encode("utf-8")
            themes_patched += 1
    if not themes_patched:
        raise ReferenceBuildError("No ppt/theme/*.xml found in pandoc's reference.pptx.")

    # -- layout branding: the beamer look, one layout at a time, found by the
    #    names pandoc selects layouts with -- never by file number.
    masters = [n for n in parts if re.fullmatch(r"ppt/slideMasters/slideMaster\d+\.xml", n)]
    if not masters:
        raise ReferenceBuildError("No slide master found in pandoc's reference.pptx.")
    master_xml = parts[masters[0]].decode("utf-8")

    seen: set[str] = set()
    for name in sorted(parts):
        if not re.fullmatch(r"ppt/slideLayouts/slideLayout\d+\.xml", name):
            continue
        xml = parts[name].decode("utf-8")
        layout = _layout_name(xml)
        if layout == "Title Slide":
            xml = patch_title_slide_layout(xml)
            rels_name = f"ppt/slideLayouts/_rels/{name.rsplit('/', 1)[-1]}.rels"
            if rels_name not in parts:
                raise ReferenceBuildError(f"Title Slide layout has no rels part ({rels_name}).")
            ct, rels = _register_media(
                parts["[Content_Types].xml"].decode("utf-8"), parts[rels_name].decode("utf-8")
            )
            parts["[Content_Types].xml"] = ct.encode("utf-8")
            parts[rels_name] = rels.encode("utf-8")
            if not TITLE_BG_IMAGE.is_file():
                raise ReferenceBuildError(f"Title background image missing: {TITLE_BG_IMAGE}")
            parts[TITLE_BG_MEDIA] = TITLE_BG_IMAGE.read_bytes()
        elif layout == "Section Header":
            xml = patch_section_header_layout(xml)
        elif layout in SEPARATOR_LAYOUTS:
            # Stable per-layout ids far above the deck's own shape ids.
            xml = patch_content_layout(xml, master_xml, 9000 + len(seen))
        else:
            continue
        seen.add(layout or name)
        parts[name] = xml.encode("utf-8")

    missing = {"Title Slide", "Section Header", *SEPARATOR_LAYOUTS} - seen
    if missing:
        raise ReferenceBuildError(
            f"Layouts not found in pandoc's reference.pptx: {sorted(missing)}. "
            "Pandoc's default deck changed; update this patcher."
        )

    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as out:
        for name, payload in parts.items():
            out.writestr(name, payload)
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
