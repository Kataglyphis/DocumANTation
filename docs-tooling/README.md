# docs-tooling

Shared documentation tooling for Kataglyphis repositories. With the sibling
[`sphinx-kataglyphis-theme/`](../sphinx-kataglyphis-theme) package it makes **DocumANTation** the
single source of truth for how the Kataglyphis docs sites are themed, templated and generated.
Downstream repos consume it as a git submodule.

## Contents

| Path | Purpose |
| --- | --- |
| `source_templates/sphinx-book/` | Landing-page template for a docs site, plus a frozen path-loaded shim for two legacy consumers — see its [README](source_templates/sphinx-book/README.md) before touching either |

Only genuinely shared things live here. Two former residents left:

- `source_templates/sphinx-python/`, a baseline for Python API docs (autodoc/napoleon), was
  removed: an org-wide audit found no `conf.py` that read it, and unlike the `sphinx-book` shim it
  imports `sphinx_kataglyphis`, so any consumer able to load it could call `setup_theme()` instead
  and get the brand CSS and shared code palette the baseline lacked.
  `git log -- docs-tooling/source_templates/sphinx-python/` has it if a Python project wants the
  autodoc defaults back.
- `sync_versions.py` and `generate-website-licenses.py` moved back to ANTfrastructure: they read
  that repo's `linux/Dockerfile.*`, `windows/Dockerfile*` and `versions.env`, so no other consumer
  could run them, and keeping them here cost a submodule commit and a pin bump on every
  ANTfrastructure version bump.

The Sphinx **theme** (the `setup_theme()` helper, scaffold CLI and base CSS) is a separate package
in [`../sphinx-kataglyphis-theme`](../sphinx-kataglyphis-theme), so consumers can `pip install -e`
it.

**Colours and fonts** are not defined here. They live once in
[`../style/brand.json`](../style/README.md) and are generated into the LaTeX, Pandoc, CSS and JSON
consumers; [`style/README.md`](../style/README.md) shows how to read the brand from Python,
Sphinx, LaTeX or any other language.

## Consuming from another repository

Add this repo as a submodule (the family layout puts it under `third_party/`):

```bash
git submodule add https://github.com/Kataglyphis/DocumANTation third_party/DocumANTation
```

Then install the theme package and call `setup_theme()`:
[`source_templates/sphinx-book/README.md`](source_templates/sphinx-book/README.md). There is
deliberately no copy-the-files route for new consumers: every copy this repo handed out drifted.
The two repos that still load a template by path are documented there, and the stylesheet one of
them links is generated, so it cannot drift again.
