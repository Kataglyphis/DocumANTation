# AGENTS.md — Kataglyphis-DocumANTation

Guidance for AI agents and contributors working on this project.
Follow these rules unless the user explicitly overrides them.

---

## Project Overview

This project converts Markdown files into PDFs (books, presentations)
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
# Build the image (once)
nerdctl build . -t pandoc_all

# Build a document -- the normal path
./scripts/build_in_container.sh {book|beamer|pptx|cv}

# The same targets via Makefile, plus the CV variants
make {book|beamer|pptx|cv}
make cv CV_LANG=german
make cv-all

# Any target, with the strict warning gates
STRICT_WARNINGS=1 ./scripts/build_in_container.sh book
```

To debug a single stage, drive the container yourself. The mounts and the empty
entrypoint never change — only the command after `activate &&` does:

```bash
nerdctl run --rm --entrypoint "" -v "$(pwd)/md2pdfLib:/md2pdfLib" -v "$(pwd)/data:/data" \
  pandoc_all sh -c '. md2pdf/bin/activate && <command>'
```

| `<command>` | Builds |
| --- | --- |
| `uv run python md2pdfLib/build.py {book\|beamer\|pptx}` | the Pandoc targets, no glossaries |
| `./md2pdfLib/scripts/compile_with_glossaries.sh --type book` | the book, full TeX pipeline |

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

[`pyproject.toml`](pyproject.toml) is authoritative — read it rather than a
copy here, which is one edit away from being wrong. What it sets today: ruff at
`line-length = 100`, `target-version = "py310"`, lint rules
`["E", "F", "I", "N", "W", "UP", "B", "C4", "SIM"]`, double quotes, spaces, LF
endings; `ty` for type checks; `pytest` + `pytest-cov` under the `dev` extra.

Code must stay 3.10-compatible (`requires-python = ">=3.10"`) — e.g.
`int.from_bytes(...)` needs an explicit `byteorder` before 3.11.

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

Use the `build.py` CLI rather than adding document-specific wrapper scripts:
`uv run python build.py {book|beamer|pptx}` on the host, or
`uv run python md2pdfLib/build.py {book|beamer|pptx}` inside the container,
where only `/md2pdfLib` is mounted.

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
It takes a `--type` flag only — a former generic positional mode had no callers
and was removed, so the valid invocations stay enumerable:

```bash
./md2pdfLib/scripts/compile_with_glossaries.sh --type book
```

---

## LaTeX Conventions

### File Organization

```
md2pdfLib/
├── style/                   ← generated from style/brand.json — do not edit
│   ├── brand-colors.tex     ← brandAccent, brandLink, linkcolor, basecolor, …
│   └── brand-fonts.tex      ← \brandSetMainFont, \brandSetMonoFont
├── themes/                  ← generated code-highlighting palettes
│   └── pygments.theme       ← dark, used by all documents (book, slides, pptx)
├── book/template/latex/     ← canonical book templates
│   ├── bookclass.cls        ← KOMA-Script scrbook based document class (+ \maketitle)
│   ├── glossary_entries.tex
│   ├── nomenclature.tex
│   ├── c_code_style.tex
│   └── logos/
├── presentation/template/latex/
│   ├── awesome-beamer/      ← git submodule
│   └── smile/               ← git submodule
```

Colours and fonts are never written in a document — they come from
`style/brand.json`. See [`style/README.md`](style/README.md).
The per-document headers that Pandoc injects live in `data/<doc>/latex/main.tex`.

### Hardcoded Values

- In LaTeX header files, use `\providecommand` (not `\newcommand`) so values can be
  overridden from Pandoc metadata or preamble injections
- All `\url{}`, `\email{}`, `\github{}` references must use consistent values.
  The canonical URL is `www.jonasheinle.de` and GitHub handle is `Kataglyphis`

### TeX Engine

- Always use **LuaLaTeX** (not pdfLaTeX or XeLaTeX)
- `lualatex -output-directory=data/out data/out/file.tex` — output-directory is
  required for clean build separation

### Pandoc Metadata

- `md2pdfLib/pandoc/base.yml` is the metadata source for `book`
- Document-type `pandoc/metadata.yml` files are used when a preset needs extra metadata
  (for example `presentation`)
- `documentclass:` paths are relative to the project root
- Syntax highlighting themes are configured in `md2pdfLib/presets.py` via Pandoc's
  `--syntax-highlighting` option
- **Do not** duplicate values between metadata files and preset args unless Pandoc
  requires a dedicated CLI option

---

## Adding a New Document Type

1. Create input markdown directory under `data/<type>/chapters/`
2. Create LaTeX header at `data/<type>/latex/main.tex` (or reuse existing)
3. Create metadata at `md2pdfLib/<type>/pandoc/metadata.yml`, or extend
   `md2pdfLib/pandoc/base.yml` when the new type intentionally shares the `book`
   base
4. Add a factory function in `md2pdfLib/presets.py`, set `highlight_style` there if
   needed, and register it in `PRESETS`
5. Add the type to the `Makefile` targets
6. Optionally add a `--type` mapping entry in `md2pdfLib/scripts/compile_with_glossaries.sh`

---

## What NOT to Do

- **Do not** duplicate LaTeX templates — use `md2pdfLib/book/template/latex/` as the
  shared location for book templates
- **Do not** add comments to code unless the logic is truly non-obvious
- **Do not** use `docker` for **local** commands — use **nerdctl** locally
  (BuildKit / rootless). Scripts accept `CONTAINER_RUNTIME=docker` for
  environments without nerdctl; both run the same image.
- **Do not** add a workflow that builds the `Dockerfile` in CI — the image is
  built locally (`nerdctl build . -t pandoc_all`). The only GitHub workflow is
  `docs-pages.yml`, which publishes the Sphinx docs to GitHub Pages.
- **Do not** commit `data/out/` (it is in `.gitignore`)
- **Do not** run `nerdctl build` without ensuring buildkitd is running
  (`systemctl --user status buildkit.service`)
- **Do not** use `subprocess.run()` without `check=True`
- **Do not** write shell scripts without `set -euo pipefail`
- **Do not** use `\newcommand` for values that can come from metadata — use
  `\providecommand` to allow override
- **Do not** forget `--entrypoint ""` when running `nerdctl run` with the
  `pandoc_all` image
- **Do not** replace `texlive-full` in the Dockerfile with individual texlive
  collections — the full scheme is deliberate: documents are free to pull in
  any LaTeX package, and a missing collection fails builds much later and
  less obviously than the one-time image-size cost

---

## Version Pins

The `Dockerfile` and `uv.lock` are authoritative; this table is a snapshot.
Pandoc and uv pins are synced from ContainerHub's
`linux/scripts/01-core/versions.env` via its `docs/scripts/sync_versions.py`
— bump them there, never by editing the Dockerfile directly.

| Component | Version | Source |
|-----------|---------|--------|
| Ubuntu | 26.04 | `FROM ubuntu:26.04` in Dockerfile |
| Pandoc | 3.10 | `ARG PANDOC_VERSION` in Dockerfile, SHA256-verified .deb (synced from ContainerHub) |
| TeX Live | 2025 | Ubuntu 26.04 repos (`texlive-full`, deliberate) |
| uv | 0.11.25 | `ARG UV_VERSION` in Dockerfile, pinned installer (synced from ContainerHub) |
| Pygments | >=2.17, pinned in `uv.lock` | `pyproject.toml` runtime dependency |
| Python | 3.14 | `python3-full` from Ubuntu 26.04 repos |
