# Introduction

This is a minimal example document built with **Kataglyphis-DocumANTation**.
It demonstrates the pipeline: write Markdown, get a branded PDF.

## What you are looking at

This document was generated from a single Markdown file using Pandoc and
LuaLaTeX inside a container. The code blocks, colours and fonts come from
`style/brand.json` — change one value and every output rebrands.

## Code example

```python
def greet(name: str) -> str:
    """Return a greeting."""
    return f"Hello, {name}!"

if __name__ == "__main__":
    print(greet("world"))
```

## Math

The quadratic formula:

$$x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}$$

## Table

| Format | Command | Output |
|--------|---------|--------|
| Book | `make book` | A4 PDF |
| Slides | `make beamer` | 16:9 PDF |
| Deck | `make pptx` | .pptx |
| CV | `make cv` | A4 PDF |
