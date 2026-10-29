#!/usr/bin/env bash
# build-theme-dist.sh <out-dir> [python]: the theme's sdist and wheel, built from the sdist and checked.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
theme="${repo_root}/sphinx-kataglyphis-theme"
out="${1:?usage: build-theme-dist.sh <out-dir> [python]}"
python="${2:-python3}"

rm -rf "${out:?}"
mkdir -p "${out}"
uv build --python "${python}" --out-dir "${out}" "${theme}"

version="$(tr -d '[:space:]' < "${theme}/VERSION.txt")"
wheel="${out}/sphinx_kataglyphis_theme-${version}-py3-none-any.whl"
sdist="${out}/sphinx_kataglyphis_theme-${version}.tar.gz"
for artifact in "${wheel}" "${sdist}"; do
  [[ -f "${artifact}" ]] || {
    printf 'build-theme-dist: %s was not built\n' "${artifact}" >&2
    exit 1
  }
done

# Consumers read these files from the installed wheel, so a missing one must fail the release, not their docs build.
"${python}" - "${wheel}" <<'EOF'
import sys
import zipfile

names = set(zipfile.ZipFile(sys.argv[1]).namelist())
required = [
    "sphinx_kataglyphis/__init__.py",
    "sphinx_kataglyphis/highlight.py",
    "sphinx_kataglyphis/brand.tokens.json",
    "sphinx_kataglyphis/dartdoc.css",
    "sphinx_kataglyphis/_static/css/custom.css",
    "sphinx_kataglyphis/logo-t3-wireframe.png",
]
missing = [name for name in required if name not in names]
if not any(name.endswith(".dist-info/licenses/LICENSE") for name in names):
    missing.append("*.dist-info/licenses/LICENSE")
if missing:
    sys.exit(f"build-theme-dist: the wheel lacks {missing}")
print(f"build-theme-dist: {sys.argv[1]} carries every file consumers read")
EOF
