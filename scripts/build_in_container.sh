#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
CONTAINER_RUNTIME="${CONTAINER_RUNTIME:-nerdctl}"
IMAGE="${IMAGE:-pandoc_all}"
STRICT_WARNINGS="${STRICT_WARNINGS:-0}"
CV_LANG="${CV_LANG:-english}"
# CV section set and summary, one file per target; see data/cv/profiles/README.md.
CV_PROFILE="${CV_PROFILE:-default}"
# Replaces CV_LANG in the basename of a tailored CV; the name half never comes from the caller.
CV_JOB_SUFFIX="${CV_JOB_SUFFIX:-}"

# The author name comes from the brand; identity is last in the tokens, so this skips brand.name.
BRAND_TOKENS="${PROJECT_ROOT}/style/brand.tokens.json"
identity_value() {
    sed -n '/"identity"/,$p' "$BRAND_TOKENS" \
        | sed -n "s/.*\"$1\"[[:space:]]*:[[:space:]]*\"\([^\"]*\)\".*/\1/p" \
        | head -1
}

usage() {
    printf 'Usage: %s <book|beamer|demo|example|pptx|cv|letter>\n' "$0" >&2
    printf '       letter: the cover letter data/cv/letters/<CV_PROFILE>.tex, typeset with that CV profile\n' >&2
    printf 'Environment: CONTAINER_RUNTIME=<nerdctl|docker> IMAGE=<container-image> STRICT_WARNINGS=0|1\n' >&2
    printf '             CV_LANG=<english|german>          (cv target only)\n' >&2
    printf '             CV_PROFILE=<data/cv/profiles/*>   (cv target only, default: default)\n' >&2
    printf '             CV_JOB_SUFFIX=<tag>               (cv target only, default: the language)\n' >&2
    printf '             CV_JOB=<output basename>          (cv target only, overrides both)\n' >&2
    exit 2
}

if [ $# -ne 1 ]; then
    usage
fi

# The strict gate's condition, written once; book passes --strict-warnings to its own script instead.
strict_step() {
    if [ "$STRICT_WARNINGS" = "1" ]; then
        CMD+=" && $1"
    fi
}

TARGET="$1"

case "$TARGET" in
    book)
        CMD='. md2pdf/bin/activate && chmod +x /md2pdfLib/scripts/compile_with_glossaries.sh && /md2pdfLib/scripts/compile_with_glossaries.sh'
        if [ "$STRICT_WARNINGS" = "1" ]; then
            CMD+=" --strict-warnings"
        fi
        CMD+=" --type book"
        ;;
    beamer|demo)
        # demo is the showcase deck (presets.demo); both need the beamer themes in texmf.
        CMD='. md2pdf/bin/activate && chmod +x /md2pdfLib/presentation/scripts/update_own_sty.sh && /md2pdfLib/presentation/scripts/update_own_sty.sh'
        CMD+=" && uv run python /md2pdfLib/build.py ${TARGET}"
        strict_step "uv run python /md2pdfLib/check_build_log.py /data/out/${TARGET}.json --format pandoc-json"
        ;;
    example)
        # The starter document: one pandoc call, no glossary/bibliography pass.
        CMD='. md2pdf/bin/activate && uv run python /md2pdfLib/build.py example'
        strict_step "uv run python /md2pdfLib/check_build_log.py /data/out/example.json --format pandoc-json"
        ;;
    pptx)
        # finalize_deck.py is not a strict step: every deck needs the layout media pandoc drops.
        CMD='. md2pdf/bin/activate && uv run python /md2pdfLib/presentation/pptx/make_reference.py /data/out/reference.pptx && uv run python /md2pdfLib/build.py pptx && uv run python /md2pdfLib/presentation/pptx/finalize_deck.py /data/out/presentation.pptx'
        strict_step "uv run python /md2pdfLib/check_build_log.py /data/out/pptx.json --format pandoc-json"
        # The log gate cannot see a clean build that came out off-brand, so check the deck.
        strict_step "uv run python /md2pdfLib/presentation/pptx/verify_brand.py /data/out/presentation.pptx"
        ;;
    cv|letter)
        # letter is the CV document with a letter body: only \cvletter and the prefix differ.
        case "$CV_LANG" in
            english|german) ;;
            *)
                printf 'Unknown CV_LANG "%s" (expected english or german)\n' "$CV_LANG" >&2
                exit 2
                ;;
        esac
        # The job name is the published filename, so the CV is a build output, not a committed binary.
        if [ ! -f "${PROJECT_ROOT}/data/cv/profiles/${CV_PROFILE}.tex" ]; then
            printf 'Unknown CV_PROFILE "%s": data/cv/profiles/%s.tex does not exist\n' \
                "$CV_PROFILE" "$CV_PROFILE" >&2
            exit 2
        fi
        CV_PREFIX="CV"
        if [ "$TARGET" = "letter" ]; then
            if [ ! -f "${PROJECT_ROOT}/data/cv/letters/${CV_PROFILE}.tex" ]; then
                printf 'No cover letter for CV_PROFILE "%s": data/cv/letters/%s.tex does not exist\n' \
                    "$CV_PROFILE" "$CV_PROFILE" >&2
                exit 2
            fi
            CV_PREFIX="Cover_Letter"
        fi
        # The tag is set with the profile (see the Makefile), never derived from its slug.
        CV_NAME="$(identity_value first_name)_$(identity_value last_name)"
        if [ "$CV_NAME" = "_" ]; then
            printf 'Could not read the author name from %s\n' "$BRAND_TOKENS" >&2
            printf 'Run: python style/generate_style.py --write\n' >&2
            exit 1
        fi
        CV_JOB="${CV_JOB:-${CV_PREFIX}_${CV_NAME}_${CV_JOB_SUFFIX:-$CV_LANG}}"
        # Language and profile go in as class option and \def, so cv.tex needs no edit.
        CV_ARG="\\def\\cvprofile{${CV_PROFILE}}"
        if [ "$TARGET" = "letter" ]; then
            CV_ARG="${CV_ARG}\\def\\cvletter{${CV_PROFILE}}"
        fi
        CV_ARG="${CV_ARG}\\PassOptionsToClass{${CV_LANG}}{myCV_METADATA}\\input{cv.tex}"
        CV_RUN="lualatex -interaction=nonstopmode -halt-on-error"
        CV_RUN+=" -output-directory=/data/out -jobname=${CV_JOB} '${CV_ARG}'"
        # Twice: the second pass resolves the hyperref bookmarks written by the first.
        CMD=". md2pdf/bin/activate && mkdir -p /data/out && cd /data/cv"
        CMD+=" && ${CV_RUN} && ${CV_RUN}"
        strict_step "uv run python /md2pdfLib/check_build_log.py /data/out/${CV_JOB}.log --format latex"
        ;;
    *)
        usage
        ;;
esac

# Brand snippets and classes resolve by name from anywhere; the trailing colon keeps the default path.
BRAND_TEXINPUTS="/md2pdfLib/style:/md2pdfLib/cv/template/latex:/md2pdfLib/common/latex:"

"${CONTAINER_RUNTIME}" run --rm \
  --entrypoint "" \
  -e "TEXINPUTS=${BRAND_TEXINPUTS}" \
  -v "${PROJECT_ROOT}/md2pdfLib:/md2pdfLib" \
  -v "${PROJECT_ROOT}/data:/data" \
  "$IMAGE" \
  sh -c "$CMD"
