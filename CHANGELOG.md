# Changelog

## Unreleased

- Scope the Linux Ruff lint and format gate to tracked project Python through ANTfrastructure's
  shared helper, so recursive theme submodules cannot break this repository's gate.
- Add a local Renovate command that uses a separate ANTfrastructure checkout and documents
  the currently branchless theme submodules.
- Add shared size, complexity, duplication and Ruff/ty reports in CI, plus a manual Python
  refactor preview. The workflows check out ANTfrastructure separately to avoid a submodule
  cycle; generated local reports stay in ignored `logs/`.
