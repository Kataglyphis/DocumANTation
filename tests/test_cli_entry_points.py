"""Tests for the command-line entry points every build actually goes through.

These were the repo's coverage hole: ``md2pdfLib/build.py`` sat at 0% -- nothing
tested the CLI that each of the six document targets invokes -- and the ``main()``
of the strict gate and the brand gate were uncovered too. All three were
exercised only by running a container build by hand.

They are also where the argument plumbing lives, and that plumbing changed:
``run_from_cli`` used to read the output name back out of ``sys.argv``, which
meant build.py had to rewrite ``sys.argv`` to hand a parsed value over.
"""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from md2pdfLib import build as build_cli
from md2pdfLib import check_build_log
from md2pdfLib.pandoc_builder import BuildConfig, BuildError
from md2pdfLib.presentation.pptx import verify_brand
from md2pdfLib.presets import PRESETS

REPO_ROOT = Path(__file__).resolve().parents[1]
BRAND = json.loads((REPO_ROOT / "style" / "brand.tokens.json").read_text("utf-8"))


# ── md2pdfLib/build.py ───────────────────────────────────────────────────────


@pytest.fixture
def captured(monkeypatch) -> list[tuple[BuildConfig, str | None]]:
    """Record what build.py hands to run_from_cli instead of running pandoc."""
    calls: list[tuple[BuildConfig, str | None]] = []

    def fake(config: BuildConfig, output_name: str | None = None) -> None:
        calls.append((config, output_name))

    monkeypatch.setattr(build_cli, "run_from_cli", fake)
    return calls


@pytest.mark.parametrize("name", sorted(PRESETS))
def test_every_registered_type_is_reachable_from_the_cli(monkeypatch, captured, name: str):
    """`build.py <type>` must resolve to that preset, for all of them.

    The choices come from PRESETS, so a preset added without a CLI entry is
    impossible -- this pins that they stay in step.
    """
    monkeypatch.setattr("sys.argv", ["build.py", name])
    build_cli.main()
    (config, output_name) = captured[0]
    assert config == PRESETS[name]()
    assert output_name is None


def test_the_output_name_is_passed_as_an_argument(monkeypatch, captured):
    """Not via sys.argv. The old path rewrote sys.argv to smuggle it across,
    which any later argv reader in the process would have seen."""
    monkeypatch.setattr("sys.argv", ["build.py", "book", "mybook.tex"])
    build_cli.main()
    (config, output_name) = captured[0]
    assert output_name == "mybook.tex"
    # And the preset itself is untouched, so nothing leaks into the next build.
    assert config.output_name is None


def test_sys_argv_is_left_alone(monkeypatch, captured):
    monkeypatch.setattr("sys.argv", ["build.py", "book", "mybook.tex"])
    build_cli.main()
    import sys

    assert sys.argv == ["build.py", "book", "mybook.tex"]


def test_an_unknown_type_is_a_usage_error(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["build.py", "nope"])
    with pytest.raises(SystemExit) as exc:
        build_cli.main()
    assert exc.value.code == 2
    assert "invalid choice" in capsys.readouterr().err


def test_no_type_at_all_is_a_usage_error(monkeypatch):
    monkeypatch.setattr("sys.argv", ["build.py"])
    with pytest.raises(SystemExit) as exc:
        build_cli.main()
    assert exc.value.code == 2


def test_the_repo_root_wrapper_exposes_the_same_main():
    """build.py at the root is a thin wrapper; the container calls the inner one."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("root_build", REPO_ROOT / "build.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.main is build_cli.main


def test_a_build_error_is_a_message_not_a_traceback(monkeypatch, capsys):
    """`Errors raise BuildError ... never silent` -- but also never a traceback."""
    from md2pdfLib import pandoc_builder

    def boom(config):
        raise BuildError("pandoc exploded")

    monkeypatch.setattr(pandoc_builder, "run_pandoc", boom)
    with pytest.raises(SystemExit) as exc:
        pandoc_builder.run_from_cli(PRESETS["book"]())
    assert exc.value.code == 1
    assert capsys.readouterr().err.strip() == "Error: pandoc exploded"


# ── md2pdfLib/check_build_log.py ─────────────────────────────────────────────


def test_the_strict_gate_passes_a_clean_log(monkeypatch, tmp_path, capsys):
    log = tmp_path / "clean.log"
    log.write_text("Output written on x.pdf (4 pages).\n", encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["check_build_log.py", str(log), "--format", "latex"])
    check_build_log.run_from_cli()
    assert "No warnings found" in capsys.readouterr().out


def test_the_strict_gate_fails_on_an_overfull_box(monkeypatch, tmp_path, capsys):
    log = tmp_path / "bad.log"
    log.write_text("Overfull \\hbox (13.1pt too wide) in paragraph\n", encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["check_build_log.py", str(log)])
    with pytest.raises(SystemExit) as exc:
        check_build_log.run_from_cli()
    assert exc.value.code == 1
    assert "Overfull" in capsys.readouterr().err


def test_the_strict_gate_reports_advisories_and_still_passes(monkeypatch, tmp_path, capsys):
    """What the book build relies on: reported, counted, not fatal."""
    log = tmp_path / "loose.log"
    log.write_text("Underfull \\hbox (badness 4846) in paragraph\n", encoding="utf-8")
    monkeypatch.setattr(
        "sys.argv",
        [
            "check_build_log.py",
            str(log),
            "--advisory-regex",
            r"^\s*Underfull \\hbox",
        ],
    )
    check_build_log.run_from_cli()
    out = capsys.readouterr()
    assert "1 advisory" in out.out
    assert "Underfull" in out.err  # printed, not hidden


def test_the_strict_gate_refuses_a_log_that_does_not_exist(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr("sys.argv", ["check_build_log.py", str(tmp_path / "gone.log")])
    with pytest.raises(SystemExit) as exc:
        check_build_log.run_from_cli()
    assert exc.value.code == 1
    assert "does not exist" in capsys.readouterr().err


def test_the_strict_gate_refuses_invalid_json(monkeypatch, tmp_path, capsys):
    log = tmp_path / "broken.json"
    log.write_text("{not json", encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["check_build_log.py", str(log), "--format", "pandoc-json"])
    with pytest.raises(SystemExit) as exc:
        check_build_log.run_from_cli()
    assert exc.value.code == 1
    assert "invalid Pandoc JSON" in capsys.readouterr().err


def test_the_strict_gate_refuses_a_json_log_that_is_not_an_array(monkeypatch, tmp_path, capsys):
    log = tmp_path / "obj.json"
    log.write_text('{"verbosity": "WARNING"}', encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["check_build_log.py", str(log), "--format", "pandoc-json"])
    with pytest.raises(SystemExit) as exc:
        check_build_log.run_from_cli()
    assert exc.value.code == 1
    assert "expected a JSON array" in capsys.readouterr().err


# ── md2pdfLib/presentation/pptx/verify_brand.py ──────────────────────────────


# The gate parses every XML part (a regex scan matches broken markup happily),
# so a fixture has to declare the prefixes it uses or it fails as malformed --
# which is the check doing its job, not a fixture detail worth hiding.
_A_NS = 'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"'
_P_NS = 'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"'


def _deck(path: Path, *, theme: str = "", slide: str = "", font: str | None = None) -> Path:
    """A well-formed deck with just the parts the brand gate inspects."""
    face = BRAND["fonts"]["main"] if font is None else font
    fonts = (
        f'<a:majorFont><a:latin typeface="{face}"/></a:majorFont>'
        f'<a:minorFont><a:latin typeface="{face}"/></a:minorFont>'
    )
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("ppt/theme/theme1.xml", f"<a:theme {_A_NS}>{fonts}{theme}</a:theme>")
        z.writestr("ppt/slides/slide1.xml", f"<p:sld {_P_NS} {_A_NS}>{slide}</p:sld>")
    return path


def test_the_brand_gate_passes_an_on_brand_deck(monkeypatch, tmp_path, capsys):
    accent = BRAND["colors"]["accent"].lstrip("#").upper()
    deck = _deck(tmp_path / "ok.pptx", theme=f'<a:srgbClr val="{accent}"/>')
    monkeypatch.setattr("sys.argv", ["verify_brand.py", str(deck)])
    verify_brand.main()
    assert "every colour is a brand value" in capsys.readouterr().out


def test_the_brand_gate_reports_every_way_a_deck_is_wrong_at_once(monkeypatch, tmp_path, capsys):
    """One build should name all of them, not just the first."""
    deck = _deck(tmp_path / "bad.pptx", theme='<a:srgbClr val="4F81BD"/>', font="Calibri")
    monkeypatch.setattr("sys.argv", ["verify_brand.py", str(deck)])
    with pytest.raises(SystemExit) as exc:
        verify_brand.main()
    assert exc.value.code == 1
    err = capsys.readouterr().err
    assert "colours that are not in the brand" in err
    assert "theme fonts are not the brand font" in err


def test_the_brand_gate_catches_a_malformed_part(monkeypatch, tmp_path, capsys):
    """A regex scan matches broken markup happily; only the parse notices."""
    deck = tmp_path / "broken.pptx"
    with zipfile.ZipFile(deck, "w") as z:
        z.writestr("ppt/theme/theme1.xml", "<a:theme>")  # never closed
        z.writestr("ppt/slides/slide1.xml", "<p:sld/>")
    monkeypatch.setattr("sys.argv", ["verify_brand.py", str(deck)])
    with pytest.raises(SystemExit) as exc:
        verify_brand.main()
    assert exc.value.code == 1
    assert "not well-formed" in capsys.readouterr().err


def test_the_brand_gate_refuses_a_deck_that_does_not_exist(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr("sys.argv", ["verify_brand.py", str(tmp_path / "gone.pptx")])
    with pytest.raises(SystemExit) as exc:
        verify_brand.main()
    assert exc.value.code == 1
    assert "no such deck" in capsys.readouterr().err


def test_the_brand_gate_usage_error(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["verify_brand.py"])
    with pytest.raises(SystemExit) as exc:
        verify_brand.main()
    assert exc.value.code == 2
    assert "Usage:" in capsys.readouterr().err


def test_off_brand_fonts_flags_a_theme_with_no_typeface(tmp_path):
    deck = tmp_path / "nofont.pptx"
    with zipfile.ZipFile(deck, "w") as z:
        z.writestr("ppt/theme/theme1.xml", "<a:theme/>")
    offenders = verify_brand.off_brand_fonts(deck, BRAND["fonts"]["main"])
    assert offenders == {"ppt/theme/theme1.xml": {"(no majorFont/minorFont latin typeface)"}}
