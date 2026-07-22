"""Single build entry point inside the mounted /md2pdfLib tree."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from md2pdfLib.pandoc_builder import run_from_cli  # noqa: E402
from md2pdfLib.presets import PRESETS  # noqa: E402


def main() -> None:
    """Run the selected document build preset from the command line."""
    parser = argparse.ArgumentParser(
        prog=Path(__file__).name,
        description="Build a document using Pandoc + LuaLaTeX.",
    )
    parser.add_argument(
        "type",
        choices=sorted(PRESETS.keys()),
        help=f"Document type to build: {', '.join(sorted(PRESETS.keys()))}",
    )
    parser.add_argument(
        "output",
        nargs="?",
        help="Output filename (default: derived from type)",
    )
    args = parser.parse_args()

    factory = PRESETS[args.type]
    sys.argv = [sys.argv[0]] + ([args.output] if args.output else [])
    run_from_cli(factory())


if __name__ == "__main__":
    main()
