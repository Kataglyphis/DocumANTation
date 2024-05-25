import os
import subprocess

input_dir = "./data/book/chapters"
output_dir = "./data/out"
output_name = "book_output.pdf"

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
    "--pdf-engine=latexmk",
    "--number-sections",
    "--resource-path=.",
    "--metadata-file",
    "md2pdfLib/book/pandoc/metadata.yml",
    "--include-in-header",
    "data/book/latex/main.tex",
    # "--include-in-header",
    # "main.tex",
    "-o",
    os.path.join(output_dir, output_name),
]

# Run the pandoc command
subprocess.run(pandoc_cmd)
