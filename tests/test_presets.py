"""Tests for the document build presets."""

from __future__ import annotations

from md2pdfLib.pandoc_builder import BuildConfig
from md2pdfLib.presets import PPTX_REFERENCE, PRESETS, beamer, book, diss, pptx


def test_presets_registry_keys():
    assert set(PRESETS) == {"book", "diss", "beamer", "pptx"}


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


def test_book_and_diss_differ_only_where_expected():
    b, d = book(), diss()
    # Same staged book pipeline...
    assert b.input_dir == d.input_dir
    assert b.top_level_division == d.top_level_division
    # ...but a different highlight theme and log file.
    assert b.highlight_style != d.highlight_style
    assert b.log_file != d.log_file


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
