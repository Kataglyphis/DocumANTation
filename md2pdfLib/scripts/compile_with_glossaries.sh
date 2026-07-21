#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# compile_with_glossaries.sh – LaTeX compilation with glossary support.
#
# Usage:
#   compile_with_glossaries.sh [--strict-warnings] --type book|diss
#   compile_with_glossaries.sh [--strict-warnings] <python-script> <output-name> [log-name]
# ---------------------------------------------------------------------------
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${PROJECT_ROOT}"

usage() {
    echo "Usage: $0 [--strict-warnings] --type <book|diss> [log-name]" >&2
    echo "   or: $0 [--strict-warnings] <python-script> <output-name> [log-name]" >&2
    exit 2
}

STRICT_WARNINGS=0
TYPE=""
POSITIONAL=()

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
        -h|--help)
            usage
            ;;
        *)
            POSITIONAL+=("$1")
            shift
            ;;
    esac
done

if [ -n "$TYPE" ]; then
    if [ ${#POSITIONAL[@]} -gt 1 ]; then
        usage
    fi
    case "$TYPE" in
        book)
            MD2PDF_CMD=(python md2pdfLib/build.py book)
            OUTPUT_NAME="book_output"
            ;;
        diss)
            MD2PDF_CMD=(python md2pdfLib/build.py diss)
            OUTPUT_NAME="diss_output"
            ;;
        *)
            echo "Unknown type: ${TYPE}" >&2
            exit 2
            ;;
    esac
else
    if [ ${#POSITIONAL[@]} -lt 2 ] || [ ${#POSITIONAL[@]} -gt 3 ]; then
        usage
    fi
    MD2PDF_SCRIPT="${POSITIONAL[0]}"
    OUTPUT_NAME="${POSITIONAL[1]}"
    read -r -a MD2PDF_CMD <<< "${MD2PDF_SCRIPT}"
fi

# The pandoc log must NOT be named ${OUTPUT_NAME}.log: lualatex runs with
# -output-directory="${OUTPUT_DIR}" and writes ${OUTPUT_NAME}.log there, which
# used to overwrite the teed pandoc output on the first pass -- so pandoc's own
# warnings were silently lost and the strict gate only ever saw LaTeX's log.
if [ -n "$TYPE" ]; then
    LOG_NAME="${POSITIONAL[0]:-${OUTPUT_NAME}.pandoc.log}"
else
    LOG_NAME="${POSITIONAL[2]:-${OUTPUT_NAME}.pandoc.log}"
fi
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

if [ "${STRICT_WARNINGS}" -eq 1 ]; then
    echo "=== Step 8: Check final logs for warnings ==="
    # Both stages can warn independently: pandoc about the conversion (missing
    # resources, duplicate identifiers), LaTeX about the typesetting.
    uv run python md2pdfLib/check_build_log.py "${OUTPUT_DIR}/${LOG_NAME}" --format latex
    uv run python md2pdfLib/check_build_log.py "${OUTPUT_DIR}/${OUTPUT_NAME}.log" --format latex
fi

echo "=== Done: ${OUTPUT_DIR}/${OUTPUT_PDF} ==="
