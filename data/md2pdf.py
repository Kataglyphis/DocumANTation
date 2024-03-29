import os
import subprocess

input_dir = "chapters"
output_dir = "my_book"

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
    "--pdf-engine=lualatex",
    "--number-sections",
    "--resource-path=.",
    "--metadata-file",
    "metadata.yml",
    "--include-in-header",
    "main.tex",
    "-o",
    os.path.join(output_dir, "book_output.pdf"),
]

# Run the pandoc command
subprocess.run(pandoc_cmd)
