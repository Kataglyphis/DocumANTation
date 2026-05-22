# Overview

Kataglyphis-mdToPdf converts Markdown content into PDF outputs for books, dissertations, presentations, and CVs.
It combines Pandoc, LuaLaTeX, and containerized tooling so the same build flow can be reused across document types.

## Core Capabilities

- `book` and `diss` use a shared Pandoc-to-LaTeX pipeline with bibliography, glossary, and nomenclature support.
- `beamer` produces presentation PDFs through the custom Beamer template stack.
- `cv` uses a direct LuaLaTeX build from the sources in `data/cv/`.
- Shared scripts keep host and container workflows aligned across local runs and CI.

## Repository Structure

| Path | Purpose |
| --- | --- |
| `data/` | Markdown chapters, per-document LaTeX headers, and generated output in `data/out/` |
| `docs/` | Sphinx documentation site for this repository |
| `md2pdfLib/` | Shared Python build logic, Pandoc presets, LaTeX templates, and shell scripts |
| `scripts/` | Top-level wrappers for containerized builds |
| `ExternalLib/Kataglyphis-ContainerHub/` | Reusable Kataglyphis docs styling and shared container components |

## Important Entry Points

- `scripts/build_in_container.sh` is the shared host-side wrapper for `book`, `diss`, `beamer`, and `cv`.
- `build.py` and `md2pdfLib/build.py` expose the CLI entry point for Pandoc-based document types.
- `md2pdfLib/pandoc_builder.py` is the shared command builder and execution layer for Pandoc runs.
- `md2pdfLib/scripts/compile_with_glossaries.sh` drives the full LuaLaTeX, bibliography, glossary, and nomenclature pipeline for `book` and `diss`.
- `md2pdfLib/check_build_log.py` provides strict warning checks for LaTeX and Pandoc logs.

## Document Types

### `book` and `diss`

Markdown chapters are rendered through Pandoc into LaTeX, then compiled with the full TeX pipeline.

### `beamer`

Pandoc generates the presentation PDF through the custom Beamer template and theme setup.

### `cv`

LuaLaTeX builds the curriculum vitae directly from the files stored in `data/cv/`.

## Where to Continue

- Setup and first builds: [Getting Started](getting-started.md)
- Full compilation stages: [Build Pipeline](build-pipeline.md)
- Dependencies and project metadata: [Project Information](project-info.md)
