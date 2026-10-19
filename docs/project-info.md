# Project Information

## Development Tooling

| Tool | Does |
| --- | --- |
| `uv` | Local Python environments and command execution |
| `ruff` | Linting and formatting checks |
| `ty` | Static type checks for the Python build logic |
| Sphinx | Builds this documentation site |

## External Dependencies

The `pandoc_all` container image carries everything the builds need: chiefly `pandoc` for the
Markdown conversion and TeX Live/LuaLaTeX for the PDFs, plus the `awesome-beamer` and `smile`
presentation-theme submodules.

**ANTfrastructure** keeps the full list, with each component's version, upstream and license:
[Third-Party Software & Licenses](https://github.com/Kataglyphis/ANTfrastructure/blob/develop/docs/third-party-licenses.md#documentation-image-pandoc_all),
under *Documentation Image (`pandoc_all`)*. It vendors this repository as a submodule and holds
the image's Pandoc and uv pins; the image itself is built locally with `nerdctl build`, by no
workflow.

`PANDOC_VERSION` and `UV_VERSION` in the `Dockerfile` are ARG defaults synced from
ANTfrastructure's `linux/scripts/01-core/versions.env`. Bump them there, not in the `Dockerfile`,
and run `python3 docs/scripts/sync_versions.py --write` **in the ANTfrastructure checkout** (the
script lives there, not here). It rewrites the copy in that checkout's
`third_party/DocumANTation` submodule, and the bump is committed here from there.

This repository is the single source of the shared Kataglyphis docs theme
(`sphinx-kataglyphis-theme/`) and docs tooling (`docs-tooling/`), which downstream repositories
consume as a submodule.

Contributing, the licence (MIT) and contact are the family's: [repository-family.md](https://github.com/Kataglyphis/ANTfrastructure/blob/develop/docs/repository-family.md).
