"""Preset BuildConfig factories for all document types."""

from collections.abc import Callable

from md2pdfLib.pandoc_builder import BuildConfig

# Generated from brand.json at build time, never committed; see make_reference.py.
PPTX_REFERENCE = "data/out/reference.pptx"

# Maps fenced divs to LaTeX environments that each document's preamble must define.
BRAND_DIVS_FILTER = "md2pdfLib/common/filters/brand-divs.lua"


def book() -> BuildConfig:
    return BuildConfig(
        input_dir="./data/book/chapters",
        output_dir="./data/out",
        default_output_name="output.tex",
        metadata_file="md2pdfLib/pandoc/base.yml",
        highlight_style="md2pdfLib/themes/pygments.theme",
        include_in_header="data/book/latex/main.tex",
        log_file="data/out/book.json",
        biblatex=True,
        toc=True,
        number_sections=True,
        number_offset=2,
        top_level_division="chapter",
        output_suffix=".tex",
        extra_args=[
            "--lua-filter",
            BRAND_DIVS_FILTER,
        ],
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
            "--lua-filter",
            BRAND_DIVS_FILTER,
            "-V",
            "themeoptions:english",
            "-V",
            "titlegraphic:data/presentation/images/title-background.jpg",
            "-V",
            "themeoptions:coloraccent=myGreenAccent",
        ],
    )


def pptx() -> BuildConfig:
    """PowerPoint deck from the beamer markdown; --reference-doc is how pptx takes the brand."""
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
            # Depth 1 like beamer's TOC; pptx cannot paginate a TOC that overflows.
            "--toc",
            "--toc-depth=1",
            # Beamer's theme numbers frametitles; pptx needs the numbers in the AST.
            "--lua-filter",
            "md2pdfLib/presentation/pptx/number-titles.lua",
        ],
    )


def demo() -> BuildConfig:
    """The slide showcase in a subdirectory, which get_sorted_markdown_files() never reaches."""
    config = beamer()
    config.input_dir = "data/presentation/demo"
    config.default_output_name = "demo_output.pdf"
    config.log_file = "data/out/demo.json"
    # citeproc wants the bibliography to exist even with no citations.
    config.bibliography = ""
    config.citeproc = False
    return config


def example() -> BuildConfig:
    """The minimal starter document: one pandoc call to PDF, no multi-pass TeX pipeline."""
    return BuildConfig(
        input_dir="data/example/chapters",
        output_dir="data/out",
        default_output_name="example_output.pdf",
        metadata_file="md2pdfLib/example/pandoc/metadata.yml",
        highlight_style="md2pdfLib/themes/pygments.theme",
        include_in_header="data/example/latex/main.tex",
        log_file="data/out/example.json",
        toc=True,
        number_sections=True,
        top_level_division="chapter",
        output_suffix=".pdf",
        extra_args=[
            "--lua-filter",
            BRAND_DIVS_FILTER,
        ],
    )


PRESETS: dict[str, Callable[[], BuildConfig]] = {
    "book": book,
    "beamer": beamer,
    "demo": demo,
    "example": example,
    "pptx": pptx,
}
