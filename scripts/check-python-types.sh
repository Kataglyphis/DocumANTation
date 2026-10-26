#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
hub_root="${ANTFRASTRUCTURE_DIR:-${repo_root}/antfrastructure-tools}"
[[ -f "${hub_root}/linux/scripts/01-core/lint-root.sh" ]] || {
  printf 'ANTfrastructure tracked-file helper is missing: %s\n' "${hub_root}" >&2
  exit 2
}
# shellcheck source=/dev/null
source "${hub_root}/linux/scripts/01-core/lint-root.sh"

report_dir="${repo_root}/logs/code-quality"
mkdir -p "${report_dir}"
tracked_list="${report_dir}/ty-tracked-files.z"
lint_root_tracked "${repo_root}" 'md2pdfLib/*.py' 'style/*.py' \
  'sphinx-kataglyphis-theme/*.py' > "${tracked_list}"
mapfile -d '' -t python_files < "${tracked_list}"
[[ "${#python_files[@]}" -gt 0 ]] || {
  printf 'No tracked Python files in the type-check scope\n' >&2
  exit 2
}

cd "${repo_root}"
uv run --locked --extra dev ty check -- "${python_files[@]}"
