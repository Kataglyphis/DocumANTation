# Gallery

All four output formats are built from the same Markdown sources. The brand
(colours, fonts, code-block styling) flows from a single `brand.json` into every
output — change one value and rebuild, and all four update simultaneously.

## Book (A4, KOMA-Script scrbook)

A print-ready textbook with dark code blocks, syntax highlighting, glossary,
nomenclature, and bibliography. Built with Pandoc + LuaLaTeX through the full
TeX pipeline (biber, makeglossaries, makeindex).

```{image} _static/gallery/book-page.png
:alt: Book page showing dark code block with syntax highlighting
:width: 600px
:align: center
```

## Beamer Slides

A 16:9 presentation deck with the same dark code-block look, tcolorbox
environments for definitions and examples, and sidebar navigation.

```{image} _static/gallery/beamer-slide.png
:alt: Beamer title slide with brand styling
:width: 600px
:align: center
```

## PowerPoint Deck

The same Markdown that builds the Beamer PDF also produces a PowerPoint deck
via Pandoc + a branded reference template generated from `brand.json` at build
time. Code blocks are boxed with the same brand palette.

## CV

A professional curriculum vitae built directly with LuaLaTeX (not Pandoc). The
same source files produce both English and German variants via a class option —
`CV_LANG=english` or `CV_LANG=german` — without editing any `.tex` file.

```{image} _static/gallery/cv-page.png
:alt: CV page with brand accent color
:width: 600px
:align: center
```

## Sphinx Website

This documentation site uses the same brand via the `sphinx-kataglyphis-theme`
package. Code blocks share the identical dark palette as the PDF outputs.

## The brand pipeline

```{code-block} text
style/brand.json
    │
    ├─► brand-colors.tex     → book, beamer, CV
    ├─► brand-fonts.tex      → book, beamer, CV
    ├─► pygments.theme       → Pandoc code highlighting (all PDFs)
    ├─► highlight.py         → Sphinx website Pygments styles
    ├─► custom.css           → Sphinx website theme
    ├─► brand.css            → standalone web tokens
    └─► brand.tokens.json    → PPTX reference deck builder
```

One JSON file. Every output. Zero drift.
