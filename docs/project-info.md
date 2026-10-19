# Project Information

## Development Tooling

- `uv` manages local Python environments and command execution.
- `ruff` provides linting and formatting checks.
- `ty` provides static type checks for the Python build logic.
- Sphinx builds the repository documentation site.

## External Dependencies

Everything the builds need ships in the `pandoc_all` container image, chiefly
`pandoc` for Markdown conversion and TeX Live/LuaLaTeX for PDF generation, plus
the `awesome-beamer` and `smile` presentation-theme submodules.

The full list, with the version, upstream and license of each component, is
maintained in **ANTfrastructure**, which vendors this repository as a submodule
and holds the image's Pandoc and uv pins (the image itself is built locally with
`nerdctl build`; no workflow builds it) — see
[Third-Party Software & Licenses](https://github.com/Kataglyphis/ANTfrastructure/blob/develop/docs/third-party-licenses.md#documentation-image-pandoc_all),
under *Documentation Image (`pandoc_all`)*.

`PANDOC_VERSION` and `UV_VERSION` in the `Dockerfile` are ARG defaults synced
from ANTfrastructure's `linux/scripts/01-core/versions.env`; bump them there and
run `python3 docs/scripts/sync_versions.py --write` **in the ANTfrastructure
checkout** (the script lives there, not in this repo), not by editing the
`Dockerfile`. The script rewrites the copy in that checkout's
`third_party/DocumANTation` submodule, so the bump is then committed here from
there.

This repository is also the single source of truth for the shared Kataglyphis
docs theme (`sphinx-kataglyphis-theme/`) and docs tooling (`docs-tooling/`),
which downstream repositories consume as a submodule.

Contributing, the licence (MIT) and contact are the family's: [repository-family.md](https://github.com/Kataglyphis/ANTfrastructure/blob/develop/docs/repository-family.md).
