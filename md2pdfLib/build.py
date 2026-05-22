"""Single build entry point inside the mounted /md2pdfLib tree."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from md2pdfLib.pandoc_builder import run_from_cli  # noqa: E402
from md2pdfLib.presets import PRESETS  # noqa: E402


def main() -> None:
    """Run the selected document build preset from the command line."""
    if len(sys.argv) < 2:
        print(
            f"Usage: python md2pdfLib/build.py {{{','.join(PRESETS)}}} [output_name]",
            file=sys.stderr,
        )
        sys.exit(1)
    preset_name = sys.argv[1]
    factory = PRESETS.get(preset_name)
    if factory is None:
        print(f"Unknown type: {preset_name}. Choose from: {', '.join(PRESETS)}", file=sys.stderr)
        sys.exit(1)
    sys.argv = [sys.argv[0], *sys.argv[2:]]
    run_from_cli(factory())


if __name__ == "__main__":
    main()
