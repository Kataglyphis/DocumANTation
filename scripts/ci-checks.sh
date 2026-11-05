#!/usr/bin/env bash
# The linux-x64.yml checks, on the interpreter ANTfrastructure's ci-image-leg.sh bound; the pandoc tests need the version the Dockerfile pins.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
hub_root="${ANTFRASTRUCTURE_DIR:-${repo_root}/antfrastructure-tools}"
cd "${repo_root}"

uv run --locked python style/generate_style.py --check
bash "${hub_root}/linux/scripts/refactor-python.sh" --root "${repo_root}" --check
bash scripts/check-python-types.sh
git ls-files -z '*.sh' | xargs -0 uv run --locked --extra dev shellcheck

pandoc_version="$(sed -n 's/^ARG PANDOC_VERSION=//p' Dockerfile)"
pandoc_sha="$(sed -n 's/^ARG PANDOC_SHA256_AMD64=//p' Dockerfile)"
[ -n "${pandoc_version}" ] && [ -n "${pandoc_sha}" ] || { printf 'the Dockerfile pins no pandoc\n' >&2; exit 2; }
pandoc_dir="$(mktemp -d)"
curl --proto '=https' --tlsv1.2 -fsSL --retry 3 -o "${pandoc_dir}/pandoc.deb" \
  "https://github.com/jgm/pandoc/releases/download/${pandoc_version}/pandoc-${pandoc_version}-1-amd64.deb"
printf '%s  %s\n' "${pandoc_sha}" "${pandoc_dir}/pandoc.deb" | sha256sum -c -
dpkg-deb -x "${pandoc_dir}/pandoc.deb" "${pandoc_dir}/root"
PATH="${pandoc_dir}/root/usr/bin:${PATH}"
pandoc --version | head -1

uv run --locked --extra dev pytest tests/ -q
