"""Validate build logs for warnings that should fail strict builds."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

WARNING_LINE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"^\s*(?:LaTeX|Package|Class)\b.*Warning:"),
    # \vbox too: a vertically overfull page loses content past the margin just
    # as an \hbox loses it past the edge, and only \hbox was caught before.
    re.compile(r"^\s*(?:Under|Over)full \\[hv]box"),
    # Pandoc's own warnings (missing resource, duplicate identifier, ...) as
    # they appear in teed stdout/stderr text logs.
    re.compile(r"^\[WARNING\]"),
    # A glyph the font cannot render is dropped silently from the PDF, so it is
    # a defect, not a nicety. LuaTeX reports it without the word "Warning", and
    # Pandoc prefixes its own copy with [WARNING] -- neither matched the
    # patterns above, which is how 81 missing λ/∑ once passed a "strict" build.
    re.compile(r"Missing character: There is no "),
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
        help="Regex for warning lines that should be dropped entirely",
    )
    parser.add_argument(
        "--advisory-regex",
        action="append",
        default=[],
        help=(
            "Regex for warning lines to report without failing. For diagnostics "
            "that cost quality but lose nothing, unlike an overfull box."
        ),
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
    # Pandoc's own WARNING entries are separate from the embedded LaTeX log and
    # were previously only inspected as a fallback when no LaTeX output existed
    # -- so for any build that reached LaTeX, pandoc-level warnings passed the
    # strict gate unseen. Collect them unconditionally.
    #
    # The `[WARNING]` prefix is added here because pandoc's own `pretty` string
    # carries no marker of its own, and that prefix is what WARNING_LINE_PATTERNS
    # matches. It used to be added on the LaTeX path only, so a target that never
    # reaches LaTeX read its pandoc warnings back as ordinary prose and no pattern
    # matched them -- pptx is such a target, and it is strict-gated, so
    # `STRICT_WARNINGS=1 ./scripts/build_in_container.sh pptx` could not fail on a
    # missing resource or a duplicate identifier. Both paths mark them now.
    warnings: list[str] = []
    other: list[str] = []
    for entry in payload:
        if not isinstance(entry, dict):
            continue
        pretty = entry.get("pretty")
        if isinstance(pretty, str):
            if entry.get("verbosity") == "WARNING":
                warnings.append(f"[WARNING] {pretty}")
            else:
                other.append(pretty)
        contents = entry.get("contents")
        if entry.get("description") == "LaTeX output" and isinstance(contents, str):
            latex_outputs.append(contents)

    if latex_outputs:
        # Only the last LaTeX log matters -- earlier passes legitimately warn
        # about undefined references that the final pass resolves. The remaining
        # entries are pandoc's INFO chatter, which holds no diagnostic the LaTeX
        # log does not.
        return "\n".join([*warnings, latex_outputs[-1]])

    return "\n".join([*warnings, *other])


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


def _split_advisories(
    warning_lines: list[str], advisory_patterns: list[re.Pattern[str]]
) -> tuple[list[str], list[str]]:
    """Split *warning_lines* into (fatal, advisory).

    Advisories are still printed -- the point is to stop a diagnostic that costs
    only quality from failing the build, not to stop anyone seeing it. An
    ``--ignore-regex`` line is dropped before it ever gets here.
    """
    fatal: list[str] = []
    advisory: list[str] = []
    for line in warning_lines:
        target = advisory if any(p.search(line) for p in advisory_patterns) else fatal
        target.append(line)
    return fatal, advisory


def run_from_cli() -> None:
    """Validate the selected log file and exit non-zero on warnings."""
    args = _parse_args()
    if not args.log_path.is_file():
        print(f"Error: log file does not exist: {args.log_path}", file=sys.stderr)
        sys.exit(1)

    ignore_patterns = [re.compile(pattern) for pattern in args.ignore_regex]
    advisory_patterns = [re.compile(pattern) for pattern in args.advisory_regex]
    log_text = _load_log_text(args.log_path, args.format)
    warning_lines = _find_warning_lines(log_text, ignore_patterns)
    fatal, advisory = _split_advisories(warning_lines, advisory_patterns)

    if advisory:
        print(f"Advisories in {args.log_path} (not failing the build):", file=sys.stderr)
        for line in advisory:
            print(f"  {line}", file=sys.stderr)

    if fatal:
        print(f"Warnings found in {args.log_path}:", file=sys.stderr)
        for line in fatal:
            print(line, file=sys.stderr)
        sys.exit(1)

    counted = f" ({len(advisory)} advisory)" if advisory else ""
    print(f"No warnings found in {args.log_path}{counted}")


if __name__ == "__main__":
    run_from_cli()
