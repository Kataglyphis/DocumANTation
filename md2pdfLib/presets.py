"""Preset BuildConfig factories for all document types."""

from collections.abc import Callable

from md2pdfLib.pandoc_builder import BuildConfig

# Generated from brand.json at build time, not committed -- see
# presentation/pptx/make_reference.py.
PPTX_REFERENCE = "data/out/reference.pptx"


def book() -> BuildConfig:
    # The dark code palette (md2pdfLib/themes/pygments.theme) is used by the
    # slides; the book prints, so it takes the light theme. A former `diss`
    # target was this exact build with the dark theme -- re-add as a preset
    # with a different highlight_style if a screen-first variant is wanted.
    return BuildConfig(
        input_dir="./data/book/chapters",
        output_dir="./data/out",
        default_output_name="output.tex",
        metadata_file="md2pdfLib/pandoc/base.yml",
        highlight_style="md2pdfLib/themes/pygments-print.theme",
        include_in_header="data/book/latex/main.tex",
        log_file="data/out/book.json",
        biblatex=True,
        toc=True,
        number_sections=True,
        number_offset=2,
        top_level_division="chapter",
        output_suffix=".tex",
    )


def beamer() -> BuildConfig:
    return BuildConfig(
        input_dir="data/presentation",
        output_dir="data/out",
        default_output_name="beamer_output.pdf",
        metadata_file="md2pdfLib/presentation/pandoc/metadata.yml",
        highlight_style="md2pdfLib/themes/pygments.theme",
        include_in_header="data/presentation/latex/main.tex",
        log_file="data/out/beamer.json",
        bibliography="data/presentation/latex/refs.bib",
        citeproc=True,
        output_suffix=".pdf",
        extra_args=[
            "--columns=10",
            "--slide-level=2",
            "-t",
            "beamer",
            "--template",
            "md2pdfLib/presentation/pandoc/awesome-beamer-template.tex",
            # No `-V linkcolor:...` here. metadata.yml carries linkcolor,
            # urlcolor and citecolor as brandLink, generated from brand.json,
            # and a -V wins over the metadata file -- so setting it here made
            # internal links stock blue while URLs and citations stayed brand
            # green. The slides were the one document where a hardcoded colour
            # survived the whole brand pipeline.
            "-V",
            "themeoptions:english",
            "-V",
            "titlegraphic:data/presentation/images/title-background.jpg",
            "-V",
            "themeoptions:coloraccent=myGreenAccent",
        ],
    )


def pptx() -> BuildConfig:
    """PowerPoint deck from the same markdown the beamer slides are built from.

    One source, two outputs -- the deck cannot drift from the slides because
    there is nothing to keep in sync. The brand comes from the reference deck
    that ``presentation/pptx/make_reference.py`` generates from brand.json at
    build time; ``--reference-doc`` is the only way pptx accepts colours and
    fonts, and pandoc's default one is stock Office blue.
    """
    return BuildConfig(
        input_dir="data/presentation",
        output_dir="data/out",
        default_output_name="presentation.pptx",
        metadata_file="md2pdfLib/presentation/pandoc/metadata.yml",
        highlight_style="md2pdfLib/themes/pygments.theme",
        log_file="data/out/pptx.json",
        bibliography="data/presentation/latex/refs.bib",
        citeproc=True,
        output_suffix=".pptx",
        extra_args=[
            "--slide-level=2",
            "-t",
            "pptx",
            "--reference-doc",
            PPTX_REFERENCE,
            # The beamer deck opens with a TOC slide; so does this one. Depth 1
            # matches the beamer TOC (sections only) and keeps the list on one
            # slide -- pptx cannot split an overflowing TOC the way beamer
            # paginates its into (I)/(II).
            "--toc",
            "--toc-depth=1",
            # Beamer numbers its frametitles via the theme; pptx gets the same
            # numbers via the AST, which the TOC slide then inherits too.
            "--lua-filter",
            "md2pdfLib/presentation/pptx/number-titles.lua",
        ],
    )


PRESETS: dict[str, Callable[[], BuildConfig]] = {
    "book": book,
    "beamer": beamer,
    "pptx": pptx,
}
