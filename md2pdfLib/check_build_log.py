"""Validate build logs for warnings that should fail strict builds."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

WARNING_LINE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"^\s*(?:LaTeX|Package|Class)\b.*Warning:"),
    re.compile(r"^\s*(?:Under|Over)full \\hbox"),
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fail when build logs contain warnings or bad box diagnostics.",
    )
    parser.add_argument("log_path", type=Path, help="Path to a LaTeX log or Pandoc JSON log")
    parser.add_argument(
        "--format",
        choices=("latex", "pandoc-json"),
        default="latex",
        help="Input log format",
    )
    parser.add_argument(
        "--ignore-regex",
        action="append",
        default=[],
        help="Regex for warning lines that should be ignored",
    )
    return parser.parse_args()


def _load_latex_text(log_path: Path) -> str:
    return log_path.read_text(encoding="utf-8", errors="replace")


def _load_pandoc_json_text(log_path: Path) -> str:
    try:
        payload = json.loads(log_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"Error: invalid Pandoc JSON log {log_path}: {exc}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(payload, list):
        print(f"Error: expected a JSON array in {log_path}", file=sys.stderr)
        sys.exit(1)

    latex_outputs: list[str] = []
    for entry in payload:
        if not isinstance(entry, dict):
            continue
        if entry.get("description") != "LaTeX output":
            continue
        contents = entry.get("contents")
        if isinstance(contents, str):
            latex_outputs.append(contents)

    if latex_outputs:
        return latex_outputs[-1]

    return "\n".join(
        entry.get("pretty", "")
        for entry in payload
        if isinstance(entry, dict) and isinstance(entry.get("pretty"), str)
    )


def _load_log_text(log_path: Path, log_format: str) -> str:
    if log_format == "pandoc-json":
        return _load_pandoc_json_text(log_path)
    return _load_latex_text(log_path)


def _find_warning_lines(text: str, ignore_patterns: list[re.Pattern[str]]) -> list[str]:
    warning_lines: list[str] = []
    for line in text.splitlines():
        if not any(pattern.search(line) for pattern in WARNING_LINE_PATTERNS):
            continue
        if any(pattern.search(line) for pattern in ignore_patterns):
            continue
        warning_lines.append(line)
    return warning_lines


def run_from_cli() -> None:
    """Validate the selected log file and exit non-zero on warnings."""
    args = _parse_args()
    if not args.log_path.is_file():
        print(f"Error: log file does not exist: {args.log_path}", file=sys.stderr)
        sys.exit(1)

    ignore_patterns = [re.compile(pattern) for pattern in args.ignore_regex]
    log_text = _load_log_text(args.log_path, args.format)
    warning_lines = _find_warning_lines(log_text, ignore_patterns)

    if warning_lines:
        print(f"Warnings found in {args.log_path}:", file=sys.stderr)
        for line in warning_lines:
            print(line, file=sys.stderr)
        sys.exit(1)

    print(f"No warnings found in {args.log_path}")


if __name__ == "__main__":
    run_from_cli()
