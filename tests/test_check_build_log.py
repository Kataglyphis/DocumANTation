"""Tests for the strict build-log warning detector."""

from __future__ import annotations

import json
import re
from pathlib import Path

from md2pdfLib.check_build_log import (
    _find_warning_lines,
    _load_pandoc_json_text,
    _split_advisories,
)


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


def test_pandoc_json_surfaces_warnings_when_the_target_never_reaches_latex(tmp_path: Path):
    """A pptx build emits no "LaTeX output" entries, and is still strict-gated.

    Its log therefore always took the no-LaTeX return, where the [WARNING]
    marker the detector matches was never added -- so pandoc could report a
    missing resource and the deck still built clean under STRICT_WARNINGS=1.
    """
    payload = [
        {"verbosity": "WARNING", "pretty": "Could not fetch resource images/missing.png"},
        {"verbosity": "INFO", "pretty": "Loaded reference.pptx"},
    ]
    log = tmp_path / "pptx.json"
    log.write_text(json.dumps(payload), encoding="utf-8")
    text = _load_pandoc_json_text(log)
    assert _find_warning_lines(text, []) == [
        "[WARNING] Could not fetch resource images/missing.png"
    ]


# ── advisories: reported, never fatal ────────────────────────────────────────
#
# The book's strict build treats two diagnostics as advisory (see
# md2pdfLib/scripts/compile_with_glossaries.sh): a loose line and a tcolorbox
# page-break hint. Both cost quality and lose nothing, unlike an overfull box.

ADVISORY_PATTERNS = [
    re.compile(r"^\s*Underfull \\hbox"),
    re.compile(r"Package tcolorbox Warning: Using nobreak failed"),
]


def test_a_loose_line_is_advisory_but_an_overfull_one_is_not():
    text = "\n".join(
        [
            "Underfull \\hbox (badness 4846) in paragraph at lines 10--12",
            "Overfull \\hbox (13.1pt too wide) in paragraph at lines 20--22",
        ]
    )
    fatal, advisory = _split_advisories(_find_warning_lines(text, []), ADVISORY_PATTERNS)
    assert len(advisory) == 1 and "Underfull" in advisory[0]
    # Text past the margin is a defect, not a nit -- it must still fail.
    assert len(fatal) == 1 and "Overfull" in fatal[0]


def test_an_underfull_vbox_still_fails():
    """Only \\hbox is advisory: a short \\vbox is a page-content problem."""
    text = "Underfull \\vbox (badness 10000) has occurred while \\output is active"
    fatal, advisory = _split_advisories(_find_warning_lines(text, []), ADVISORY_PATTERNS)
    assert advisory == []
    assert len(fatal) == 1


def test_the_tcolorbox_page_break_hint_is_advisory():
    text = "Package tcolorbox Warning: Using nobreak failed. Try to enlarge `lines before break'"
    fatal, advisory = _split_advisories(_find_warning_lines(text, []), ADVISORY_PATTERNS)
    assert len(advisory) == 1
    assert fatal == []


def test_other_package_warnings_stay_fatal():
    """Narrowing the gate must not let a real package warning through."""
    text = "\n".join(
        [
            "Package fvextra Warning: csquotes should be loaded after fvextra",
            "LaTeX Warning: Command \\@parboxrestore  has changed.",
            "Missing character: There is no lambda in font Roboto!",
        ]
    )
    fatal, advisory = _split_advisories(_find_warning_lines(text, []), ADVISORY_PATTERNS)
    assert advisory == []
    assert len(fatal) == 3


def test_advisories_are_kept_not_dropped():
    """--ignore-regex drops a line; --advisory-regex must still report it."""
    text = "Underfull \\hbox (badness 4846) in paragraph at lines 10--12"
    dropped = _find_warning_lines(text, [re.compile(r"Underfull \\hbox")])
    assert dropped == []  # what --ignore-regex would do
    fatal, advisory = _split_advisories(_find_warning_lines(text, []), ADVISORY_PATTERNS)
    assert fatal == [] and len(advisory) == 1  # what --advisory-regex does instead


def test_no_advisory_patterns_means_everything_is_fatal():
    text = "Underfull \\hbox (badness 4846) in paragraph at lines 10--12"
    fatal, advisory = _split_advisories(_find_warning_lines(text, []), [])
    assert len(fatal) == 1 and advisory == []
