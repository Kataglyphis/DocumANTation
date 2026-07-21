"""Shared pandoc build utilities for all document types (book, diss, presentation)."""

from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class BuildError(Exception):
    """Raised when a build step fails."""


_FILENAME_RE = re.compile(r"[A-Za-z0-9._-]+")


def safe_output_name(raw_name: str, default_suffix: str = ".tex") -> str:
    """Return a safe output filename.

    - strips path components (preventing path traversal)
    - only allows letters, numbers, dot, underscore, hyphen
    - appends *default_suffix* if the name doesn't already end with it
    """
    name = Path(raw_name or "").name
    if not _FILENAME_RE.fullmatch(name):
        raise BuildError(
            "Invalid output filename. Use only letters, numbers, dot, underscore and hyphen."
        )
    # default_suffix is included so a format whose extension is not in the fixed
    # list still round-trips: "deck.pptx" must not become "deck.pptx.pptx".
    for suffix in {".tex", ".pdf", ".log", default_suffix}:
        if name.endswith(suffix):
            return name
    return name + default_suffix


def resolve_project_path(path_value: str) -> Path:
    """Return *path_value* resolved against the project root when relative."""
    path = Path(path_value)
    return path if path.is_absolute() else PROJECT_ROOT / path


def _markdown_sort_key(path: Path) -> tuple[int, str]:
    prefix = path.stem.split("-", 1)[0]
    if not prefix.isdigit():
        raise BuildError(
            f"Markdown files must start with a numeric prefix like '01-'. Invalid file: {path.name}"
        )
    # Name as tiebreaker: two files sharing a prefix otherwise fall back to
    # iterdir()'s filesystem order, which differs between machines -- the same
    # sources could produce differently-ordered documents.
    return (int(prefix), path.name)


def get_sorted_markdown_files(input_dir: str | Path) -> list[str]:
    """Return *.md files from *input_dir* sorted by numeric prefix.

    Files are expected to follow the pattern ``NN-description.md``.
    The numeric prefix is parsed from the first segment before ``-``.
    """
    path = Path(input_dir)
    if not path.is_dir():
        raise BuildError(f"Input directory does not exist: {input_dir}")

    md_files = [
        file_path
        for file_path in path.iterdir()
        if file_path.is_file() and file_path.suffix == ".md"
    ]
    if not md_files:
        raise BuildError(f"No .md files found in {input_dir}")

    return [str(file_path) for file_path in sorted(md_files, key=_markdown_sort_key)]


@dataclass
class BuildConfig:
    """Configuration for a pandoc build pipeline."""

    input_dir: str
    metadata_file: str
    output_dir: str = "./data/out"
    output_name: str | None = None
    default_output_name: str = "output.tex"
    pdf_engine: str = "lualatex"
    highlight_style: str = ""
    include_in_header: str = ""
    log_file: str = ""
    bibliography: str = ""
    document_class: str = ""
    resource_path: str = "."
    top_level_division: str = ""
    number_sections: bool = False
    number_offset: int = 0
    biblatex: bool = False
    citeproc: bool = False
    toc: bool = False
    extra_args: list[str] = field(default_factory=list)
    extra_metadata_files: list[str] = field(default_factory=list)
    output_suffix: str = ".tex"


# Mapping from BuildConfig field name to pandoc CLI flag.
_STR_FLAGS: dict[str, str] = {
    "highlight_style": "--syntax-highlighting",
    "include_in_header": "--include-in-header",
    "bibliography": "--bibliography",
    "document_class": "--documentclass",
    "top_level_division": "--top-level-division",
}

_BOOL_FLAGS: dict[str, str] = {
    "toc": "--toc",
    "biblatex": "--biblatex",
    "citeproc": "--citeproc",
}


def build_pandoc_cmd(config: BuildConfig, input_files: list[str], output_path: str) -> list[str]:
    """Assemble the pandoc command-line from a BuildConfig."""
    cmd: list[str] = [
        "pandoc",
        *input_files,
        "--resource-path",
        config.resource_path,
        "--pdf-engine",
        config.pdf_engine,
        "--metadata-file",
        config.metadata_file,
    ]

    if config.log_file:
        cmd += ["--log", config.log_file]

    for field_name, flag in _STR_FLAGS.items():
        val = getattr(config, field_name)
        if val:
            cmd += [flag, val]

    for f in config.extra_metadata_files:
        cmd += ["--metadata-file", f]

    for field_name, flag in _BOOL_FLAGS.items():
        if getattr(config, field_name):
            cmd += [flag]

    if config.number_sections:
        cmd += ["--number-sections"]
        if config.number_offset:
            cmd += ["--number-offset", str(config.number_offset)]

    cmd += ["--verbose"]
    cmd += config.extra_args
    cmd += ["-o", output_path]

    return cmd


def run_pandoc(config: BuildConfig) -> None:
    """Execute the full pandoc build pipeline.

    1. Resolve the output name
    2. Create the output directory
    3. Discover and sort input markdown files
    4. Build the pandoc command
    5. Run pandoc (raises :class:`BuildError` on failure)
    """
    output_name = safe_output_name(
        config.output_name or config.default_output_name,
        default_suffix=config.output_suffix,
    )

    output_dir = resolve_project_path(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / output_name

    if config.log_file:
        resolve_project_path(config.log_file).parent.mkdir(parents=True, exist_ok=True)

    input_files = get_sorted_markdown_files(resolve_project_path(config.input_dir))
    cmd = build_pandoc_cmd(config, input_files, str(output_path))

    try:
        subprocess.run(cmd, check=True, cwd=PROJECT_ROOT)
    except subprocess.CalledProcessError as exc:
        raise BuildError(f"Pandoc failed with exit code {exc.returncode}") from exc


def run_from_cli(config: BuildConfig) -> None:
    """Entry point suitable for ``if __name__ == '__main__'`` scripts.

    Accepts the optional output name from ``sys.argv[1]``, traps
    :class:`BuildError` and prints a user-friendly message before exiting
    with a non-zero code.
    """
    try:
        if len(sys.argv) > 1:
            config.output_name = sys.argv[1]
        run_pandoc(config)
    except BuildError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
