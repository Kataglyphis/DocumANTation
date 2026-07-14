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
