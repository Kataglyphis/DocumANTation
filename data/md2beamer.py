import os
import subprocess

input_dir = "presentationMd"
output_dir = "presentationPdf"

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
    "--resource-path=.",
    # "--metadata-file",
    # "metadata_beamer.yml",
    "-t",
    "beamer",
    "--verbose",
    # "--pdf-engine",
    # "lualatex",
    # "--include-in-header",
    # "latex_template/main.tex",
    # "-V",
    # "linkcolor:blue",
    # "-V",
    # "mainfont=DejaVu Serif",
    # "-V", "monofont=SauceCodePro Nerd Font",
    "-o",
    os.path.join(output_dir, "beamer_output.pdf"),
]

# Run the pandoc command
subprocess.run(pandoc_cmd)
