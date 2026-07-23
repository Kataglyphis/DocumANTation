#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
CONTAINER_RUNTIME="${CONTAINER_RUNTIME:-nerdctl}"
IMAGE="${IMAGE:-pandoc_all}"
STRICT_WARNINGS="${STRICT_WARNINGS:-0}"
CV_LANG="${CV_LANG:-english}"

usage() {
    printf 'Usage: %s <book|beamer|pptx|cv>\n' "$0" >&2
    printf 'Environment: CONTAINER_RUNTIME=<nerdctl|docker> IMAGE=<container-image> STRICT_WARNINGS=0|1\n' >&2
    printf '             CV_LANG=<english|german>  (cv target only)\n' >&2
    exit 2
}

if [ $# -ne 1 ]; then
    usage
fi

TARGET="$1"

case "$TARGET" in
    book)
        CMD='. md2pdf/bin/activate && chmod +x /md2pdfLib/scripts/compile_with_glossaries.sh && /md2pdfLib/scripts/compile_with_glossaries.sh'
        if [ "$STRICT_WARNINGS" = "1" ]; then
            CMD+=" --strict-warnings"
        fi
        CMD+=" --type book"
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
        # finalize_deck.py runs unconditionally: pandoc drops media that only
        # slide layouts reference, so the title background must be re-attached
        # to every emitted deck, not just strict-checked ones.
        CMD='. md2pdf/bin/activate && uv run python /md2pdfLib/presentation/pptx/make_reference.py /data/out/reference.pptx && uv run python /md2pdfLib/build.py pptx && uv run python /md2pdfLib/presentation/pptx/finalize_deck.py /data/out/presentation.pptx'
        if [ "$STRICT_WARNINGS" = "1" ]; then
            CMD+=' && uv run python /md2pdfLib/check_build_log.py /data/out/pptx.json --format pandoc-json'
            # The log gate only sees what pandoc complains about. A deck that
            # builds cleanly and comes out stock Office blue would pass it, so
            # check the artifact itself.
            CMD+=' && uv run python /md2pdfLib/presentation/pptx/verify_brand.py /data/out/presentation.pptx'
        fi
        ;;
    cv)
        case "$CV_LANG" in
            english|german) ;;
            *)
                printf 'Unknown CV_LANG "%s" (expected english or german)\n' "$CV_LANG" >&2
                exit 2
                ;;
        esac
        # The job name is the filename the CV is published under on
        # jonasheinle.de (data/book/chapters/23-about-me.md links to it), so
        # the deliverable is a reproducible build output rather than a binary
        # someone has to remember to re-commit. Output goes to /data/out like
        # every other target, which keeps aux/log/pdf out of the source tree.
        CV_JOB="CV_Jonas_Heinle_${CV_LANG}"
        # Selects the language without editing cv.tex; see the class options.
        CV_ARG="\\PassOptionsToClass{${CV_LANG}}{myCV_METADATA}\\input{cv.tex}"
        CV_RUN="lualatex -interaction=nonstopmode -halt-on-error"
        CV_RUN+=" -output-directory=/data/out -jobname=${CV_JOB} '${CV_ARG}'"
        # Twice: the second pass resolves the hyperref bookmarks written by the first.
        CMD=". md2pdf/bin/activate && mkdir -p /data/out && cd /data/cv"
        CMD+=" && ${CV_RUN} && ${CV_RUN}"
        if [ "$STRICT_WARNINGS" = "1" ]; then
            CMD+=" && uv run python /md2pdfLib/check_build_log.py /data/out/${CV_JOB}.log --format latex"
        fi
        ;;
    *)
        usage
        ;;
esac

# Put the brand snippets, shared environments and the document classes on the
# LaTeX search path so documents can say \input{brand-colors.tex},
# \input{brand-cv.tex} or \documentclass{myCV_METADATA} without knowing where
# those live relative to their build directory. A project consuming this repo
# as a submodule points TEXINPUTS at its own checkout the same way. The
# trailing colon keeps the default search path.
BRAND_TEXINPUTS="/md2pdfLib/style:/md2pdfLib/cv/template/latex:/md2pdfLib/common/latex:"

"${CONTAINER_RUNTIME}" run --rm \
  --entrypoint "" \
  -e "TEXINPUTS=${BRAND_TEXINPUTS}" \
  -v "${PROJECT_ROOT}/md2pdfLib:/md2pdfLib" \
  -v "${PROJECT_ROOT}/data:/data" \
  "$IMAGE" \
  sh -c "$CMD"
