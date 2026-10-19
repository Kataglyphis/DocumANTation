# Overview

DocumANTation turns Markdown into books, presentations and CVs with Pandoc and LuaLaTeX, through
one containerized build flow for every document type.

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

The book, the CV and the starter document have sources of their own; they share the brand and the
toolchain, not the prose.

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

| Entry point | Does |
| --- | --- |
| `scripts/build_in_container.sh` | The host-side wrapper for `book`, `beamer`, `demo`, `example`, `pptx`, `cv` and `letter` |
| `build.py`, `md2pdfLib/build.py` | The CLI for the Pandoc-based document types |
| `md2pdfLib/pandoc_builder.py` | Builds and runs every Pandoc command |
| `md2pdfLib/scripts/compile_with_glossaries.sh` | The full LuaLaTeX, bibliography, glossary and nomenclature pipeline for `book` |
| `md2pdfLib/check_build_log.py` | The strict warning checks over LaTeX and Pandoc logs |
| `style/brand.json` | The single source of the visual brand (colours, fonts, code palette) and the identity (author, e-mail, URL, GitHub handle, institute); `style/generate_style.py` fans it into every consumer, and `--check` fails on drift |

## Document Types

### `book`

Pandoc renders the Markdown chapters into LaTeX; the full TeX pipeline compiles it, bibliography,
glossary and nomenclature included.

### `beamer`

Pandoc builds the presentation PDF through the custom Beamer template and theme.

### `pptx`

The same presentation markdown as a PowerPoint deck. Colours and fonts come from a
`--reference-doc` generated from `style/brand.json` at build time, and `verify_brand.py` fails a
deck that leaves the brand.

### `demo`

The slide primitives showcase in `data/presentation/demo/`, built as its own deck through the
same Beamer template. It needs its own target because `get_sorted_markdown_files()` lists a single
level: Markdown in a subdirectory of an input directory never reaches Pandoc.

### `example`

The minimal starter document in `data/example/chapters/`: one Pandoc call straight to PDF, with
no bibliography, glossary or nomenclature, so a first build cannot fail inside the TeX pipeline.
Replace its Markdown to begin a project of your own.

### `cv`

LuaLaTeX builds the curriculum vitae directly from `data/cv/`, with the `myCV_METADATA` class from
`md2pdfLib/cv/template/latex/`. `CV_LANG` selects English (default) or German from the same
sources; `CV_PROFILE` selects which sections and summary a tailored application CV shows
(`data/cv/profiles/`).

### `letter`

A cover letter: the `cv` document with a letter from `data/cv/letters/` as its body, typeset with
the CV profile of the same name, so it shares the CV's class, header and footer.

## Shared Sphinx Baseline

Every family Sphinx site brands its docs with `sphinx_kataglyphis.setup_theme()`. The last two
that loaded `docs-tooling/source_templates/sphinx-book/conf_base.py` by file path, AccelerANTgine
and BeschleunigerBallett, switched on 2026-10-19, so the file and its generated `custom.css` have
no consumer left. `tests/test_theme.py` still pins its five constants to `setup_theme()` until
both files are deleted.

## Where to Continue

- Setup and first builds: [Getting Started](getting-started.md)
- Full compilation stages: [Build Pipeline](build-pipeline.md)
- Dependencies and project metadata: [Project Information](project-info.md)
