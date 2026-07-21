# Getting Started

This guide takes you from clone to a working local setup for documentation and PDF builds.

## 1) Prerequisites

- `nerdctl`
- BuildKit running for local image builds: `systemctl --user status buildkit.service`
- Git with submodule support
- Optional: `make` for shortcut targets

## 2) Clone the Repository

```bash
git clone --recurse-submodules git@github.com:Kataglyphis/Kataglyphis-mdToPdf.git
cd Kataglyphis-mdToPdf
```

If you cloned without submodules:

```bash
git submodule update --init --recursive
```

## 3) Build the Container Image

```bash
nerdctl build . -t pandoc_all
```

The `pandoc_all` image (see the [`Dockerfile`](https://github.com/Kataglyphis/Kataglyphis-mdToPdf/blob/main/Dockerfile))
bundles everything the PDF pipeline needs, so you never install TeX on the host:

- Ubuntu 26.04 with the full **TeX Live** distribution and **LuaLaTeX**
- **Pandoc** (pinned via the `PANDOC_VERSION` build arg)
- ImageMagick, Ghostscript, and a `uv`-managed `md2pdf` virtualenv
- the `awesome-beamer` and `smile` LaTeX themes baked into `texmf`

> The build pulls `texlive-full`, so the first build is large and slow. Make sure
> the beamer/smile submodules are checked out first (step 2) — the image copies
> them in.

## 4) Build the Documentation Site

The HTML documentation site (this site) builds **on the host** with Sphinx — it
does *not* use the `pandoc_all` container:

```bash
uv run --extra docs sphinx-build -W -b html docs docs/_build/html
```

Generated HTML lands in `docs/_build/html/`. The container is only for the PDF
document targets in the next step.

## 5) Build a Document Target

### Book or dissertation

```bash
./scripts/build_in_container.sh book
./scripts/build_in_container.sh diss
```

### Presentation

```bash
./scripts/build_in_container.sh beamer
```

### CV

```bash
./scripts/build_in_container.sh cv                  # English
CV_LANG=german ./scripts/build_in_container.sh cv   # German
```

Both land in `data/out/` as `CV_Jonas_Heinle_<language>.pdf`.

Optional host shortcuts if `make` is installed:

```bash
make book
make diss
make beamer
make cv
make cv CV_LANG=german
make cv-all              # both published CV variants
```

## 6) Enable Strict Warning Checks

```bash
STRICT_WARNINGS=1 ./scripts/build_in_container.sh book
STRICT_WARNINGS=1 ./scripts/build_in_container.sh cv
```

## Running the Container Manually

`build_in_container.sh` and `make` are wrappers around a plain `nerdctl run`. To
drive the container yourself — for debugging, or a one-off command — run it
directly, mounting `md2pdfLib/` and `data/`:

```bash
nerdctl run --rm --entrypoint "" \
  -v "$(pwd)/md2pdfLib:/md2pdfLib" \
  -v "$(pwd)/data:/data" \
  pandoc_all sh -c '. md2pdf/bin/activate && uv run python /md2pdfLib/build.py beamer'
```

> **Always pass `--entrypoint ""`.** The image's default `CMD` drops you into an
> interactive shell; without overriding the entrypoint your `sh -c '...'` command
> is ignored. The wrapper scripts already do this for you.

Drop into an interactive shell in the container to poke around:

```bash
nerdctl run --rm -it \
  -v "$(pwd)/md2pdfLib:/md2pdfLib" \
  -v "$(pwd)/data:/data" \
  pandoc_all
```

## Next Steps

- Repository structure and shared components: [Overview](overview.md)
- TeX and Pandoc compilation stages: [Build Pipeline](build-pipeline.md)
- Rules and quick commands for agents/contributors: [AGENTS.md](https://github.com/Kataglyphis/Kataglyphis-mdToPdf/blob/main/AGENTS.md)
