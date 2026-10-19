# Sphinx Book Theme Template Kit

Files to bootstrap a documentation website in any repository. They live in **DocumANTation**, the
single source of truth for shared Kataglyphis docs tooling, which downstream repos consume as a
git submodule.

## Included files

| File | Status |
| --- | --- |
| `index_template.rst` | Landing-page template with cards — copy it and edit it |
| `conf_base.py` | **Frozen legacy shim.** Loaded by path, not by anything here |
| `custom.css` | **Generated.** A verbatim copy of the theme stylesheet |

The theme baseline and the visual style are not *authored* here: they live once, in the
`sphinx-kataglyphis-theme/` package, whose brand tokens are generated from
[`style/brand.json`](../../../style/README.md).

### Why `conf_base.py` and `custom.css` are still here

**Two** repositories load `conf_base.py` **by filesystem path** from their own
`docs/source/conf.py`:

| Repo | Notes |
| --- | --- |
| `AccelerANTgine` | also symlinks its `_static/css/custom.css` into this directory |
| `BeschleunigerBallett` | branch `develop`; falls back to an inline copy of these values if the path is missing |

Both read `SPHINX_EXTENSIONS`, `HTML_THEME`, `HTML_THEME_OPTIONS`, `HTML_STATIC_PATH` and
`HTML_CSS_FILES`, and both set their own `repository_url` afterwards. Deleting the two files broke
the first of them with

```text
ImportError: Cannot load shared Sphinx baseline from .../sphinx-book/conf_base.py
```

until they were restored. So keep them, but not as a supported route:

- `conf_base.py` is **frozen**: pure constants, no imports, no brand values. It deliberately lags
  `setup_theme()`: it can name only a Pygments style that Pygments itself ships, because neither
  consumer installs `sphinx-kataglyphis-theme`. Migrate them to `setup_theme()`; do not grow this
  file.
- `custom.css` is **generated** by `style/generate_style.py`; do not edit it. As a hand-written
  fork it rotted as predicted: ~490 lines behind the original and still painting links the
  pre-cyan green, so one site rendered a different brand while every drift check passed. It is
  now a byte copy that `--check` and the test suite both enforce.

## How to consume

New consumers install the theme and call `setup_theme()`. There is deliberately no second
supported way: every copy this folder handed out drifted.

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

That brings the theme, the brand CSS, the shared code palette and the Kataglyphis fonts. This
repo's own `docs/conf.py` makes the same call, so what works here works downstream.

Defaults, each set only when `conf.py` or the call has not set it: the family logo as `html_logo`
and `html_favicon`, the project name as `html_title` and as the logo text (Sphinx's own title,
`<project> <release> documentation`, doubled an index titled "… documentation"), and
`myst_heading_anchors = 6`.

### Links

Markdown links are written for GitHub and work on the site too:

- A link to `page.md` or `page.md#a-heading` resolves to the built page. Every heading gets
  GitHub's slug, so an anchor that works on GitHub works here.
- A link to a repository file the site does not publish (outside the docs source dir, a
  directory, an excluded page) goes to `<repository_url>/blob/develop/<path>`, `tree` for a
  directory, with its `#fragment`. The repository is the nearest `.git` above the source dir.
- A link to a file that does not exist stays a MyST warning, so `sphinx-build -W` still fails on
  it.

`kataglyphis_repository_links=False` turns the GitHub links off; `kataglyphis_repository_branch`
names another branch. Both go into the `setup_theme()` call.

## Per-project tweaks

Do not fork the stylesheet. Put project rules in their own file and use the brand tokens, not
literals:

```python
setup_theme(globals(), ..., html_css_files_extra=["css/my-project.css"])
```

```css
/* docs/_static/css/my-project.css */
.my-thing { color: var(--brand-accent-strong); border: 1px solid var(--brand-surface-border); }
```
