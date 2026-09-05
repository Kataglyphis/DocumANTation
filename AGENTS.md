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
md2pdfLib/presentation/pptx/  → OOXML post-processing for the PowerPoint target
md2pdfLib/presentation/pptx/pptx_common.py → shared OOXML layer for that package
Dockerfile         → container build definition
```

### The pptx package

Every module there rewrites a .pptx archive, and the shared mechanics live in
`pptx_common.py` — use them rather than writing the loop again:

| Need | Use |
| --- | --- |
| Change some slides and write the deck back | `edit_slides(deck, transform)` |
| A slide's layout / master / layout name | the `DeckParts` passed to the transform |
| Name the archive parts | `SLIDE_RE`, `MASTER_RE`, `THEME_RE`, `LAYOUT_RE`, `LAYOUT_RELS_RE` |
| Pin unsized runs to a font size | `sized_runs(fragment, size)` |
| Add shapes to a slide or layout | `append_shapes(xml, shapes)` -- literal, never `re.sub` |
| Read the brand | `brand_tokens()` (md2pdfLib/style/, the only copy the container mounts) |
| A `<deck.pptx>` entry point | `run_cli(action, errors=(...))` |

These modules are run **by path** from the build script
(`uv run python /md2pdfLib/presentation/pptx/finalize_deck.py <deck>`), so each
one bootstraps `sys.path` with the md2pdf root before importing its siblings as
`md2pdfLib.presentation.pptx.*`. Do not reintroduce a bare `import pptx_common`
fallback: it produced a second copy of every module under a top-level name, so a
test and the build could hold two module objects with two sets of constants —
and `ty` cannot resolve it.

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
./scripts/build_in_container.sh {book|beamer|demo|example|pptx|cv}

# The same targets via Makefile, plus the CV variants
make {book|beamer|demo|example|pptx|cv}
make cv CV_LANG=german
make cv-all

# Any target, with the strict warning gates
STRICT_WARNINGS=1 ./scripts/build_in_container.sh book
```

### What the strict gate fails on

`md2pdfLib/check_build_log.py` fails the build on LaTeX/Package/Class warnings,
overfull boxes, underfull `\vbox`es, missing glyphs and pandoc's own warnings.
Two LaTeX diagnostics are passed as `--advisory-regex` by
`compile_with_glossaries.sh` instead: an underfull `\hbox` (a loose line — it
loses nothing, unlike an overfull one, and whether it appears depends on where
the surrounding prose happens to wrap) and tcolorbox's "Using nobreak failed"
page-break hint. Advisories are **printed with the build and counted**, just not
fatal. Use `--ignore-regex` only for something that should not be reported at
all; prefer `--advisory-regex`, which keeps it visible.

To debug a single stage, drive the container yourself. The mounts and the empty
entrypoint never change — only the command after `activate &&` does:

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
| **ruff** | Linter + formatter | Place `[tool.ruff]` in `pyproject.toml` (see below) |
| **ty** | Type checker | Place `[tool.ty]` in `pyproject.toml` (see below) |

### Code Style

- **Type annotations required** on all functions (Python 3.10+ syntax: `str | None`)
- **No comments** unless the logic is genuinely non-obvious
- Use `pathlib.Path` for all path operations (not `os.path` or string concatenation)
- All `subprocess.run()` calls **must** use `check=True`
- All public-API functions **must** have docstrings (Google style)
- Use the top-level `build.py` entry point instead of per-document wrapper scripts
- `if __name__ == "__main__":` blocks call `main()`, which parses arguments and
  passes them on — nothing reaches back into `sys.argv` to hand a value over
- Errors raise `BuildError` (from `md2pdfLib.pandoc_builder`) or `sys.exit(1)` — never silent

### pyproject.toml

[`pyproject.toml`](pyproject.toml) is authoritative — read it rather than a
copy here, which is one edit away from being wrong. What it sets today: ruff at
`line-length = 100`, `target-version = "py310"`, lint rules
`["E", "F", "I", "N", "W", "UP", "B", "C4", "SIM"]`, double quotes, spaces, LF
endings; `ty` for type checks; `pytest` + `pytest-cov` + `shellcheck-py` under
the `dev` extra.

Code must stay 3.10-compatible (`requires-python = ">=3.10"`) — e.g.
`int.from_bytes(...)` needs an explicit `byteorder` before 3.11.

### Running Tools

```bash
# On the host -- all five are CI gates in checks.yml, in this order:
uv run --extra dev ruff check .
uv run --extra dev ruff format --check .
uv run --extra dev ty check md2pdfLib style sphinx-kataglyphis-theme
uv run --extra dev shellcheck $(git ls-files '*.sh')
uv run --extra dev pytest tests/ -q
```

`--extra dev` is not optional: ruff, ty, pytest, pytest-cov and the theme
package `tests/test_theme.py` imports all live in that extra, so a fresh
checkout without it resolves `pygments` alone and every command above fails with
"program not found" rather than on a real defect.

`tests/test_brand_divs_filter.py` drives `md2pdfLib/common/filters/brand-divs.lua`
through **real pandoc** and skips when pandoc is absent, so on a host without it
those 23 tests do not run. CI installs pandoc (at the version the Dockerfile
pins) before the suite so they always do; to run them locally, use the image:

```bash
nerdctl run --rm --entrypoint "" -v "$(pwd):/repo" -w /repo pandoc_all   sh -c '. /md2pdf/bin/activate && uv pip install -q pytest          && python -m pytest tests/test_brand_divs_filter.py -o addopts=""'
```

### Entry Point

Use the `build.py` CLI rather than adding document-specific wrapper scripts:
`uv run python build.py {book|beamer|demo|example|pptx}` on the host, or
`uv run python md2pdfLib/build.py {book|beamer|demo|example|pptx}` inside the container,
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

These are enforced: `checks.yml` runs `shellcheck` over `git ls-files '*.sh'`,
so every tracked script is linted and a new one cannot be added outside the
gate. Run it locally with `uv run --extra dev shellcheck $(git ls-files '*.sh')`.

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
│   └── logos/
├── third_party/
│   ├── awesome-beamer/      ← git submodule
│   └── smile/               ← git submodule
```

Colours and fonts are never written in a document — they come from
`style/brand.json`. See [`style/README.md`](style/README.md).
The per-document headers that Pandoc injects live in `data/<doc>/latex/main.tex`.

### Hardcoded Values

- In LaTeX header files, use `\providecommand` (not `\newcommand`) so values can be
  overridden from Pandoc metadata or preamble injections
- **Never write an identity value by hand.** The author name, both e-mail
  addresses, the URL, the GitHub handle and the institute live in the `identity`
  section of `style/brand.json` and are generated out, exactly like the colours:
  `md2pdfLib/style/brand-identity.tex` for LaTeX (`\brandName`, `\brandEmail`,
  `\brandGithub`, `\brandUrl`, `\brandUrlDisplay`, `\brandInstitute`, plus the
  `\myname`/`\myurl`/`\githubBase` aliases the classes already used), the
  generated `author:`/`institute:` keys for Pandoc, and `brand()["identity"]`
  for Python and Sphinx. This paragraph used to *ask* for consistency and
  nothing checked it, so the name reached 16 files and the URL acquired three
  spellings; `tests/test_identity_is_single_source.py` now fails the build
  instead. Prose may still name the author — a template may not.

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
   base. **A new metadata file must be added to `YAML_TARGETS` in
   `style/generate_style.py`** and seeded with a `mainfont:` line — that is what
   generates the brand block into it. Skip this and the document silently builds
   in Pandoc's default font with no brand link colours, and no check notices.
4. Add a factory function in `md2pdfLib/presets.py`, set `highlight_style` there if
   needed, and register it in `PRESETS`
5. Add the type to `DOC_TARGETS` in the `Makefile` (and to `WATCH_TARGETS` plus a
   `WATCH_DIR_<type>`/`WATCH_EXT_<type>` pair if it should be watchable)
6. Add a case in `scripts/build_in_container.sh` — the `beamer|demo` case shows
   how two targets share one pipeline
7. Optionally add a `--type` mapping entry in `md2pdfLib/scripts/compile_with_glossaries.sh`

`tests/test_presets_reach_every_source.py` enforces steps 1–4: it fails if a
preset names a path that does not exist, and if any Markdown under `data/` is
collected by no preset. Note that `get_sorted_markdown_files()` lists **one
level** — Markdown in a subdirectory of an `input_dir` is never passed to pandoc,
so such a subdirectory needs its own preset (that is what `demo` is).

---

## What NOT to Do

- **Do not** duplicate LaTeX templates — use `md2pdfLib/book/template/latex/` as the
  shared location for book templates
- **Do not** add comments to code unless the logic is truly non-obvious
- **Do not** use `docker` for **local** commands — use **nerdctl** locally
  (BuildKit / rootless). Scripts accept `CONTAINER_RUNTIME=docker` for
  environments without nerdctl; both run the same image.
- **Do not** add a workflow that builds the `Dockerfile` or the documents.
  Two workflows exist and neither needs a TeX distribution: `checks.yml`
  (brand drift, lint, types, tests) and `docs-pages.yml` (publishes the Sphinx
  docs to GitHub Pages). Two workflows were deliberately removed --
  `publish-image.yml`, because nothing consumed the GHCR image it pushed, and
  the document-building job, because the ~8.5 GB `texlive-full` image cost more
  to build on every push than it caught.

  **Consequence, worth stating plainly:** nothing in CI compiles LaTeX, so
  nothing in CI catches a broken template, a missing TeX package or an overfull
  box. Building the documents -- with the strict gates -- is a local step:

  ```bash
  STRICT_WARNINGS=1 ./scripts/build_in_container.sh {book|beamer|demo|example|pptx|cv}
  ```

  Run it before releasing anything that touches a template, a preset or the
  brand.
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
| Pandoc | 3.10.2 | `ARG PANDOC_VERSION` in Dockerfile, SHA256-verified .deb (synced from ContainerHub) |
| TeX Live | 2025 | Ubuntu 26.04 repos (`texlive-full`, deliberate) |
| uv | 0.12.5 | `ARG UV_VERSION` in Dockerfile, pinned installer (synced from ContainerHub) |
| Pygments | >=2.17, pinned in `uv.lock` | `pyproject.toml` runtime dependency |
| Python | 3.14 | `python3-full` from Ubuntu 26.04 repos |
