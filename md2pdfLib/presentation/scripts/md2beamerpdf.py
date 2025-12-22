import os
import subprocess

input_dir = "data/presentation"
output_dir = "data/out"
presentation_name = "beamer_output.pdf"

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
    "--log=data/out/beamer.json",
    "--resource-path=.",
    "--columns=10",
    "--slide-level=2",
    "--metadata-file",
    "md2pdfLib/presentation/pandoc/metadata.yml",
    "-t",
    "beamer",
    "--template",
    "md2pdfLib/presentation/pandoc/awesome-beamer-template.tex",
    "--verbose",
    "--bibliography",
    "data/presentation/latex/refs.bib",
    "--citeproc",
    "--pdf-engine",
    "lualatex",
    "--pdf-engine-opt=-shell-escape",
    "--highlight-style=md2pdfLib/pygments.theme",
    "--include-in-header",
    "data/presentation/latex/main.tex",
    "-V",
    "linkcolor:blue",
    "-V",
    "themeoptions:english",
    # "-V",
    # "themeoptions:secslide",
    # "-V",
    # "themeoptions:subsecslide",
    # "-V",
    # "themeoptions:color",
    # "-V",
    # "themeoptions:listings",
    # "-V",
    # "themeoptions:footnote",
    "-V",
    "titlegraphic:data/presentation/images/The World's First AI.jpg",
    "-V",
    "themeoptions:coloraccent=myGreenAccent",
    "-V",
    "mainfont=Roboto",
    "-o",
    os.path.join(output_dir, presentation_name),
]

# Run the pandoc command
subprocess.run(pandoc_cmd)
