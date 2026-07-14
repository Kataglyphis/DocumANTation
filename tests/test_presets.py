"""Tests for the document build presets."""

from __future__ import annotations

from md2pdfLib.pandoc_builder import BuildConfig
from md2pdfLib.presets import PRESETS, beamer, book, diss


def test_presets_registry_keys():
    assert set(PRESETS) == {"book", "diss", "beamer"}


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
