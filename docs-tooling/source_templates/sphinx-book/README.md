# Sphinx Book Theme Template Kit

This folder contains reusable files to bootstrap a documentation website across
multiple repositories. It lives in **Kataglyphis-DocumANTation**, the single
source of truth for shared Kataglyphis docs tooling, and is consumed by
downstream repos as a git submodule.

## Included files

- `conf_base.py` – baseline Sphinx theme settings for `sphinx-book-theme`
- `custom.css` – shared visual style (light/dark mode)
- `index_template.rst` – modern landing page template with cards

## Two ways to consume

### Option A — install the theme package (recommended)

The sibling `sphinx-kataglyphis-theme/` package wraps all of this behind a single
`setup_theme()` call. Add it to your `requirements.txt`:

```text
-e ./external/Kataglyphis-DocumANTation/sphinx-kataglyphis-theme
```

and in `docs/conf.py`:

```python
from sphinx_kataglyphis import setup_theme

setup_theme(
    globals(),
    repository_url="https://github.com/org/repo",
    project_name="My Project",
)
```

### Option B — reference these template files directly

1. Copy the shared assets into your docs tree:

```bash
mkdir -p docs/source/_static/css
cp external/Kataglyphis-DocumANTation/docs-tooling/source_templates/sphinx-book/custom.css docs/source/_static/css/custom.css
cp external/Kataglyphis-DocumANTation/docs-tooling/source_templates/sphinx-book/index_template.rst docs/source/index.rst
```

2. Add dependencies to your `requirements.txt`:

```text
sphinx-book-theme
sphinx_design
myst-parser
```

3. Configure `docs/source/conf.py`:

```python
extensions = ["myst_parser", "sphinx_design"]
html_theme = "sphinx_book_theme"
html_static_path = ["_static"]
html_css_files = ["css/custom.css"]
```

4. Build docs as usual.
