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

# The image the beamer title page shows in its right-hand wedge (presets.py
# passes it as titlegraphic); the pptx title layout reproduces that wedge with
# the same asset. Resolved relative to the md2pdf root's parent so it works on
# the host checkout and inside the container (where /data is a sibling mount
# of /md2pdfLib).
TITLE_BG_IMAGE = MD2PDF_ROOT.parent / "data/presentation/images/title-background.jpg"
TITLE_BG_REL_ID = "rIdBrandTitleBg"
TITLE_BG_MEDIA = "ppt/media/brandTitleBg.jpg"

# Slide geometry of pandoc's default deck (16:9). The patchers position
# everything in these EMU coordinates; the build fails loudly if the deck's
# slide size ever changes (see build_reference).
SLIDE_CX = 9144000
SLIDE_CY = 5143500

# The title-page wedge: the right ~38% of the slide, with a slanted left edge
# like the awesome-beamer title page. The image is portrait (1800x4000); the
# srcRect crop keeps a band matching the wedge box's aspect, biased toward the
# top of the picture where its subject sits. A test recomputes the total crop
# from the image file, so these cannot drift from the asset.
WEDGE_X = 5669280  # 62% across
WEDGE_CX = SLIDE_CX - WEDGE_X
WEDGE_SLANT = 25000  # left-edge slant, in 1/100000 of the wedge width
WEDGE_EDGE_EMU = 91440  # accent sliver peeking out along the slanted edge
TITLE_BG_SRCRECT_T = 8000
TITLE_BG_SRCRECT_B = 25390

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

# The beamer footline: a light strip across the bottom with an accent block on
# the right (the theme's `footline` / `footlineright` boxes).
FOOTLINE_HEIGHT_EMU = 228600  # 0.238in
FOOTLINE_ACCENT_CX = 914400  # 1in accent block, right-aligned


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


def _style_placeholder_text(
    xml: str,
    ph_type: str,
    *,
    scheme: str | None = None,
    bold: bool = False,
    small_caps: bool = False,
    align_left: bool = False,
) -> str:
    """Replace a placeholder's level-1 list style with the given treatment.

    Replaces the whole <a:lstStyle> rather than merging: unset properties fall
    back to the master, which is the inheritance PowerPoint uses anyway.
    """
    start, end = _sp_span(xml, ph_type)
    block = xml[start:end]
    attrs = (' b="1"' if bold else "") + (' cap="small"' if small_caps else "")
    fill = f'<a:solidFill><a:schemeClr val="{scheme}"/></a:solidFill>' if scheme else ""
    algn = ' algn="l"' if align_left else ""
    lvl = f"<a:lvl1pPr{algn}><a:defRPr{attrs}>{fill}</a:defRPr></a:lvl1pPr>"
    style = f"<a:lstStyle>{lvl}</a:lstStyle>"
    if "<a:lstStyle/>" in block:
        patched = block.replace("<a:lstStyle/>", style, 1)
    elif "<a:lstStyle>" in block:
        patched = re.sub(r"<a:lstStyle>.*?</a:lstStyle>", style, block, count=1, flags=re.S)
    else:
        raise ReferenceBuildError(f'"{ph_type}" has no <a:lstStyle> to style.')
    return xml[:start] + patched + xml[end:]


def _set_placeholder_xfrm(xml: str, ph_type: str, x: int, y: int, cx: int, cy: int) -> str:
    """Move/size a placeholder by replacing (or inserting) its <a:xfrm>."""
    start, end = _sp_span(xml, ph_type)
    block = xml[start:end]
    xfrm = f'<a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
    if "<a:xfrm>" in block:
        patched = re.sub(r"<a:xfrm>.*?</a:xfrm>", xfrm, block, count=1, flags=re.S)
    elif "<p:spPr/>" in block:
        patched = block.replace("<p:spPr/>", f"<p:spPr>{xfrm}</p:spPr>", 1)
    elif "<p:spPr>" in block:
        patched = block.replace("<p:spPr>", f"<p:spPr>{xfrm}", 1)
    else:
        raise ReferenceBuildError(f'"{ph_type}" has no <p:spPr> to position.')
    return xml[:start] + patched + xml[end:]


def _append_shape(xml: str, shape: str) -> str:
    new, count = re.subn(r"</p:spTree>", f"{shape}</p:spTree>", xml, count=1)
    if count != 1:
        raise ReferenceBuildError("Layout has no <p:spTree> to receive a shape.")
    return new


def _rect(shape_id: int, name: str, x: int, y: int, cx: int, cy: int, fill: str) -> str:
    return (
        f'<p:sp><p:nvSpPr><p:cNvPr id="{shape_id}" name="{name}"/>'
        '<p:cNvSpPr/><p:nvPr userDrawn="1"/></p:nvSpPr>'
        f'<p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
        '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
        f"{fill}<a:ln><a:noFill/></a:ln></p:spPr>"
        "<p:txBody><a:bodyPr/><a:lstStyle/><a:p/></p:txBody></p:sp>"
    )


def _wedge(shape_id: int, name: str, x: int, fill: str) -> str:
    """A full-height quad whose left edge slants -- the beamer title wedge."""
    return (
        f'<p:sp><p:nvSpPr><p:cNvPr id="{shape_id}" name="{name}"/>'
        '<p:cNvSpPr/><p:nvPr userDrawn="1"/></p:nvSpPr>'
        f'<p:spPr><a:xfrm><a:off x="{x}" y="0"/>'
        f'<a:ext cx="{WEDGE_CX}" cy="{SLIDE_CY}"/></a:xfrm>'
        "<a:custGeom><a:avLst/><a:gdLst/><a:ahLst/><a:cxnLst/>"
        '<a:rect l="0" t="0" r="100000" b="100000"/>'
        f'<a:pathLst><a:path w="100000" h="100000"><a:moveTo><a:pt x="{WEDGE_SLANT}" y="0"/>'
        '</a:moveTo><a:lnTo><a:pt x="100000" y="0"/></a:lnTo>'
        '<a:lnTo><a:pt x="100000" y="100000"/></a:lnTo>'
        '<a:lnTo><a:pt x="0" y="100000"/></a:lnTo><a:close/></a:path></a:pathLst>'
        f"</a:custGeom>{fill}<a:ln><a:noFill/></a:ln></p:spPr>"
        "<p:txBody><a:bodyPr/><a:lstStyle/><a:p/></p:txBody></p:sp>"
    )


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
    """The beamer title page, in OOXML.

    What the beamer theme actually renders (verified against the built PDF):
    a WHITE page -- not an image-covered one -- with the title bold and
    left-aligned in the top-left, the subtitle in grey below it over an accent
    rule, and the image confined to a right-hand wedge with a slanted edge,
    an accent sliver marking the diagonal.
    """
    bg = (
        '<p:bg><p:bgPr><a:solidFill><a:schemeClr val="lt1"/></a:solidFill>'
        "<a:effectLst/></p:bgPr></p:bg>"
    )
    xml = _insert_bg(xml, bg)

    # The wedge: accent quad first, image quad on top shifted right, so only a
    # sliver of accent shows along the slanted edge -- the beamer diagonal.
    accent_fill = '<a:solidFill><a:schemeClr val="accent1"/></a:solidFill>'
    image_fill = (
        f'<a:blipFill rotWithShape="1"><a:blip r:embed="{TITLE_BG_REL_ID}"/>'
        f'<a:srcRect t="{TITLE_BG_SRCRECT_T}" b="{TITLE_BG_SRCRECT_B}"/>'
        "<a:stretch><a:fillRect/></a:stretch></a:blipFill>"
    )
    xml = _append_shape(
        xml, _wedge(9101, "Brand Wedge Edge", WEDGE_X - WEDGE_EDGE_EMU, accent_fill)
    )
    xml = _append_shape(xml, _wedge(9102, "Brand Wedge", WEDGE_X, image_fill))

    # Title and subtitle move to the left column, clear of the wedge, and take
    # the frametitle treatment: bold small caps, black; subtitle in grey.
    text_cx = WEDGE_X - int(WEDGE_SLANT / 100000 * WEDGE_CX) - 2 * 457200
    xml = _set_placeholder_xfrm(xml, "ctrTitle", 457200, 1097280, text_cx, 1600200)
    xml = _style_placeholder_text(xml, "ctrTitle", bold=True, small_caps=True, align_left=True)
    xml = _set_placeholder_xfrm(xml, "subTitle", 457200, 2856230, text_cx, 1500000)
    xml = _style_placeholder_text(xml, "subTitle", scheme="tx2", align_left=True)

    # The accent rule between title and subtitle, like the beamer title page.
    xml = _append_shape(
        xml,
        _rect(
            9103, "Brand Title Rule", 457200, 2742690, text_cx, SEPARATOR_HEIGHT_EMU, accent_fill
        ),
    )
    return xml


def patch_section_header_layout(xml: str) -> str:
    """Section pages go accent-on-dark, like the beamer theme's section slides
    (`section number projected` is accent on black)."""
    bg = (
        '<p:bg><p:bgPr><a:solidFill><a:schemeClr val="dk1"/></a:solidFill>'
        "<a:effectLst/></p:bgPr></p:bg>"
    )
    xml = _insert_bg(xml, bg)
    xml = _style_placeholder_text(
        xml, "title", scheme="accent1", bold=True, small_caps=True, align_left=True
    )
    xml = _style_placeholder_text(xml, "body", scheme="lt2", align_left=True)
    return xml


def patch_content_layout(xml: str, master_xml: str, shape_id: int) -> str:
    """Content slides take the beamer frame: bold small-caps title, an accent
    separator rule under it, and the footline strip with its accent block."""
    x, y, cx, cy = _title_geometry(xml, master_xml)
    accent_fill = '<a:solidFill><a:schemeClr val="accent1"/></a:solidFill>'
    xml = _style_placeholder_text(xml, "title", bold=True, small_caps=True, align_left=True)
    xml = _append_shape(
        xml, _rect(shape_id, "Brand Separator", x, y + cy, cx, SEPARATOR_HEIGHT_EMU, accent_fill)
    )
    # Footline: light full-width strip (a soft grey derived from text-black by
    # alpha, so it needs no colour slot of its own) + the accent block right.
    grey_fill = (
        '<a:solidFill><a:schemeClr val="dk1"><a:alpha val="8000"/></a:schemeClr></a:solidFill>'
    )
    foot_y = SLIDE_CY - FOOTLINE_HEIGHT_EMU
    xml = _append_shape(
        xml,
        _rect(
            shape_id + 100, "Brand Footline", 0, foot_y, SLIDE_CX, FOOTLINE_HEIGHT_EMU, grey_fill
        ),
    )
    xml = _append_shape(
        xml,
        _rect(
            shape_id + 200,
            "Brand Footline Accent",
            SLIDE_CX - FOOTLINE_ACCENT_CX,
            foot_y,
            FOOTLINE_ACCENT_CX,
            FOOTLINE_HEIGHT_EMU,
            accent_fill,
        ),
    )
    return xml


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

    # -- geometry guard: every patcher positions in SLIDE_CX/CY coordinates,
    #    so a changed slide size must fail here, not misplace shapes quietly.
    pres = parts["ppt/presentation.xml"].decode("utf-8")
    size = re.search(r'<p:sldSz cx="(\d+)" cy="(\d+)"', pres)
    if not size or (int(size.group(1)), int(size.group(2))) != (SLIDE_CX, SLIDE_CY):
        raise ReferenceBuildError(
            f"Slide size changed (expected {SLIDE_CX}x{SLIDE_CY}, "
            f"got {size.groups() if size else 'none'}); update the layout patchers."
        )

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
