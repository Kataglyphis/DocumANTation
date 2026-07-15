# docs-tooling

Shared documentation tooling for Kataglyphis repositories. This directory, together
with the sibling [`sphinx-kataglyphis-theme/`](../sphinx-kataglyphis-theme) package,
makes **Kataglyphis-DocumANTation** the single source of truth for how the
Kataglyphis docs sites are themed, templated, and generated. Downstream repos
consume it as a git submodule.

## Contents

| Path | Purpose |
| --- | --- |
| `source_templates/sphinx-book/` | Baseline `sphinx-book-theme` config and a landing-page template |
| `source_templates/sphinx-python/` | Baseline Sphinx config for Python API docs (autodoc/napoleon) |
| `scripts/sync_versions.py` | Regenerate version snapshots / inline markers / dependency tables from a repo's `versions.env` + `deps.json` |
| `scripts/generate-website-licenses.py` | Generate the website open-source-license markdown pages from `deps.json` + `versions.env` |

The Sphinx **theme** itself (the `setup_theme()` helper, scaffold CLI, and base
CSS) is packaged separately in [`../sphinx-kataglyphis-theme`](../sphinx-kataglyphis-theme)
so consumers can `pip install -e` it.

**Colours and fonts** are not defined here. They live once in
[`../style/brand.json`](../style/README.md) and are generated into the LaTeX,
Pandoc, CSS and JSON consumers — see [`style/README.md`](../style/README.md) for
how to read the brand from Python, Sphinx, LaTeX, or any other language.

## Consuming from another repository

Add this repo as a submodule (e.g. under `external/`):

```bash
git submodule add https://github.com/Kataglyphis/Kataglyphis-DocumANTation external/Kataglyphis-DocumANTation
```

Then either install the theme package (see
[`source_templates/sphinx-book/README.md`](source_templates/sphinx-book/README.md),
Option A) or reference the template files directly (Option B).

## Running the generation scripts

Both scripts are parameterized so they can run against the consuming repo from
inside the submodule. Point them at the consumer's root with `--repo-root`:

```bash
python external/Kataglyphis-DocumANTation/docs-tooling/scripts/sync_versions.py \
  --check --repo-root . \
  --versions-env linux/scripts/01-core/versions.env

python external/Kataglyphis-DocumANTation/docs-tooling/scripts/generate-website-licenses.py \
  --check --repo-root . \
  --deps-json docs/deps/deps.json \
  --versions-env linux/scripts/01-core/versions.env \
  --assets-dir linux/webserver/dist/assets/assets/documents/footer
```

Use `--write` instead of `--check` to update files in place. The version keys,
Dockerfile paths, and marker names these scripts look for follow the
ContainerHub layout; a consuming repo needs the same `versions.env` / `deps.json`
conventions for them to apply.
