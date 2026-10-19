# Gallery

Every output below comes from the same toolchain; the slide deck and the PowerPoint deck from the
same Markdown. The brand (colours, fonts, code-block styling) flows from one `brand.json` into all
of them: change a value, rebuild, and every output follows.

## Book (A4, KOMA-Script scrbook)

A print-ready textbook with dark code blocks, syntax highlighting, glossary, nomenclature and
bibliography, built with Pandoc + LuaLaTeX through the full TeX pipeline (biber, makeglossaries,
makeindex).

```{image} ../images/book-page.png
:alt: Book page showing dark code block with syntax highlighting
:width: 600px
:align: center
```

## Beamer Slides

A 16:9 deck with the same dark code blocks, tcolorbox environments for definitions and examples,
and sidebar navigation.

```{image} ../images/beamer-slide.png
:alt: Beamer title slide with brand styling
:width: 600px
:align: center
```

## PowerPoint Deck

The Beamer PDF's Markdown, rendered by Pandoc against a branded reference template generated from
`brand.json` at build time. Code blocks are boxed in the brand palette.

## CV

Built directly with LuaLaTeX, not Pandoc. The same source files produce the English and the German
variant through a class option — `CV_LANG=english` or `CV_LANG=german` — without editing a `.tex`
file.

```{image} ../images/cv-page.png
:alt: CV page with brand accent color
:width: 600px
:align: center
```

## Sphinx Website

This site takes the same brand from the `sphinx-kataglyphis-theme` package; its code blocks use
the PDFs' dark palette.

## The brand pipeline

```{code-block} text
style/brand.json
    │
    ├─► brand-colors.tex     → book, beamer, CV
    ├─► brand-fonts.tex      → book, beamer, CV
    ├─► brand-identity.tex   → author, URLs, handles (book, beamer, CV)
    ├─► pandoc metadata      → author/institute + fonts and link colours
    ├─► pygments.theme       → Pandoc code highlighting (all PDFs)
    ├─► highlight.py         → Sphinx website Pygments styles
    ├─► custom.css           → Sphinx website theme
    ├─► brand.css            → standalone web tokens
    └─► brand.tokens.json    → PPTX reference deck builder
```
