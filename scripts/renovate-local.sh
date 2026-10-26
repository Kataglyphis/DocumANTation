#!/usr/bin/env bash
# DocumANTation cannot vendor ANTfrastructure because the hub already vendors this repo.
set -euo pipefail

_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
_REPO_ROOT="$(cd "${_SCRIPT_DIR}/.." && pwd)"

if [ -z "${ANTFRASTRUCTURE_DIR:-}" ]; then
  if [ -f "${_REPO_ROOT}/antfrastructure-tools/linux/scripts/renovate-local.sh" ]; then
    ANTFRASTRUCTURE_DIR="${_REPO_ROOT}/antfrastructure-tools"
  elif [ -f "${_REPO_ROOT}/../ANTfrastructure/linux/scripts/renovate-local.sh" ]; then
    ANTFRASTRUCTURE_DIR="${_REPO_ROOT}/../ANTfrastructure"
  else
    _ANTFRASTRUCTURE_TMP="$(mktemp -d)"
    trap 'rm -rf -- "${_ANTFRASTRUCTURE_TMP}"' EXIT
    _GITHUB_HOME="$(python3 -c \
      'import json,sys; print(json.load(open(sys.argv[1], encoding="utf-8"))["identity"]["github_url"])' \
      "${_REPO_ROOT}/style/brand.json")"
    git clone --quiet --depth 1 --single-branch --branch develop --no-recurse-submodules \
      "${_GITHUB_HOME}/ANTfrastructure.git" "${_ANTFRASTRUCTURE_TMP}/ANTfrastructure"
    ANTFRASTRUCTURE_DIR="${_ANTFRASTRUCTURE_TMP}/ANTfrastructure"
  fi
fi

if [ ! -f "${ANTFRASTRUCTURE_DIR}/linux/scripts/renovate-local.sh" ]; then
  printf 'ANTfrastructure checkout not found at %s; set ANTFRASTRUCTURE_DIR to its path.\n' "${ANTFRASTRUCTURE_DIR}" >&2
  exit 1
fi

bash "${ANTFRASTRUCTURE_DIR}/linux/scripts/renovate-local.sh" "${_REPO_ROOT}" "$@"
