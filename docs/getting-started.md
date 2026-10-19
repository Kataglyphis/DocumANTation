# Getting Started

From clone to a built document and the docs site.

## 1) Prerequisites

- `nerdctl` (or docker: the scripts take `CONTAINER_RUNTIME=docker`)
- BuildKit running for local image builds: `systemctl --user status buildkit.service`
- Git with submodule support
- Optional: `make` for shortcut targets

## 2) Clone the Repository

```bash
git clone --branch develop --recurse-submodules https://github.com/Kataglyphis/DocumANTation.git
cd DocumANTation
```

Cloned without submodules:

```bash
git submodule update --init --recursive
```

## 3) Build the Container Image

```bash
nerdctl build . -t pandoc_all
```

The `pandoc_all` image ([`Dockerfile`](https://github.com/Kataglyphis/DocumANTation/blob/develop/Dockerfile))
carries everything the PDF pipeline needs; the host never installs TeX:

- Ubuntu 26.04 with the full **TeX Live** distribution and **LuaLaTeX**
- **Pandoc** (pinned via the `PANDOC_VERSION` build arg)
- ImageMagick, Ghostscript, and a `uv`-managed `md2pdf` virtualenv
- the `awesome-beamer` and `smile` LaTeX themes baked into `texmf`

> The build pulls `texlive-full`, so the first build is large and slow. Check out the
> beamer/smile submodules first (step 2): the image copies them in.

## 4) Build the Documentation Site

This site builds **on the host** with Sphinx, not in the `pandoc_all` container:

```bash
uv run --extra docs sphinx-build -W -b html docs docs/_build/html
```

The HTML lands in `docs/_build/html/`. The published site is
[kataglyphis.github.io/DocumANTation](https://kataglyphis.github.io/DocumANTation/): `docs.yml`
builds it on every push and deploys it from `develop`.

## 5) Build a Document Target

Every output lands in `data/out/`.

### Book

```bash
./scripts/build_in_container.sh book
```

### Presentation

```bash
./scripts/build_in_container.sh beamer   # PDF slides
./scripts/build_in_container.sh pptx     # PowerPoint deck, same sources
./scripts/build_in_container.sh demo     # the slide primitives showcase
```

`beamer` and `pptx` build `data/presentation/`; `demo` builds `data/presentation/demo/` as a deck
of its own ([why a separate target](overview.md#demo)).

### Starter document

```bash
./scripts/build_in_container.sh example
```

Writes `data/out/example_output.pdf` from `data/example/chapters/` in one Pandoc call, with no
bibliography, glossary or nomenclature pass. Replace its Markdown with your own to start a
project.

### CV

```bash
./scripts/build_in_container.sh cv                  # English
CV_LANG=german ./scripts/build_in_container.sh cv   # German
CV_PROFILE=parallel-ai ./scripts/build_in_container.sh letter  # data/cv/letters/<CV_PROFILE>.tex
```

The CV lands as `CV_Jonas_Heinle_<language>.pdf`. `CV_PROFILE` selects a tailored section set
from `data/cv/profiles/`, and `letter` typesets that profile's cover letter
(`data/cv/letters/<CV_PROFILE>.tex`) in the same class; `data/cv/README.md` in the repository has
both.

With `make` installed:

```bash
make book
make beamer
make demo
make example
make pptx
make cv
make cv CV_LANG=german
make cv-all              # both published CV variants
```

## 6) Enable Strict Warning Checks

```bash
STRICT_WARNINGS=1 ./scripts/build_in_container.sh book
STRICT_WARNINGS=1 ./scripts/build_in_container.sh cv
```

What fails the build: [Build Pipeline § Strict Warning Checks](build-pipeline.md#strict-warning-checks).

## 7) Live Demo Mode

The PDF rebuilds on every source change:

```bash
make watch-beamer    # rebuilds on every .md change
make watch-book      # same for the book
```

It watches with `entr`; pair it with a PDF viewer that reloads by itself (`zathura`, `evince`, or
`skim` on macOS). `watch-cv`, `watch-demo` and `watch-example` exist too (`WATCH_TARGETS` in the
`Makefile`); the CV one watches the `.tex` sources in `data/cv/`.

## Running the Container Manually

`build_in_container.sh` and `make` wrap a plain `nerdctl run`. To debug or run a one-off
command, mount `md2pdfLib/` and `data/` yourself:

```bash
nerdctl run --rm --entrypoint "" \
  -v "$(pwd)/md2pdfLib:/md2pdfLib" \
  -v "$(pwd)/data:/data" \
  pandoc_all sh -c '. md2pdf/bin/activate && uv run python /md2pdfLib/build.py beamer'
```

> **`--entrypoint ""` is optional.** The image has had no `ENTRYPOINT` since 2026-05-22
> (`23734a7`), only a `CMD` that opens an interactive shell, so a command after the image name
> replaces that `CMD` with or without the flag (measured 2026-09-25). The wrapper scripts still
> pass it; it is harmless.

An interactive shell in the container:

```bash
nerdctl run --rm -it \
  -v "$(pwd)/md2pdfLib:/md2pdfLib" \
  -v "$(pwd)/data:/data" \
  pandoc_all
```

## Next Steps

- Repository structure and shared components: [Overview](overview.md)
- TeX and Pandoc compilation stages: [Build Pipeline](build-pipeline.md)
- Rules and quick commands for agents/contributors: [AGENTS.md](https://github.com/Kataglyphis/DocumANTation/blob/develop/AGENTS.md)
