#!/usr/bin/env bash
# DocumANTation cannot vendor ANTfrastructure because the hub already vendors this repo.
set -euo pipefail

_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
_REPO_ROOT="$(cd "${_SCRIPT_DIR}/.." && pwd)"

if [ -z "${ANTFRASTRUCTURE_DIR:-}" ]; then
  if [ -d "${_REPO_ROOT}/antfrastructure-tools" ]; then
    ANTFRASTRUCTURE_DIR="${_REPO_ROOT}/antfrastructure-tools"
  else
    ANTFRASTRUCTURE_DIR="${_REPO_ROOT}/../ANTfrastructure"
  fi
fi

if [ ! -f "${ANTFRASTRUCTURE_DIR}/linux/scripts/renovate-local.sh" ]; then
  printf 'ANTfrastructure checkout not found at %s; set ANTFRASTRUCTURE_DIR to its path.\n' "${ANTFRASTRUCTURE_DIR}" >&2
  exit 1
fi

exec bash "${ANTFRASTRUCTURE_DIR}/linux/scripts/renovate-local.sh" "${_REPO_ROOT}" "$@"
