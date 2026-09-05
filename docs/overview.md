# Overview

DocumANTation converts Markdown content into PDF outputs for books, presentations, and CVs.
It combines Pandoc, LuaLaTeX, and containerized tooling so the same build flow can be reused across document types.

## Repository Structure

| Path | Purpose |
| --- | --- |
| `data/` | Markdown chapters, per-document LaTeX headers, and generated output in `data/out/` |
| `docs/` | Sphinx documentation site for this repository |
| `md2pdfLib/` | Shared Python build logic, Pandoc presets, LaTeX templates, and shell scripts |
| `scripts/` | Top-level wrappers for containerized builds |
| `sphinx-kataglyphis-theme/` | Reusable Sphinx theme package (`sphinx_kataglyphis`) shared across Kataglyphis docs sites |
| `docs-tooling/` | Shared Sphinx templates and doc-generation scripts consumed by downstream repos as a submodule |

## Important Entry Points

- `scripts/build_in_container.sh` is the shared host-side wrapper for `book`, `beamer`, `demo`, `example`, `pptx`, and `cv`.
- `build.py` and `md2pdfLib/build.py` expose the CLI entry point for Pandoc-based document types.
- `md2pdfLib/pandoc_builder.py` is the shared command builder and execution layer for Pandoc runs.
- `md2pdfLib/scripts/compile_with_glossaries.sh` drives the full LuaLaTeX, bibliography, glossary, and nomenclature pipeline for `book`.
- `md2pdfLib/check_build_log.py` provides strict warning checks for LaTeX and Pandoc logs.
- `style/brand.json` is the single source for both the visual brand (colours, fonts,
  code palette) and the identity (author, e-mail, URL, GitHub handle, institute);
  `style/generate_style.py` fans it into every consumer and `--check` fails on drift.

## Document Types

### `book`

Markdown chapters are rendered through Pandoc into LaTeX, then compiled with the
full TeX pipeline — bibliography, glossary and nomenclature included.

### `beamer`

Pandoc generates the presentation PDF through the custom Beamer template and theme setup.

### `pptx`

The same presentation markdown rendered as a PowerPoint deck. Colours and fonts
come from a `--reference-doc` generated from `style/brand.json` at build time,
and `verify_brand.py` gates the emitted deck on staying on-brand.

### `demo`

The slide primitives showcase in `data/presentation/demo/`, built as its own
deck through the same Beamer template. It needs a target of its own because
`get_sorted_markdown_files()` lists a single level, so Markdown in a
subdirectory of an input directory is never handed to Pandoc.

### `example`

The minimal starter document in `data/example/chapters/`: one Pandoc call
straight to PDF, deliberately with no bibliography, glossary or nomenclature so
that a first build cannot fail inside the TeX pipeline. Replace its Markdown to
begin a project of your own.

### `cv`

LuaLaTeX builds the curriculum vitae directly from the content in `data/cv/`,
using the `myCV_METADATA` class from `md2pdfLib/cv/template/latex/`. `CV_LANG`
selects English (default) or German from the same sources.

## Where to Continue

- Setup and first builds: [Getting Started](getting-started.md)
- Full compilation stages: [Build Pipeline](build-pipeline.md)
- Dependencies and project metadata: [Project Information](project-info.md)
