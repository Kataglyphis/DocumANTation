import os
import subprocess
import sys

input_dir = "./data/diss/chapters"
output_dir = "./data/out"

# Standardwert für den Ausgabedateinamen
default_output_name = "output.pdf"
output_name = sys.argv[1] if len(sys.argv) > 1 else default_output_name

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
    "--log=data/out/diss.json",
    "--verbose",
    "--pdf-engine=lualatex",
    # "--toc",
    # "--number-offset=2",
    "--number-sections",
    # "--top-level-division=chapter",
    "--resource-path=.",
    "--metadata-file",
    "md2pdfLib/diss/pandoc/metadata.yml",
    "--highlight-style=md2pdfLib/pygments.theme",
    "--include-in-header",
    "data/diss/latex/Diss_Main.tex",
    # "--include-in-header",
    # "main.tex",
    "-o",
    os.path.join(output_dir, output_name),
]

# Run the pandoc command
subprocess.run(pandoc_cmd)
