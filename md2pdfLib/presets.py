"""Preset BuildConfig factories for all document types."""

from collections.abc import Callable

from md2pdfLib.pandoc_builder import BuildConfig

# Generated from brand.json at build time, not committed -- see
# presentation/pptx/make_reference.py.
PPTX_REFERENCE = "data/out/reference.pptx"


def _book_like(highlight_style: str, log_file: str) -> BuildConfig:
    return BuildConfig(
        input_dir="./data/book/chapters",
        output_dir="./data/out",
        default_output_name="output.tex",
        metadata_file="md2pdfLib/pandoc/base.yml",
        highlight_style=highlight_style,
        include_in_header="data/book/latex/main.tex",
        log_file=log_file,
        biblatex=True,
        toc=True,
        number_sections=True,
        number_offset=2,
        top_level_division="chapter",
        output_suffix=".tex",
    )


def book() -> BuildConfig:
    return _book_like("md2pdfLib/themes/pygments-print.theme", "data/out/book.json")


def diss() -> BuildConfig:
    return _book_like("md2pdfLib/themes/pygments.theme", "data/out/diss.json")


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
            "-V",
            "linkcolor:blue",
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
        ],
    )


PRESETS: dict[str, Callable[[], BuildConfig]] = {
    "book": book,
    "diss": diss,
    "beamer": beamer,
    "pptx": pptx,
}
