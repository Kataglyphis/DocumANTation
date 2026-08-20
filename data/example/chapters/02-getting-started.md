# Getting Started with Your Own Documents

To use this pipeline for your own content:

1. **Clone** this repository
2. **Replace** the content in `data/example/chapters/` with your Markdown
3. **Customize** `style/brand.json` with your colours and fonts
4. **Build**: `make example` — one Pandoc call, straight to
   `data/out/example_output.pdf`

`make example` builds *this* directory. The other targets have sources of their
own: `make book` builds `data/book/`, `make beamer` and `make pptx` build
`data/presentation/`, and `make cv` builds `data/cv/`. Point a new target at
your own directory by adding a preset in `md2pdfLib/presets.py`.

## Rebranding

Edit `style/brand.json` and regenerate:

```json
{
  "colors": {
    "accent": "#6af0ad",
    "accent_strong": "#2ad488"
  }
}
```

Then run:

```bash
uv run python style/generate_style.py --write
make book
```

Every output rebrands: the PDF code blocks, the slide deck, the CV, and the
Sphinx documentation website.
