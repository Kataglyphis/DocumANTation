"""Preset BuildConfig factories for all document types."""

from collections.abc import Callable

from md2pdfLib.pandoc_builder import BuildConfig

# Generated from brand.json at build time, not committed -- see
# presentation/pptx/make_reference.py.
PPTX_REFERENCE = "data/out/reference.pptx"

# Lua filter mapping fenced divs (::: {.note}, ::: {.theorem}, etc.) to
# LaTeX environments. Shared by book and beamer; the filter emits raw LaTeX
# that targets environments defined by each document's preamble.
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


def demo() -> BuildConfig:
    """The slide primitives showcase in data/presentation/demo/, as its own deck.

    Those sources sit in a subdirectory, and get_sorted_markdown_files() lists
    one level, so for a long time nothing built them at all -- two rotted
    references (a missing image, a moved theme path) sat in them unnoticed
    because no build ever read them. They are showcase material rather than part
    of the published talk, so they get a target of their own instead of being
    folded into it.
    """
    config = beamer()
    config.input_dir = "data/presentation/demo"
    config.default_output_name = "demo_output.pdf"
    config.log_file = "data/out/demo.json"
    # The demo sources cite nothing, and citeproc with no citations still wants
    # the bibliography to exist.
    config.bibliography = ""
    config.citeproc = False
    return config


def example() -> BuildConfig:
    """The minimal starter document in data/example/chapters/.

    data/example/chapters/02-getting-started.md tells a newcomer to put their
    Markdown here and run `make book` -- which builds data/book/ instead, so the
    instruction could not work and the example was unbuildable. This is the
    target that makes it true.

    A single pandoc call straight to PDF: no bibliography, glossary or
    nomenclature, so it needs none of the multi-pass TeX pipeline the book does.
    """
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
