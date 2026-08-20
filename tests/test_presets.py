"""Tests for the document build presets."""

from __future__ import annotations

from md2pdfLib.pandoc_builder import BuildConfig
from md2pdfLib.presets import PPTX_REFERENCE, PRESETS, beamer, book, demo, example, pptx


def test_presets_registry_keys():
    assert set(PRESETS) == {"book", "beamer", "demo", "example", "pptx"}


def test_all_presets_return_buildconfig():
    for factory in PRESETS.values():
        assert isinstance(factory(), BuildConfig)


def test_book_preset_shape():
    cfg = book()
    assert cfg.input_dir == "./data/book/chapters"
    assert cfg.top_level_division == "chapter"
    assert cfg.biblatex is True
    assert cfg.toc is True
    assert cfg.number_sections is True
    assert cfg.output_suffix == ".tex"


def test_beamer_preset_targets_beamer():
    cfg = beamer()
    assert cfg.output_suffix == ".pdf"
    assert cfg.citeproc is True
    assert "beamer" in cfg.extra_args
    assert "-t" in cfg.extra_args


def test_pptx_preset_targets_pptx():
    cfg = pptx()
    assert cfg.output_suffix == ".pptx"
    assert cfg.citeproc is True
    assert "pptx" in cfg.extra_args
    assert "-t" in cfg.extra_args


def test_pptx_uses_the_generated_reference_deck():
    """Without --reference-doc a pptx is stock Office blue, not the brand."""
    args = pptx().extra_args
    assert "--reference-doc" in args
    assert args[args.index("--reference-doc") + 1] == PPTX_REFERENCE


def test_pptx_and_beamer_render_the_same_deck():
    """One markdown source, two outputs -- so the two decks cannot drift apart."""
    p, b = pptx(), beamer()
    assert p.input_dir == b.input_dir
    assert p.metadata_file == b.metadata_file
    assert p.bibliography == b.bibliography
    # Same slide boundaries, so the decks have the same slides.
    assert "--slide-level=2" in p.extra_args
    assert "--slide-level=2" in b.extra_args
    # Same code palette as the beamer slides and the website.
    assert p.highlight_style == b.highlight_style
    # ...but their own outputs and logs, or one would overwrite the other.
    assert p.log_file != b.log_file
    assert p.default_output_name != b.default_output_name


def test_demo_is_the_beamer_pipeline_over_its_own_sources():
    """It shares beamer's template and theme so the showcase looks like the deck."""
    d, b = demo(), beamer()
    assert d.input_dir == "data/presentation/demo"
    assert d.input_dir != b.input_dir
    assert d.metadata_file == b.metadata_file
    assert d.highlight_style == b.highlight_style
    assert "beamer" in d.extra_args
    # Its own output and log, or it would overwrite the published deck's.
    assert d.default_output_name != b.default_output_name
    assert d.log_file != b.log_file
    # The demo sources cite nothing; citeproc with no bibliography is a failure
    # waiting for the first build, not a harmless leftover.
    assert d.bibliography == ""
    assert d.citeproc is False


def test_example_is_a_single_pass_pdf():
    """The starter document must not need biber or makeglossaries to build.

    A newcomer's first build failing inside a TeX tool they have not read about
    is the worst possible introduction, so the example carries no bibliography,
    glossary or nomenclature and goes straight to PDF in one pandoc call.
    """
    cfg = example()
    assert cfg.output_suffix == ".pdf"
    assert cfg.biblatex is False
    assert cfg.citeproc is False
    assert cfg.bibliography == ""
    assert cfg.toc is True


def test_example_does_not_borrow_the_book_metadata():
    """base.yml carries the book's title and bibliography.

    Sharing it would title the example "Computer graphics" and demand biber for
    a document with no citations.
    """
    assert example().metadata_file != book().metadata_file
    assert example().metadata_file == "md2pdfLib/example/pandoc/metadata.yml"


def test_every_preset_writes_its_own_output_and_log():
    """Two presets sharing either would have the second silently clobber the first."""
    configs = {name: factory() for name, factory in PRESETS.items()}
    outputs = [c.default_output_name for c in configs.values()]
    logs = [c.log_file for c in configs.values() if c.log_file]
    assert len(outputs) == len(set(outputs)), f"duplicate output names: {sorted(outputs)}"
    assert len(logs) == len(set(logs)), f"duplicate log files: {sorted(logs)}"
