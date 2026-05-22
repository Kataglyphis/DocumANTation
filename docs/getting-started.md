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

## 4) Build the Documentation Site

```bash
uv run --extra docs sphinx-build -W -b html docs docs/_build/html
```

Generated HTML lands in `docs/_build/html/`.

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
./scripts/build_in_container.sh cv
```

Optional host shortcuts if `make` is installed:

```bash
make book
make diss
make beamer
make cv
```

## 6) Enable Strict Warning Checks

```bash
STRICT_WARNINGS=1 ./scripts/build_in_container.sh book
STRICT_WARNINGS=1 ./scripts/build_in_container.sh cv
```

## Next Steps

- Repository structure and shared components: [Overview](overview.md)
- TeX and Pandoc compilation stages: [Build Pipeline](build-pipeline.md)
