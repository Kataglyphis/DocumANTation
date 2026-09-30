#!/usr/bin/env bash
# compile_with_glossaries.sh [--strict-warnings] --type book - the full LuaLaTeX pipeline with glossaries.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${PROJECT_ROOT}"

usage() {
    echo "Usage: $0 [--strict-warnings] --type <book>" >&2
    exit 2
}

STRICT_WARNINGS=0
TYPE=""

while [ $# -gt 0 ]; do
    case "$1" in
        --strict-warnings)
            STRICT_WARNINGS=1
            shift
            ;;
        --type)
            TYPE="${2:-}"
            if [ -z "$TYPE" ]; then
                usage
            fi
            shift 2
            ;;
        -h|--help|*)
            usage
            ;;
    esac
done

case "$TYPE" in
    book)
        MD2PDF_CMD=(python md2pdfLib/build.py book)
        OUTPUT_NAME="book_output"
        ;;
    *)
        usage
        ;;
esac

# Not ${OUTPUT_NAME}.log: lualatex writes that name into the same directory and would overwrite it.
LOG_NAME="${OUTPUT_NAME}.pandoc.log"
OUTPUT_DIR="data/out"
OUTPUT_TEX="${OUTPUT_NAME}.tex"
OUTPUT_PDF="${OUTPUT_NAME}.pdf"
LATEX_ARGS=(-interaction=nonstopmode -halt-on-error -output-directory="${OUTPUT_DIR}")

mkdir -p "${OUTPUT_DIR}"

echo "=== Step 1: Generate .tex from markdown ==="
uv run "${MD2PDF_CMD[@]}" "${OUTPUT_TEX}" 2>&1 | tee "${OUTPUT_DIR}/${LOG_NAME}"

echo "=== Step 2: First lualatex pass ==="
lualatex "${LATEX_ARGS[@]}" "${OUTPUT_DIR}/${OUTPUT_TEX}"

echo "=== Step 3: Bibliography (biber) ==="
(cd "${OUTPUT_DIR}" && biber --input-directory="${PROJECT_ROOT}" "${OUTPUT_NAME}")

echo "=== Step 4: Glossary (makeglossaries) ==="
(cd "${OUTPUT_DIR}" && makeglossaries "${OUTPUT_NAME}")

echo "=== Step 5: Nomenclature (makeindex) ==="
if [ -f "${OUTPUT_DIR}/${OUTPUT_NAME}.nlo" ]; then
    (cd "${OUTPUT_DIR}" && makeindex "${OUTPUT_NAME}.nlo" -s nomencl.ist -o "${OUTPUT_NAME}.nls")
else
    echo "  (no .nlo file – skipping)"
fi

echo "=== Step 6: Second lualatex pass ==="
lualatex "${LATEX_ARGS[@]}" "${OUTPUT_DIR}/${OUTPUT_TEX}"

echo "=== Step 7: Third lualatex pass ==="
lualatex "${LATEX_ARGS[@]}" "${OUTPUT_DIR}/${OUTPUT_TEX}"

# Advisory only: they cost quality but lose nothing, and a loose line depends on where prose wraps.
LATEX_ADVISORIES=(
    --advisory-regex '^\s*Underfull \\hbox'
    --advisory-regex 'Package tcolorbox Warning: Using nobreak failed'
)

if [ "${STRICT_WARNINGS}" -eq 1 ]; then
    echo "=== Step 8: Check final logs for warnings ==="
    # The pandoc log gets no advisories: it carries no box diagnostics.
    uv run python md2pdfLib/check_build_log.py "${OUTPUT_DIR}/${LOG_NAME}" --format latex
    uv run python md2pdfLib/check_build_log.py "${OUTPUT_DIR}/${OUTPUT_NAME}.log" \
        --format latex "${LATEX_ADVISORIES[@]}"
fi

echo "=== Done: ${OUTPUT_DIR}/${OUTPUT_PDF} ==="
