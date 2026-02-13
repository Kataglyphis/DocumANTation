import os
import re
import subprocess
import sys
from pathlib import Path

input_dir = "./data/book/chapters"
output_dir = "./data/out"

# Standardwert für den Ausgabedateinamen
default_output_name = "output.tex"


def _safe_output_name(raw_name: str) -> str:
    """Return a safe output filename for data/out.

    - strips any path components
    - disallows shell-like / special characters
    - ensures a .tex suffix
    """
    name = Path(raw_name).name
    if not re.fullmatch(r"[A-Za-z0-9._-]+", name or ""):
        raise ValueError(
            "Invalid output filename. Use only letters, numbers, dot, underscore and hyphen."
        )
    if not name.endswith(".tex"):
        name += ".tex"
    return name


output_name = (
    _safe_output_name(sys.argv[1]) if len(sys.argv) > 1 else default_output_name
)

# Ensure the output directory exists
os.makedirs(output_dir, exist_ok=True)

# List all files in the input directory and sort them numerically based on the prefix
input_files = sorted(
    [
        os.path.join(input_dir, file)
        for file in os.listdir(input_dir)
        if os.path.isfile(os.path.join(input_dir, file))
    ],
    key=lambda x: int(os.path.splitext(os.path.basename(x).split("-")[0])[0]),
)

# # Build the pandoc command
pandoc_cmd = [
    "pandoc",
    *input_files,
    "--log=data/out/book.json",
    "--verbose",
    "--pdf-engine=lualatex",
    "--biblatex",
    "--toc",
    "--number-offset=2",
    "--number-sections",
    "--top-level-division=chapter",
    "--resource-path=.",
    "--metadata-file",
    "md2pdfLib/book/pandoc/metadata.yml",
    "--highlight-style=md2pdfLib/pygments-print.theme",
    "--include-in-header",
    "data/book/latex/main.tex",
    # "--include-in-header",
    # "main.tex",
    "-o",
    os.path.join(output_dir, output_name),
]

# Run the pandoc command (argv list; no shell; output filename sanitized)
subprocess.run(pandoc_cmd, check=True)  # nosemgrep
