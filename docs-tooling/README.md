# docs-tooling

Shared documentation tooling for Kataglyphis repositories. This directory, together
with the sibling [`sphinx-kataglyphis-theme/`](../sphinx-kataglyphis-theme) package,
makes **Kataglyphis-DocumANTation** the single source of truth for how the
Kataglyphis docs sites are themed, templated, and generated. Downstream repos
consume it as a git submodule.

## Contents

| Path | Purpose |
| --- | --- |
| `source_templates/sphinx-book/` | Landing-page template for a docs site |
| `source_templates/sphinx-python/` | Baseline Sphinx config for Python API docs (autodoc/napoleon) |

Only genuinely shared things live here. `sync_versions.py` and
`generate-website-licenses.py` used to, and moved back to ContainerHub: they
read that repo's `linux/Dockerfile.*`, `windows/Dockerfile*` and `versions.env`,
so no other consumer could run them, and keeping them here meant every
ContainerHub version bump needed a submodule commit and a pin bump.

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

Then install the theme package and call `setup_theme()` — see
[`source_templates/sphinx-book/README.md`](source_templates/sphinx-book/README.md).
There is deliberately no second, copy-the-files route: every copy this repo
ever handed out drifted.
