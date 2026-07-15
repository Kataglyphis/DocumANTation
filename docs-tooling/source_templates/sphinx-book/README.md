# Sphinx Book Theme Template Kit

Files to bootstrap a documentation website across repositories. This lives in
**Kataglyphis-DocumANTation**, the single source of truth for shared Kataglyphis
docs tooling, and is consumed by downstream repos as a git submodule.

## Included files

- `index_template.rst` – landing page template with cards

That is all that belongs here. The theme baseline and the visual style are
**not** duplicated in this folder — they live once, in the
`sphinx-kataglyphis-theme/` package, and its brand tokens are generated from
[`style/brand.json`](../../../style/README.md).

## How to consume

Install the theme and call `setup_theme()`. There is no second way, on purpose:
this folder used to offer a "copy the files" option, and both copies it produced
rotted — the stylesheet fork fell ~270 lines behind the original, and a
duplicated `conf_base.py` drifted away from `setup_theme()` until this repo's
own docs silently lost the shared code palette.

`requirements.txt`:

```text
-e ./external/Kataglyphis-DocumANTation/sphinx-kataglyphis-theme
```

`docs/conf.py`:

```python
from sphinx_kataglyphis import setup_theme

setup_theme(
    globals(),
    repository_url="https://github.com/org/repo",
    project_name="My Project",
)
```

That gives you the theme, the brand CSS, the shared code palette, and the
Kataglyphis fonts. This repo's own `docs/conf.py` uses exactly the same call —
if it works here, it works downstream.

## Per-project tweaks

Do not fork the stylesheet. Put project rules in their own file and use the
brand tokens rather than literals:

```python
setup_theme(globals(), ..., html_css_files_extra=["css/my-project.css"])
```

```css
/* docs/_static/css/my-project.css */
.my-thing { color: var(--brand-accent-strong); border: 1px solid var(--brand-surface-border); }
```
