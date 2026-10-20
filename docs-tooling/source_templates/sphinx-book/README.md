# Sphinx Book Theme Template Kit

Files to bootstrap a documentation website in any repository. They live in **DocumANTation**, the
single source of truth for shared Kataglyphis docs tooling, which downstream repos consume as a
git submodule.

## Included files

| File | Status |
| --- | --- |
| `index_template.rst` | Landing-page template with cards — copy it and edit it |

The theme baseline and the visual style are not *authored* here: they live once, in the
`sphinx-kataglyphis-theme/` package, whose brand tokens are generated from
[`style/brand.json`](../../../style/README.md).

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
  directory, with its `#fragment`. The repository root is the nearest directory above the
  source dir holding `.git`, `.gitmodules` or `.github`, so an export without `.git`
  (`git archive`) links like a checkout. With none of them nothing is rewritten: a file link
  stays a Sphinx download and a directory link a MyST warning.
- A path inside a submodule goes to the submodule's own repository: its `url` in `.gitmodules`
  (https, ssh or `git@host:` form) and its `branch =`, else `develop`. A nested submodule
  resolves through each level's `.gitmodules`.
- A link to a file that does not exist stays a MyST warning, so `sphinx-build -W` still fails on
  it.

With `exhale` among the extensions, the links in its tree views (`*_view_hierarchy.rst.include`)
get the ids docutils gives Exhale's labels: Exhale writes `#exhale-class-classFoo-1-1Bar` with
its case kept, docutils lowercases the id. No `include-read` hook of your own is needed. Its tree
views fold without jQuery: the theme copies its own `apply-collapsible-lists.js` over Exhale's,
whose `$(document).ready` throws `$ is not defined` since Sphinx 6 dropped jQuery.

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
