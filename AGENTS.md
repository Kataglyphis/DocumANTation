# AGENTS.md — DocumANTation

Rules for agents and contributors. An explicit instruction from the user overrides them.

---

## Project Overview

Converts Markdown into PDFs (books, presentations) with **Pandoc + LuaLaTeX**, driven by Python
scripts inside a Docker/nerdctl container.

```
data/              → user-authored markdown content
md2pdfLib/         → templates, config, scripts, fonts, themes
md2pdfLib/pandoc_builder.py  → shared Pandoc build logic (single source of truth)
md2pdfLib/scripts/            → shared shell scripts
md2pdfLib/presentation/pptx/  → OOXML post-processing for the PowerPoint target
md2pdfLib/presentation/pptx/pptx_common.py → shared OOXML layer for that package
Dockerfile         → container build definition
images/logos/      → every family repository's logo, drawn by scripts/make_repo_logos.py
```

### The pptx package

Every module there rewrites a .pptx archive. Use the shared mechanics in `pptx_common.py`; never
write the loop again:

| Need | Use |
| --- | --- |
| Change some slides and write the deck back | `edit_slides(deck, transform)` |
| A slide's layout / master / layout name | the `DeckParts` passed to the transform |
| Name the archive parts | `SLIDE_RE`, `MASTER_RE`, `THEME_RE`, `LAYOUT_RE`, `LAYOUT_RELS_RE` |
| Pin unsized runs to a font size | `sized_runs(fragment, size)` |
| Add shapes to a slide or layout | `append_shapes(xml, shapes)` -- literal, never `re.sub` |
| Read the brand | `brand_tokens()` (md2pdfLib/style/, the only copy the container mounts) |
| A `<deck.pptx>` entry point | `run_cli(action, errors=(...))` |

The build script runs these modules **by path**
(`uv run python /md2pdfLib/presentation/pptx/finalize_deck.py <deck>`), so each one bootstraps
`sys.path` with the md2pdf root and imports its siblings as `md2pdfLib.presentation.pptx.*`.
**Never reintroduce a bare `import pptx_common` fallback**: it loaded a second copy of every
module under a top-level name, so a test and the build could hold two module objects with two
sets of constants, and `ty` cannot resolve it.

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
./scripts/build_in_container.sh {book|beamer|demo|example|pptx|cv|letter}

# The same targets via Makefile, plus the CV variants. `letter` typesets
# data/cv/letters/<CV_PROFILE>.tex, so it needs a CV_PROFILE that has one.
make {book|beamer|demo|example|pptx|cv|letter}
make cv CV_LANG=german
make cv CV_PROFILE=<data/cv/profiles/*>
make cv-all

# Any target, with the strict warning gates
STRICT_WARNINGS=1 ./scripts/build_in_container.sh book
```

### What the strict gate fails on

`md2pdfLib/check_build_log.py` fails the build on LaTeX/Package/Class warnings, overfull boxes,
underfull `\vbox`es, missing glyphs and pandoc's own warnings. `compile_with_glossaries.sh` passes
two LaTeX diagnostics as `--advisory-regex` instead:

- an underfull `\hbox`: a loose line loses nothing, unlike an overfull one, and whether it appears
  depends on where the prose happens to wrap;
- tcolorbox's "Using nobreak failed" page-break hint.

Advisories are **printed with the build and counted**, not fatal. Prefer `--advisory-regex`, which
keeps a diagnostic visible; use `--ignore-regex` only for something that should not be reported at
all.

To debug one stage, drive the container yourself. The mounts and the empty entrypoint stay; only
the command after `activate &&` changes:

```bash
nerdctl run --rm --entrypoint "" -v "$(pwd)/md2pdfLib:/md2pdfLib" -v "$(pwd)/data:/data" \
  pandoc_all sh -c '. md2pdf/bin/activate && <command>'
```

| `<command>` | Builds |
| --- | --- |
| `uv run python md2pdfLib/build.py {book\|beamer\|demo\|example\|pptx}` | the Pandoc targets, no glossaries |
| `./md2pdfLib/scripts/compile_with_glossaries.sh --type book` | the book, full TeX pipeline |

---

## Python Conventions

### Tooling

| Tool | Purpose | Config |
|------|---------|--------|
| **uv** | Package manager, venv, script runner | `uv run python script.py` |
| **ruff** | Linter + formatter | `[tool.ruff]` in `pyproject.toml` |
| **ty** | Type checker | `[tool.ty]` in `pyproject.toml` |

### Code Style

- **Type annotations required** on all functions (`str | None` unions)
- **Comments: one line, only the why**, and none where the logic is obvious: the family rule in [`ANTfrastructure/AGENTS.md` § Comments](https://github.com/Kataglyphis/ANTfrastructure/blob/develop/AGENTS.md#comments-one-line-only-the-why)
- **Search with `rg`**, not `grep -r`: the family rule in [`ANTfrastructure/AGENTS.md` § Searching the tree](https://github.com/Kataglyphis/ANTfrastructure/blob/develop/AGENTS.md#searching-the-tree-ripgrep-rg).
- `pathlib.Path` for every path operation (not `os.path` or string concatenation)
- Every `subprocess.run()` call **must** use `check=True`
- Every public-API function **must** have a docstring: one summary line, Google-style Args/Returns only where not obvious
- `if __name__ == "__main__":` blocks call `main()`, which parses arguments and passes them on;
  nothing reaches back into `sys.argv` to hand a value over
- Errors raise `BuildError` (from `md2pdfLib.pandoc_builder`) or `sys.exit(1)` — never silent

### pyproject.toml

[`pyproject.toml`](pyproject.toml) is authoritative; read it, not a copy here. Today it sets ruff
`line-length = 100`, `target-version = "py314"`, lint rules
`["E", "F", "I", "N", "W", "UP", "B", "C4", "SIM"]`, double quotes, spaces, LF endings; `ty` for
type checks; `pytest` + `pytest-cov` + `shellcheck-py` under the `dev` extra. Code stays
3.14-compatible (`requires-python = ">=3.14"`).

### Running Tools

```bash
# On the host -- all five are CI gates in linux-x64.yml, in this order:
uv run --extra dev ruff check .
uv run --extra dev ruff format --check .
uv run --extra dev ty check md2pdfLib style sphinx-kataglyphis-theme
git ls-files -z '*.sh' | xargs -0 uv run --extra dev shellcheck
uv run --extra dev pytest tests/ -q
```

`--extra dev` is required: ruff, ty, pytest, pytest-cov and the theme package
`tests/test_theme.py` imports all live in that extra. Without it a fresh checkout resolves
`pygments` alone, and every command above fails with "program not found" instead of on a real
defect.

`tests/test_brand_divs_filter.py` drives `md2pdfLib/common/filters/brand-divs.lua` through **real
pandoc** and skips when pandoc is absent, so a host without it skips those 23 tests. CI installs
pandoc (at the version the Dockerfile pins) before the suite. Locally, use the image:

```bash
nerdctl run --rm --entrypoint "" -v "$(pwd):/repo" -w /repo pandoc_all   sh -c '. /md2pdf/bin/activate && uv pip install -q pytest          && python -m pytest tests/test_brand_divs_filter.py -o addopts=""'
```

### Entry Point

Use the top-level `build.py` CLI; never add a per-document wrapper script.
`uv run python build.py {book|beamer|demo|example|pptx}` on the host,
`uv run python md2pdfLib/build.py {book|beamer|demo|example|pptx}` in the container, where only
`/md2pdfLib` is mounted.

---

## Docs Conventions

**Write docs like a developer: short and precise** (owner, 2026-10-19). Say what a thing does,
how to run it and what breaks; no filler, no marketing, no repetition.

## Shell Scripting Conventions

- **Shebang:** `#!/usr/bin/env bash`
- **Safety:** Every script **must** start with `set -euo pipefail`
- **No unparameterized output names** — use `OUTPUT_NAME` variable or CLI args
- **Working directory for TeX tools:** Always run `biber`, `makeglossaries`,
  `makeindex` inside `data/out/` (use a subshell: `(cd data/out && ...)`)
- **No `rm -rf` without `${VAR:?}` guard** to prevent accidental root deletion
- Use `"$(dirname "$0")"` for relative references to sibling scripts

`linux-x64.yml` runs `shellcheck` over `git ls-files '*.sh'`, so no tracked script escapes the
gate. The local command is the `shellcheck` line under *Running Tools*: NUL-separated, because an
unquoted `$(git ls-files ...)` word-splits (SC2046).

### Shared Compile Script

`md2pdfLib/scripts/compile_with_glossaries.sh` is the canonical compile script. It takes `--type`
(plus an optional `--strict-warnings`) and nothing else: a generic positional mode had no callers
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
│   └── logos/
├── third_party/
│   ├── awesome-beamer/      ← git submodule
│   └── smile/               ← git submodule
```

No document sets a colour or a font; they come from `style/brand.json`
([`style/README.md`](style/README.md)). The per-document headers Pandoc injects live in
`data/<doc>/latex/main.tex`.

### Hardcoded Values

- LaTeX header files use `\providecommand`, never `\newcommand`, so Pandoc metadata or a preamble
  injection can override a value
- **Never write an identity value by hand.** The author name, both e-mail addresses, the URL, the
  GitHub handle and the institute live in the `identity` section of `style/brand.json` and are
  generated like the colours: `md2pdfLib/style/brand-identity.tex` for LaTeX (`\brandName`,
  `\brandEmail`, `\brandGithub`, `\brandUrl`, `\brandUrlDisplay`, `\brandInstitute`, plus the
  `\myname`/`\myurl`/`\githubBase` aliases the classes already used), the generated
  `author:`/`institute:` keys for Pandoc, and `brand()["identity"]` for Python and Sphinx. While
  this rule only *asked* for consistency, the name reached 16 files and the URL three spellings;
  `tests/test_identity_is_single_source.py` now fails the build. Prose may name the author; a
  template may not.

### TeX Engine

- Always **LuaLaTeX** (not pdfLaTeX or XeLaTeX)
- `lualatex -output-directory=data/out data/out/file.tex`: the output directory keeps the build
  apart from the sources and is required

### Pandoc Metadata

- `md2pdfLib/pandoc/base.yml` is the metadata source for `book`
- A document type's own `pandoc/metadata.yml` holds the extra metadata its preset needs (for
  example `presentation`)
- `documentclass:` paths are relative to the project root
- Syntax highlighting themes are set in `md2pdfLib/presets.py` through Pandoc's
  `--syntax-highlighting` option
- **Do not** duplicate a value between metadata files and preset args unless Pandoc requires a
  dedicated CLI option

---

## Adding a New Document Type

1. Create the input markdown directory `data/<type>/chapters/`
2. Create the LaTeX header `data/<type>/latex/main.tex` (or reuse an existing one)
3. Create the metadata `md2pdfLib/<type>/pandoc/metadata.yml`, or extend
   `md2pdfLib/pandoc/base.yml` when the new type deliberately shares the `book` base. **A new
   metadata file goes into `YAML_TARGETS` in `style/generate_style.py`** with a seed `mainfont:`
   line; that generates the brand block into it. Without it the document builds in Pandoc's
   default font with no brand link colours, and no check notices.
4. Add a factory function in `md2pdfLib/presets.py`, set `highlight_style` there if needed, and
   register it in `PRESETS`
5. Add the type to `DOC_TARGETS` in the `Makefile` (and to `WATCH_TARGETS` plus a
   `WATCH_DIR_<type>`/`WATCH_EXT_<type>` pair if it should be watchable)
6. Add a case in `scripts/build_in_container.sh`; the `beamer|demo` case shows how two targets
   share one pipeline
7. Optionally add a `--type` mapping in `md2pdfLib/scripts/compile_with_glossaries.sh`

`tests/test_presets_reach_every_source.py` enforces steps 1–4: it fails when a preset names a
path that does not exist, and when any Markdown under `data/` is collected by no preset.
`get_sorted_markdown_files()` lists **one level**: Markdown in a subdirectory of an `input_dir` is
never passed to pandoc, so such a subdirectory needs its own preset (that is what `demo` is).

---

## What NOT to Do

- **Do not** duplicate LaTeX templates: `md2pdfLib/book/template/latex/` is the shared location
  for book templates
- **Do not** use `docker` for **local** commands; use **nerdctl** (BuildKit / rootless). The
  scripts accept `CONTAINER_RUNTIME=docker` where nerdctl is missing; both run the same image.
- **Do not** add a workflow that builds the `Dockerfile` or the documents. The two build and
  publishing workflows need no TeX distribution, named per the family convention (2026-09-24):

  | Workflow | Name | Runs | Was |
  | --- | --- | --- | --- |
  | `linux-x64.yml` | "Linux x64 · build + test" | brand drift, lint, types, tests | `checks.yml` |
  | `docs.yml` | "Docs · publish" | builds the Sphinx docs on every push; publishes them to GitHub Pages from `develop` | `docs-pages.yml` |

  Separate quality workflows measure code and verify submodule pins; they do not build the
  image or documents.

  Two were removed on purpose: `publish-image.yml`, because nothing consumed the GHCR image it
  pushed, and the document-building job, because building the ~8.5 GB `texlive-full` image on
  every push cost more than it caught.

  **So nothing in CI compiles LaTeX**: no CI job catches a broken template, a missing TeX package
  or an overfull box. Build the documents with the strict gates locally, before releasing
  anything that touches a template, a preset or the brand:

  ```bash
  STRICT_WARNINGS=1 ./scripts/build_in_container.sh {book|beamer|demo|example|pptx|cv|letter}
  ```

- **Do not** commit `data/out/` (it is in `.gitignore`)
- **Do not** run `nerdctl build` before checking buildkitd is running
  (`systemctl --user status buildkit.service`)
- `--entrypoint ""` in a `nerdctl run` of the `pandoc_all` image is a harmless leftover, not a
  requirement: [Getting Started § Running the Container Manually](docs/getting-started.md#running-the-container-manually).
- **Do not** replace `texlive-full` in the Dockerfile with individual texlive collections. The
  full scheme is deliberate: documents may pull in any LaTeX package, and a missing collection
  fails a build much later and less obviously than the one-time image-size cost.

---

## Version Pins

The `Dockerfile` and `uv.lock` are authoritative; this table is a snapshot, and
`tests/test_docs_versions.py` fails when its Ubuntu, Pandoc or uv row drifts from the Dockerfile.
Pandoc and uv are synced from ANTfrastructure's `linux/scripts/01-core/versions.env` by its
`docs/scripts/sync_versions.py`: bump them there, never in the Dockerfile
([how](docs/project-info.md#external-dependencies)).

| Component | Version | Source |
|-----------|---------|--------|
| Ubuntu | 26.04 | `FROM ubuntu:26.04` in Dockerfile |
| Pandoc | 3.12.1 | `ARG PANDOC_VERSION` in Dockerfile, SHA256-verified .deb (synced from ANTfrastructure) |
| TeX Live | 2025 | Ubuntu 26.04 repos (`texlive-full`, deliberate) |
| uv | 0.13.1 | `ARG UV_VERSION` in Dockerfile, pinned installer (synced from ANTfrastructure) |
| Pygments | >=2.17, pinned in `uv.lock` | `pyproject.toml` runtime dependency |
| Python | 3.14 | `python3-full` from Ubuntu 26.04 repos |
