"""Unit tests for the pure helpers in md2pdfLib.pandoc_builder.

These exercise the command-assembly and input-discovery logic without invoking
pandoc or LaTeX, so they run fast in CI.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from md2pdfLib.pandoc_builder import (
    PROJECT_ROOT,
    BuildConfig,
    BuildError,
    build_pandoc_cmd,
    get_sorted_markdown_files,
    resolve_project_path,
    safe_output_name,
)

# ── safe_output_name ─────────────────────────────────────────────────────────


def test_safe_output_name_appends_default_suffix():
    assert safe_output_name("chapter", default_suffix=".tex") == "chapter.tex"


@pytest.mark.parametrize("name", ["out.tex", "out.pdf", "out.log"])
def test_safe_output_name_keeps_known_suffixes(name):
    assert safe_output_name(name) == name


def test_safe_output_name_strips_path_components():
    # Path traversal attempt collapses to the basename, then gets a suffix.
    assert safe_output_name("../../etc/passwd") == "passwd.tex"


@pytest.mark.parametrize("bad", ["", "spaces here", "semi;colon", "star*"])
def test_safe_output_name_rejects_invalid(bad):
    with pytest.raises(BuildError):
        safe_output_name(bad)


def test_safe_output_name_reduces_dir_path_to_basename():
    # A trailing-slash path reduces to its final segment, which is valid.
    assert safe_output_name("slash/only/") == "only.tex"


# ── markdown discovery / sorting ─────────────────────────────────────────────


def test_get_sorted_markdown_files_orders_by_numeric_prefix(tmp_path: Path):
    for name in ["10-ten.md", "02-two.md", "01-one.md", "notes.txt"]:
        (tmp_path / name).write_text("x", encoding="utf-8")
    result = [Path(p).name for p in get_sorted_markdown_files(tmp_path)]
    assert result == ["01-one.md", "02-two.md", "10-ten.md"]


def test_get_sorted_markdown_files_ties_break_by_name(tmp_path: Path):
    # Same numeric prefix must not fall back to filesystem order, which
    # differs between machines.
    for name in ["01-beta.md", "01-alpha.md", "02-gamma.md"]:
        (tmp_path / name).write_text("x", encoding="utf-8")
    result = [Path(p).name for p in get_sorted_markdown_files(tmp_path)]
    assert result == ["01-alpha.md", "01-beta.md", "02-gamma.md"]


def test_get_sorted_markdown_files_rejects_non_numeric_prefix(tmp_path: Path):
    (tmp_path / "intro.md").write_text("x", encoding="utf-8")
    with pytest.raises(BuildError):
        get_sorted_markdown_files(tmp_path)


def test_get_sorted_markdown_files_empty_dir(tmp_path: Path):
    with pytest.raises(BuildError):
        get_sorted_markdown_files(tmp_path)


def test_get_sorted_markdown_files_missing_dir(tmp_path: Path):
    with pytest.raises(BuildError):
        get_sorted_markdown_files(tmp_path / "does-not-exist")


# ── resolve_project_path ─────────────────────────────────────────────────────


def test_resolve_project_path_relative_is_under_root():
    assert resolve_project_path("data/out") == PROJECT_ROOT / "data/out"


def test_resolve_project_path_absolute_unchanged(tmp_path: Path):
    assert resolve_project_path(str(tmp_path)) == tmp_path


# ── build_pandoc_cmd ─────────────────────────────────────────────────────────


def _cfg(**kw) -> BuildConfig:
    base = {"input_dir": "in", "metadata_file": "meta.yml"}
    base.update(kw)
    return BuildConfig(**base)


def test_build_pandoc_cmd_core_shape():
    cmd = build_pandoc_cmd(_cfg(), ["01-a.md", "02-b.md"], "out/book.tex")
    assert cmd[0] == "pandoc"
    assert cmd[1:3] == ["01-a.md", "02-b.md"]
    assert "--pdf-engine" in cmd and "lualatex" in cmd
    assert "--metadata-file" in cmd
    # output path always comes last, right after -o
    assert cmd[-2:] == ["-o", "out/book.tex"]


def test_build_pandoc_cmd_bool_and_number_flags():
    cmd = build_pandoc_cmd(
        _cfg(toc=True, number_sections=True, number_offset=2), ["01-a.md"], "o.tex"
    )
    assert "--toc" in cmd
    assert "--number-sections" in cmd
    i = cmd.index("--number-offset")
    assert cmd[i + 1] == "2"


def test_build_pandoc_cmd_number_offset_ignored_without_number_sections():
    cmd = build_pandoc_cmd(_cfg(number_offset=5), ["01-a.md"], "o.tex")
    assert "--number-offset" not in cmd


def test_build_pandoc_cmd_extra_args_precede_output():
    cmd = build_pandoc_cmd(_cfg(extra_args=["-t", "beamer"]), ["01-a.md"], "o.pdf")
    assert "beamer" in cmd
    assert cmd.index("-t") < cmd.index("-o")


def test_build_pandoc_cmd_str_flags_only_when_set():
    cmd = build_pandoc_cmd(_cfg(document_class="scrbook"), ["01-a.md"], "o.tex")
    j = cmd.index("--documentclass")
    assert cmd[j + 1] == "scrbook"
