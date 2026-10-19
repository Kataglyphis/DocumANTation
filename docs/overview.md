# Overview

DocumANTation converts Markdown content into PDF outputs for books, presentations, and CVs.
It combines Pandoc, LuaLaTeX, and containerized tooling so the same build flow can be reused across document types.

## Key Features

| Feature | Detail |
|---------|--------|
| **Six targets, one toolchain** | Book (scrbook), Beamer slides, PowerPoint deck, bilingual CV (and cover letters in its class), showcase deck, starter doc — one container, one command each |
| **Slides and deck from one source** | `data/presentation/` renders to both Beamer and pptx, so the two cannot disagree |
| **Brand-consistent code blocks** | `brand.json` → Pandoc + Pygments + LaTeX + CSS — same dark palette everywhere |
| **Containerized builds** | One Dockerfile, pinned Pandoc (SHA256-verified) and uv, zero host dependencies beyond a container runtime |
| **Strict build gates** | `STRICT_WARNINGS=1` turns Pandoc/LaTeX warnings into build failures — locally, since CI compiles no LaTeX |
| **Generated style pipeline** | `generate_style.py` fans `brand.json` into 15 consumer files; `--check` prevents drift |
| **Identity is a token too** | Author, URL, GitHub handle and institute are generated into LaTeX, Pandoc metadata and Sphinx — never retyped |
| **Reusable Sphinx theme** | `sphinx-kataglyphis-theme` — pip-installable package with brand tokens and Pygments styles |

The slide deck and the PowerPoint deck are the same Markdown rendered twice, so
they cannot drift from each other. The book, the CV and the starter document have
sources of their own; what they share is the brand and the toolchain, not the
prose.

## Why not just Pandoc?

| | Pandoc + template | Eisvogel | Typst | DocumANTation |
|---|---|---|---|---|
| Six targets, one brand + toolchain | Manual | No | No | Book + Beamer + PPTX + CV + showcase + starter |
| Author/URL/handle as generated tokens | No | No | No | `identity` in `brand.json` → LaTeX, Pandoc, Sphinx |
| Brand-consistent code highlighting | Manual | No | Partial | `brand.json` → all formats |
| Containerized reproducible build | Manual | No | No | One Dockerfile, pinned Pandoc + uv |
| Strict build-log warning gates | No | No | No | `STRICT_WARNINGS=1` |
| Bilingual CV from one source | No | No | No | `CV_LANG=english\|german` |
| Sphinx theme with same brand | No | No | No | `sphinx-kataglyphis-theme` |

## Repository Structure

| Path | Purpose |
| --- | --- |
| `data/` | Markdown chapters, per-document LaTeX headers, and generated output in `data/out/` |
| `docs/` | Sphinx documentation site for this repository |
| `md2pdfLib/` | Shared Python build logic, Pandoc presets, LaTeX templates, and shell scripts |
| `scripts/` | Top-level wrappers for containerized builds |
| `sphinx-kataglyphis-theme/` | Reusable Sphinx theme package (`sphinx_kataglyphis`) shared across Kataglyphis docs sites |
| `docs-tooling/` | Shared Sphinx templates consumed by downstream repos as a submodule (its doc-generation scripts moved to ANTfrastructure on 2026-07-15) |

## Important Entry Points

- `scripts/build_in_container.sh` is the shared host-side wrapper for `book`, `beamer`, `demo`, `example`, `pptx`, `cv` and `letter`.
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
selects English (default) or German from the same sources, and `CV_PROFILE`
which sections and summary a tailored application CV shows (`data/cv/profiles/`).

### `letter`

A cover letter: the `cv` document with a letter from `data/cv/letters/` as its
body, typeset with the CV profile of the same name, so it shares the CV's class,
header and footer.

## Shared Sphinx Baseline

New projects brand their docs with `sphinx_kataglyphis.setup_theme()`, but AccelerANTgine and
BeschleunigerBallett still load `docs-tooling/source_templates/sphinx-book/conf_base.py` by file
path. Its five constants (`SPHINX_EXTENSIONS`, `HTML_THEME`, `HTML_THEME_OPTIONS`,
`HTML_STATIC_PATH`, `HTML_CSS_FILES`) are therefore a public contract, pinned by
`tests/test_theme.py`. The file may import only the standard library, because neither consumer
installs the theme package, and its colours arrive only through the generated `custom.css`.

## Where to Continue

- Setup and first builds: [Getting Started](getting-started.md)
- Full compilation stages: [Build Pipeline](build-pipeline.md)
- Dependencies and project metadata: [Project Information](project-info.md)
