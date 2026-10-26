# Changelog

## Unreleased

- Search local submodules and the separate ANTfrastructure checkout before adding Bash or
  PowerShell behavior; extend the shared owner for functionality used by other consumers.
- Scope the Linux Ruff lint, format and ty gates to tracked project Python through
  ANTfrastructure's shared helpers, so recursive theme submodules cannot break the gates.
- Add a local Renovate command that uses a separate ANTfrastructure checkout and documents
  the currently branchless theme submodules.
- Add shared size, complexity, duplication and Ruff/ty reports in CI, plus a manual Python
  refactor preview. The workflows check out ANTfrastructure separately to avoid a submodule
  cycle; generated local reports stay in ignored `logs/`.
