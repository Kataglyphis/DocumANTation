#!/usr/bin/env bash
# Update the Beamer .sty files in the local TeX tree.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET_DIR="${TEXMFHOME:-$HOME/texmf}/tex/latex/commonstuff"
SOURCE_DIR="${SCRIPT_DIR}/../template/latex"

echo "==> Removing old .sty files..."
rm -rf "${TARGET_DIR:?}/awesome-beamer" "${TARGET_DIR:?}/smile"
rm -f "${TARGET_DIR:?}/beamerthemeawesome.sty" "${TARGET_DIR:?}/smile.sty"

echo "==> Creating target directory..."
mkdir -p "${TARGET_DIR}"

echo "==> Copying updated .sty files..."
cp -r "${SOURCE_DIR}/awesome-beamer" "${TARGET_DIR}/"
cp -r "${SOURCE_DIR}/smile" "${TARGET_DIR}/"
cp "${SOURCE_DIR}/awesome-beamer/beamerthemeawesome.sty" "${TARGET_DIR}/"
cp "${SOURCE_DIR}/smile/smile.sty" "${TARGET_DIR}/"

echo "==> Updating TeX file database..."
texhash

echo "==> Update complete."
