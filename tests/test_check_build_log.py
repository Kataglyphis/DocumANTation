"""Tests for the strict build-log warning detector."""

from __future__ import annotations

import json
import re
from pathlib import Path

from md2pdfLib.check_build_log import _find_warning_lines, _load_pandoc_json_text


def test_detects_latex_and_badbox_warnings():
    text = "\n".join(
        [
            "This is normal output.",
            "LaTeX Warning: Reference `foo' undefined.",
            "Package hyperref Warning: Token not allowed.",
            "Overfull \\hbox (12.3pt too wide) in paragraph",
            "Underfull \\hbox (badness 10000)",
        ]
    )
    found = _find_warning_lines(text, [])
    assert len(found) == 4
    assert all("normal output" not in line for line in found)


def test_clean_log_has_no_warnings():
    assert _find_warning_lines("all good\ncompiled cleanly\n", []) == []


def test_ignore_regex_suppresses_matching_warnings():
    text = "LaTeX Warning: Reference `foo' undefined.\nLaTeX Warning: Something else."
    ignore = [re.compile(r"Reference `foo' undefined")]
    found = _find_warning_lines(text, ignore)
    assert len(found) == 1
    assert "Something else" in found[0]


def test_load_pandoc_json_extracts_latex_output(tmp_path: Path):
    payload = [
        {"description": "other", "contents": "ignore me"},
        {"description": "LaTeX output", "contents": "LaTeX Warning: boom"},
    ]
    log = tmp_path / "beamer.json"
    log.write_text(json.dumps(payload), encoding="utf-8")
    text = _load_pandoc_json_text(log)
    assert "LaTeX Warning: boom" in text
    assert _find_warning_lines(text, []) == ["LaTeX Warning: boom"]


def test_detects_missing_characters():
    # A glyph the font lacks is dropped from the PDF silently; LuaTeX reports it
    # without the word "Warning", so it needs its own pattern.
    text = "\n".join(
        [
            "Missing character: There is no λ (U+03BB) in font Latin Modern Mono!",
            "[WARNING] Missing character: There is no ∑ (U+2211) in font ...",
            "This line is fine.",
        ]
    )
    found = _find_warning_lines(text, [])
    assert len(found) == 2
    assert all("fine" not in line for line in found)


def test_missing_character_can_be_ignored_explicitly():
    text = "Missing character: There is no λ (U+03BB) in font X!"
    assert _find_warning_lines(text, [re.compile(r"U\+03BB")]) == []


def test_detects_vbox_badness():
    # A vertically overfull page loses content past the bottom margin just as
    # an \hbox loses it past the edge; only \hbox used to be caught.
    text = "\n".join(
        [
            "Overfull \\vbox (7.6pt too high) detected at line 42",
            "Underfull \\vbox (badness 10000) has occurred",
        ]
    )
    assert len(_find_warning_lines(text, [])) == 2


def test_detects_pandoc_warning_lines():
    text = "[WARNING] Could not fetch resource images/missing.png\n[INFO] Loaded thing"
    found = _find_warning_lines(text, [])
    assert found == ["[WARNING] Could not fetch resource images/missing.png"]


def test_pandoc_json_surfaces_warning_entries_alongside_latex_output(tmp_path: Path):
    # Pandoc's own WARNING entries used to be read only when no LaTeX output
    # existed, so any build that reached LaTeX passed the gate with them unseen.
    payload = [
        {"verbosity": "WARNING", "pretty": "Duplicate identifier 'intro'"},
        {"verbosity": "INFO", "pretty": "Loaded template"},
        {"description": "LaTeX output", "contents": "clean latex log"},
    ]
    log = tmp_path / "beamer.json"
    log.write_text(json.dumps(payload), encoding="utf-8")
    text = _load_pandoc_json_text(log)
    assert "clean latex log" in text
    assert _find_warning_lines(text, []) == ["[WARNING] Duplicate identifier 'intro'"]
