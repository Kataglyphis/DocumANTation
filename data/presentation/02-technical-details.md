# Technical details

## Demo roadmap (3 minutes)

1. Edit a slide in Markdown
2. Build the PDF in Docker
3. Show the final deck + theme

# System overview

- Flutter/Dart app as the UI layer
- Content lives in Markdown (Git)
- PDF output is generated via pandoc + LaTeX

# Pipeline (Markdown $\rightarrow$ PDF)

- Inputs: ordered `data/presentation/*.md`
- Template: awesome-beamer theme
- Engine: `lualatex`
- Citations: BibTeX + `--citeproc`

# Why Docker for the build?

- Same toolchain on Windows/Linux/CI
- Fonts + LaTeX packages are pinned
- Reproducible output for YouTube recordings

# Practical details

- Code blocks: `minted` (needs `-shell-escape`)
- Citations: keep sources in `refs.bib`
- Resource paths: images can live next to the repo

# Trade-offs

- `-shell-escape` is powerful (use only in trusted builds)
- LaTeX builds can be slower than pure HTML
- Template work is “real LaTeX” (but reusable)

# Takeaways

- Markdown keeps content portable
- Flutter keeps UI consistent across targets
- Docker keeps builds reproducible
