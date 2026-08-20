"""Tests for brand-divs.lua, the one bridge from Markdown to every output.

That filter decides what the book, the slides, the deck and the website
actually contain -- 330 lines and eighteen handlers -- and it had no tests at
all. Three defects had accumulated behind that gap:

- a tab-set printed every tab's *label* but only the first tab's *body*, so the
  book advertised C++ and GLSL sections it did not contain;
- the document-level handler was registered as ``Doc``, which pandoc never
  calls (the key is ``Pandoc``), so the "List of Listings" the filter's own
  header documented was never emitted;
- ``FORMAT:match("latex") and not FORMAT:match("beamer") ~= nil`` reads as
  ``... and ((not X) ~= nil)`` in Lua, which is always true -- the beamer
  exclusion did nothing, and only worked out because pandoc reports "beamer"
  rather than "latex" for that writer.

These run pandoc for real, because the filter's contract is what pandoc does
with it, not what the Lua looks like.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
FILTER = REPO_ROOT / "md2pdfLib" / "common" / "filters" / "brand-divs.lua"

pytestmark = pytest.mark.skipif(
    shutil.which("pandoc") is None, reason="pandoc not on PATH (CI installs it; the image has it)"
)


def render(markdown: str, to: str = "latex") -> str:
    """Run the filter over *markdown* and return pandoc's output."""
    result = subprocess.run(
        ["pandoc", "--lua-filter", str(FILTER), "-t", to, "-f", "markdown"],
        input=markdown,
        capture_output=True,
        text=True,
        check=True,
        encoding="utf-8",
    )
    return result.stdout


# ── admonitions ──────────────────────────────────────────────────────────────


def test_a_titled_admonition_becomes_its_environment_with_the_title():
    out = render('::: {.note title="Watch out"}\nBody text.\n:::\n')
    assert "\\begin{note}{Watch out}" in out
    assert "Body text." in out
    assert "\\end{note}" in out


def test_an_untitled_admonition_takes_no_title_argument():
    """\\begin{note}{} would render an empty title bar."""
    out = render("::: {.note}\nBody text.\n:::\n")
    assert "\\begin{note}" in out
    assert "\\begin{note}{" not in out


def test_a_title_with_latex_specials_is_escaped():
    """An unescaped & or _ in a title is a LaTeX error, not a typo."""
    out = render('::: {.warning title="A & B_C #1"}\nx\n:::\n')
    assert "\\&" in out and "\\_" in out and "\\#" in out


@pytest.mark.parametrize("cls", ["note", "warning", "tip", "important", "theorem", "proof"])
def test_every_documented_admonition_class_maps_to_an_environment(cls: str):
    out = render(f"::: {{.{cls}}}\nx\n:::\n")
    assert f"\\begin{{{cls}}}" in out


def test_html_output_leaves_the_div_for_sphinx_to_style():
    """The website renders these itself; raw LaTeX there would be printed text."""
    out = render('::: {.note title="T"}\nBody.\n:::\n', to="html")
    assert "\\begin{note}" not in out
    assert "note" in out


# ── tab sets: every tab must survive ──────────────────────────────────────────


TAB_SET = """::: {.tab-set}

::: {.tab title="Rust"}
RUSTBODYMARKER
:::

::: {.tab title="C++"}
CPPBODYMARKER
:::

::: {.tab title="GLSL"}
GLSLBODYMARKER
:::

:::
"""


def test_a_tab_set_renders_every_tab_body_not_just_the_first():
    """The defect this test exists for: two of three bodies were dropped.

    Print has no interactive tabs, so the only honest rendering is to show
    them all. Showing one body under a bar naming three is content loss that
    reads to the reader as a broken document.
    """
    # Markers carry no underscore on purpose: LaTeX escapes _ to \_, so a
    # marker containing one never matches the rendered output verbatim.
    out = render(TAB_SET)
    for marker in ("RUSTBODYMARKER", "CPPBODYMARKER", "GLSLBODYMARKER"):
        assert marker in out, f"{marker} was dropped from the output"


def test_a_tab_set_labels_every_tab_it_renders():
    out = render(TAB_SET)
    for title in ("Rust", "C++", "GLSL"):
        assert title in out


def test_a_tab_set_never_advertises_a_tab_whose_body_is_missing():
    """Labels and bodies must come in pairs -- that is the whole bug."""
    out = render(TAB_SET)
    labelled = [t for t in ("Rust", "C++", "GLSL") if t in out]
    bodied = [
        t
        for t, m in (
            ("Rust", "RUSTBODYMARKER"),
            ("C++", "CPPBODYMARKER"),
            ("GLSL", "GLSLBODYMARKER"),
        )
        if m in out
    ]
    assert labelled == bodied


def test_an_empty_tab_set_is_left_alone():
    out = render("::: {.tab-set}\nnothing here\n:::\n")
    assert "nothing here" in out


# ── code blocks ──────────────────────────────────────────────────────────────


def test_a_titled_listing_gets_a_titled_box():
    out = render('```rust {.listing title="src/main.rs"}\nfn main() {}\n```\n')
    assert "tcolorbox" in out
    assert "src/main.rs" in out
    # The body is syntax-highlighted, so it arrives split across token macros.
    assert "main()" in out


def test_a_plain_code_block_is_left_to_the_normal_highlighter():
    """Only .listing blocks get a box; everything else keeps Shaded/Highlighting."""
    out = render("```rust\nfn main() {}\n```\n")
    assert "tcolorbox" not in out


def test_a_listing_title_with_specials_is_escaped():
    out = render('```c {.listing title="a_b & c"}\nx\n```\n')
    assert "\\_" in out and "\\&" in out


# ── spans ────────────────────────────────────────────────────────────────────


def test_a_gls_span_becomes_a_glossary_reference():
    out = render("The [GPU]{.gls} is fast.\n")
    assert "\\gls{gpu}" in out


def test_a_nomen_span_registers_a_nomenclature_entry():
    out = render('[BRDF]{.nomen def="Bidirectional reflectance"} matters.\n')
    assert "\\nomenclature{BRDF}{Bidirectional reflectance}" in out


# ── speaker notes ────────────────────────────────────────────────────────────


def test_speaker_notes_are_stripped_from_the_book():
    """A \\note outside beamer is an undefined command."""
    out = render("::: {.notes}\nSay this out loud.\n:::\n")
    assert "Say this out loud." not in out
    assert "\\note{" not in out


def test_speaker_notes_survive_into_beamer():
    out = render("::: {.notes}\nSay this out loud.\n:::\n", to="beamer")
    assert "\\note{" in out
    assert "Say this out loud" in out


# ── format detection ─────────────────────────────────────────────────────────


def test_beamer_and_book_take_different_column_syntax():
    """The precedence bug made the beamer/latex split accidental; pin it."""
    columns = "::: {.columns}\n\n::: {.column}\nLEFT\n:::\n\n::: {.column}\nRIGHT\n:::\n\n:::\n"
    book = render(columns)
    slides = render(columns, to="beamer")

    assert "minipage" in book and "\\column{" not in book
    assert "\\begin{columns}" in slides and "minipage" not in slides
    for out in (book, slides):
        assert "LEFT" in out and "RIGHT" in out


def test_the_filter_emits_no_raw_latex_into_html():
    """Every handler must check the format; one that forgets shows LaTeX to readers."""
    source = (
        '::: {.note title="T"}\nx\n:::\n\n'
        "::: {.columns}\n\n::: {.column}\ny\n:::\n\n:::\n\n"
        'The [GPU]{.gls} and [BRDF]{.nomen def="d"}.\n\n'
        '```rust {.listing title="f.rs"}\nz\n```\n'
    )
    out = render(source, to="html")
    for leak in ("\\begin{", "\\gls{", "\\nomenclature{", "tcolorbox", "minipage"):
        assert leak not in out, f"{leak} leaked into HTML output"
