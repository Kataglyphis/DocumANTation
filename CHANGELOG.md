# Changelog

## Unreleased

- Clear every quality ratchet without allowlist entries, and run the lint gates on every push and
  pull request instead of only by hand. `build_reference` and `patch_content_layout` split into
  named steps (the reference deck stays byte-identical); the Dart docs' layout CSS moves out of
  `generate_style.py` into the hand-written `style/dartdoc-layout.css` (every generated file
  unchanged); the title background is re-encoded at 1350×3000 (392 KiB instead of 1.5 MB, same
  aspect, so the pptx crop holds) without its camera EXIF, which carried GPS coordinates. A test
  now fails any tracked JPEG or PNG that carries EXIF.
- Pin smile at ae4926c and awesome-beamer at 4c5fc05, which drop their ANTfrastructure submodules and
  call the hub's workflows with `hub-checkout: true`; a recursive clone of ANTfrastructure or
  DocumANTation now ends.
- Move `setup-uv` to v10.3.2 and refresh `uv.lock` (sphinx 9.2.0, pytest 9.2.0, ty 0.0.92,
  coverage 7.17.0, sphinxcontrib-jsmath 2.0.0) through the hub's local Renovate run; ruff stays at
  the hub's `RUFF_VERSION` until the hub moves it.
- Ship the MIT LICENSE inside the sphinx-kataglyphis-theme wheel and sdist; the theme now declares
  `license = "MIT"` with `license-files`, and a test holds its copy equal to the root LICENSE.
- Search local submodules and the separate ANTfrastructure checkout before adding Bash or
  PowerShell behavior; extend the shared owner for functionality used by other consumers.
- Scope the Linux Ruff lint, format and ty gates to tracked project Python through
  ANTfrastructure's shared helpers, so recursive theme submodules cannot break the gates.
- Add a local Renovate command that uses a separate ANTfrastructure checkout and documents
  the currently branchless theme submodules.
- Add shared size, complexity, duplication and Ruff/ty reports in CI, plus a manual Python
  refactor preview. The workflows check out ANTfrastructure separately to avoid a submodule
  cycle; generated local reports stay in ignored `logs/`.
