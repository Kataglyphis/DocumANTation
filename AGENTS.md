# AGENTS.md — Kataglyphis-mdToPdf

Guidance for AI agents and contributors working on this project.
Follow these rules unless the user explicitly overrides them.

---

## Project Overview

This project converts Markdown files into PDFs (books, dissertations, presentations)
via **Pandoc + LuaLaTeX**, orchestrated by Python scripts and driven from within a
Docker/nerdctl container.

```
data/              → user-authored markdown content
md2pdfLib/         → templates, config, scripts, fonts, themes
md2pdfLib/pandoc_builder.py  → shared Pandoc build logic (single source of truth)
md2pdfLib/scripts/            → shared shell scripts
Dockerfile         → container build definition
```

### Related documentation

- [`Dockerfile`](Dockerfile) — the `pandoc_all` image (Ubuntu + TeX Live + Pandoc + the beamer/smile themes)
- [Getting Started](docs/getting-started.md) — clone → build image → build a document, step by step
- [Build Pipeline](docs/build-pipeline.md) — the per-target Pandoc/LuaLaTeX compilation stages
- [Overview](docs/overview.md) — repository structure and shared components

---

## Quick Commands

```bash
# Build the Docker image
nerdctl build . -t pandoc_all

# Build anything via Makefile
make book
make diss
make beamer
make cv

# Or manually inside the container
nerdctl run --rm --entrypoint "" -v "$(pwd)/md2pdfLib:/md2pdfLib" -v "$(pwd)/data:/data" \
  pandoc_all sh -c '. md2pdf/bin/activate && ./md2pdfLib/scripts/compile_with_glossaries.sh --type book'

# Or use the shared helper wrapper
./scripts/build_in_container.sh {book|diss|beamer|cv}

# Build presentation (Python-only, no glossaries)
nerdctl run --rm --entrypoint "" -v "$(pwd)/md2pdfLib:/md2pdfLib" -v "$(pwd)/data:/data" \
  pandoc_all sh -c '. md2pdf/bin/activate && uv run python md2pdfLib/build.py beamer'

# Build book/diss with glossaries (full TeX pipeline)
nerdctl run --rm --entrypoint "" -v "$(pwd)/md2pdfLib:/md2pdfLib" -v "$(pwd)/data:/data" \
  pandoc_all sh -c '. md2pdf/bin/activate && ./md2pdfLib/scripts/compile_with_glossaries.sh --type book'
```

All build types:
```
python build.py {book|diss|beamer}
python md2pdfLib/build.py {book|diss|beamer}
./scripts/build_in_container.sh {book|diss|beamer|cv}
./md2pdfLib/scripts/compile_with_glossaries.sh --type {book|diss}
```

---

## Python Conventions

### Tooling

| Tool | Purpose | Config |
|------|---------|--------|
| **uv** | Package manager, venv, script runner | `uv run python script.py` |
| **ruff** | Linter + formatter | Place `[tool.ruff]` in `pyproject.toml` (see below) |
| **ty** | Type checker | Place `[tool.ty]` in `pyproject.toml` (see below) |

### Code Style

- **Type annotations required** on all functions (Python 3.10+ syntax: `str | None`)
- **No comments** unless the logic is genuinely non-obvious
- Use `pathlib.Path` for all path operations (not `os.path` or string concatenation)
- All `subprocess.run()` calls **must** use `check=True`
- All public-API functions **must** have docstrings (Google style)
- Use the top-level `build.py` entry point instead of per-document wrapper scripts
- `if __name__ == "__main__":` blocks call `run_from_cli()`
- Errors raise `BuildError` (from `md2pdfLib.pandoc_builder`) or `sys.exit(1)` — never silent

### pyproject.toml

```toml
[project]
name = "kataglyphis-md2pdf"
version = "0.1.0"
requires-python = ">=3.10"

[project.optional-dependencies]
dev = ["ruff", "ty"]

[tool.ruff]
line-length = 100
target-version = "py310"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP", "B", "C4", "SIM"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "lf"

```

### Running Tools

```bash
# Inside the container (venv activated):
uv run ruff check md2pdfLib/
uv run ruff format --check md2pdfLib/
uv run ty check md2pdfLib/

# Install dev tools (one-time):
uv pip install ruff ty
```

### Entry Point

Use the CLI entry point instead of document-specific wrapper scripts:

```bash
uv run python build.py book
uv run python build.py diss
uv run python build.py beamer

# Inside the container (only /md2pdfLib is mounted):
uv run python md2pdfLib/build.py book
```

---

## Shell Scripting Conventions

- **Shebang:** `#!/usr/bin/env bash`
- **Safety:** Every script **must** start with `set -euo pipefail`
- **No unparameterized output names** — use `OUTPUT_NAME` variable or CLI args
- **Working directory for TeX tools:** Always run `biber`, `makeglossaries`,
  `makeindex` inside `data/out/` (use a subshell: `(cd data/out && ...)`)
- **No `rm -rf` without `${VAR:?}` guard** to prevent accidental root deletion
- Use `"$(dirname "$0")"` for relative references to sibling scripts

### Shared Compile Script

The canonical compilation script is `md2pdfLib/scripts/compile_with_glossaries.sh`.
It accepts either a `--type` flag or positional arguments:

```bash
./md2pdfLib/scripts/compile_with_glossaries.sh --type book
./md2pdfLib/scripts/compile_with_glossaries.sh --type diss
```

---

## LaTeX Conventions

### File Organization

```
md2pdfLib/
├── book/template/latex/     ← canonical shared templates (used by book + diss)
│   ├── bookclass.cls        ← KOMA-Script scrbook based document class
│   ├── titlepage.tex
│   ├── glossary_entries.tex
│   ├── nomenclature.tex
│   ├── c_code_style.tex
│   └── logos/
├── presentation/template/latex/
│   ├── awesome-beamer/      ← git submodule
│   └── smile/               ← git submodule
```

### Hardcoded Values

- **Canonical Pandoc metadata** lives in `md2pdfLib/pandoc/base.yml` for `book`/`diss`
  and in document-type `pandoc/metadata.yml` files where applicable
- In LaTeX header files, use `\providecommand` (not `\newcommand`) so values can be
  overridden from Pandoc metadata or preamble injections
- All `\url{}`, `\email{}`, `\github{}` references must use consistent values.
  The canonical URL is `www.jonasheinle.de` and GitHub handle is `Kataglyphis`

### TeX Engine

- Always use **LuaLaTeX** (not pdfLaTeX or XeLaTeX)
- `lualatex -output-directory=data/out data/out/file.tex` — output-directory is
  required for clean build separation

### Pandoc Metadata

- `md2pdfLib/pandoc/base.yml` is the shared metadata source for `book` and `diss`
- Document-type `pandoc/metadata.yml` files are used when a preset needs extra metadata
  (for example `presentation`)
- `documentclass:` paths are relative to the project root
- Syntax highlighting themes are configured in `md2pdfLib/presets.py` via Pandoc's
  `--syntax-highlighting` option
- **Do not** duplicate values between metadata files and preset args unless Pandoc
  requires a dedicated CLI option

---

## Build Pipeline

```
Markdown (.md) → pandoc (via pandoc_builder.py) → .tex
     ↓
lualatex (pass 1) → .aux, .bcf, .glo, .nlo
     ↓
biber → bibliography
makeglossaries → glossary
makeindex → nomenclature
     ↓
lualatex (pass 2) → resolve cross-refs → .aux updated
     ↓
lualatex (pass 3) → final PDF
```

All auxiliary tools run inside `data/out/` (subshell cd).

---

## Adding a New Document Type

1. Create input markdown directory under `data/<type>/chapters/`
2. Create LaTeX header at `data/<type>/latex/main.tex` (or reuse existing)
3. Create metadata at `md2pdfLib/<type>/pandoc/metadata.yml`, or extend
   `md2pdfLib/pandoc/base.yml` when the new type intentionally shares the `book`/`diss`
   base
4. Add a factory function in `md2pdfLib/presets.py`, set `highlight_style` there if
   needed, and register it in `PRESETS`
5. Add the type to the `Makefile` targets
6. Optionally add a `--type` mapping entry in `md2pdfLib/scripts/compile_with_glossaries.sh`

---

## What NOT to Do

- **Do not** duplicate LaTeX templates — use `md2pdfLib/book/template/latex/` as the
  shared location for book/diss templates
- **Do not** add comments to code unless the logic is truly non-obvious
- **Do not** use `docker` for **local** commands — use **nerdctl** locally
  (BuildKit / rootless). CI on GitHub-hosted runners uses `docker` (via
  `CONTAINER_RUNTIME=docker`) because nerdctl isn't preinstalled; both build the
  same `Dockerfile`, so keep them equivalent.
- **Do not** commit `data/out/` (it is in `.gitignore`)
- **Do not** run `nerdctl build` without ensuring buildkitd is running
  (`systemctl --user status buildkit.service`)
- **Do not** use `subprocess.run()` without `check=True`
- **Do not** write shell scripts without `set -euo pipefail`
- **Do not** use `\newcommand` for values that can come from metadata — use
  `\providecommand` to allow override
- **Do not** forget `--entrypoint ""` when running `nerdctl run` with the
  `pandoc_all` image
- **Do not** install texlive-full in the Dockerfile — use specific texlive collections

---

## Version Pins

| Component | Version | Source |
|-----------|---------|--------|
| Ubuntu | 26.04 | `FROM ubuntu:26.04` in Dockerfile |
| Pandoc | 3.9.0.2 | Hardcoded in Dockerfile (ARG for future) |
| TeX Live | 2025 | Ubuntu 26.04 repos |
| uv | latest | https://astral.sh/uv/install.sh |
| Pygments | latest | `uv pip install Pygments` |
| Python | 3.14 | `python3-full` from repos |
