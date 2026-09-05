# Sphinx Book Theme Template Kit

Files to bootstrap a documentation website across repositories. This lives in
**DocumANTation**, the single source of truth for shared Kataglyphis
docs tooling, and is consumed by downstream repos as a git submodule.

## Included files

| File | Status |
| --- | --- |
| `index_template.rst` | Landing-page template with cards — copy it and edit it |
| `conf_base.py` | **Frozen legacy shim.** Loaded by path, not by anything here |
| `custom.css` | **Generated.** A verbatim copy of the theme stylesheet |

The theme baseline and the visual style are not *authored* in this folder — they
live once, in the `sphinx-kataglyphis-theme/` package, and its brand tokens are
generated from [`style/brand.json`](../../../style/README.md).

### Why `conf_base.py` and `custom.css` are still here

**Two** repositories load `conf_base.py` **by filesystem path** from their own
`docs/source/conf.py`:

| Repo | Notes |
| --- | --- |
| `Kataglyphis-Cpp-Inference` | also symlinks its `_static/css/custom.css` into this directory |
| `Kataglyphis-BeschleunigerBallett` | branch `develop`; falls back to an inline copy of these values if the path is missing |

Both read `SPHINX_EXTENSIONS`, `HTML_THEME`, `HTML_THEME_OPTIONS`,
`HTML_STATIC_PATH` and `HTML_CSS_FILES`, and both set their own
`repository_url` afterwards. Deleting the two files broke the first of them with

```text
ImportError: Cannot load shared Sphinx baseline from .../sphinx-book/conf_base.py
```

until they were restored. So do not delete them — but do not treat them as a
supported route either:

- `conf_base.py` is **frozen**: pure constants, no imports, no brand values. It
  is deliberately behind `setup_theme()` — it can only name a Pygments style
  that Pygments itself ships, because neither consumer installs
  `sphinx-kataglyphis-theme`. Migrate them to `setup_theme()`; do not grow this
  file.
- `custom.css` is **generated** by `style/generate_style.py` — do not edit it.
  It used to be a hand-written fork, and it rotted exactly as predicted: ~490
  lines behind the original and still painting links the pre-cyan green, so that
  one site rendered a different brand while every drift check passed. It is now
  a byte copy that `--check` and the test suite both enforce.

## How to consume

New consumers: install the theme and call `setup_theme()`. There is no second
supported way, on purpose — every copy this folder ever handed out drifted.

`requirements.txt`:

```text
-e ./third_party/DocumANTation/sphinx-kataglyphis-theme
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
