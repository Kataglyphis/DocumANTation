#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
CONTAINER_RUNTIME="${CONTAINER_RUNTIME:-nerdctl}"
IMAGE="${IMAGE:-pandoc_all}"
STRICT_WARNINGS="${STRICT_WARNINGS:-0}"

usage() {
    printf 'Usage: %s <book|diss|beamer|pptx|cv>\n' "$0" >&2
    printf 'Environment: CONTAINER_RUNTIME=<nerdctl|docker> IMAGE=<container-image> STRICT_WARNINGS=0|1\n' >&2
    exit 2
}

if [ $# -ne 1 ]; then
    usage
fi

TARGET="$1"

case "$TARGET" in
    book|diss)
        CMD='. md2pdf/bin/activate && chmod +x /md2pdfLib/scripts/compile_with_glossaries.sh && /md2pdfLib/scripts/compile_with_glossaries.sh'
        if [ "$STRICT_WARNINGS" = "1" ]; then
            CMD+=" --strict-warnings"
        fi
        CMD+=" --type ${TARGET}"
        ;;
    beamer)
        CMD='. md2pdf/bin/activate && chmod +x /md2pdfLib/presentation/scripts/update_own_sty.sh && /md2pdfLib/presentation/scripts/update_own_sty.sh && uv run python /md2pdfLib/build.py beamer'
        if [ "$STRICT_WARNINGS" = "1" ]; then
            CMD+=' && uv run python /md2pdfLib/check_build_log.py /data/out/beamer.json --format pandoc-json'
        fi
        ;;
    pptx)
        # The reference deck carries the brand for pptx and is generated from
        # brand.json here, every build, rather than committed as a binary.
        CMD='. md2pdf/bin/activate && uv run python /md2pdfLib/presentation/pptx/make_reference.py /data/out/reference.pptx && uv run python /md2pdfLib/build.py pptx'
        if [ "$STRICT_WARNINGS" = "1" ]; then
            CMD+=' && uv run python /md2pdfLib/check_build_log.py /data/out/pptx.json --format pandoc-json'
        fi
        ;;
    cv)
        CMD='. md2pdf/bin/activate && cd /data/cv && lualatex -interaction=nonstopmode -halt-on-error cv.tex && lualatex -interaction=nonstopmode -halt-on-error cv.tex'
        if [ "$STRICT_WARNINGS" = "1" ]; then
            CMD+=' && uv run python /md2pdfLib/check_build_log.py /data/cv/cv.log --format latex'
        fi
        ;;
    *)
        usage
        ;;
esac

# Put the brand snippets on the LaTeX search path so documents can say
# \input{brand-colors.tex} without knowing where the style directory sits
# relative to their build directory. A project consuming this repo as a
# submodule points TEXINPUTS at its own checkout the same way. The trailing
# colon keeps the default search path.
BRAND_TEXINPUTS="/md2pdfLib/style:"

"${CONTAINER_RUNTIME}" run --rm \
  --entrypoint "" \
  -e "TEXINPUTS=${BRAND_TEXINPUTS}" \
  -v "${PROJECT_ROOT}/md2pdfLib:/md2pdfLib" \
  -v "${PROJECT_ROOT}/data:/data" \
  "$IMAGE" \
  sh -c "$CMD"
