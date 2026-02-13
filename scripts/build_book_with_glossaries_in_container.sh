#!/usr/bin/env bash
set -euo pipefail

IMAGE="ghcr.io/kataglyphis/kataglyphis_md2pdf"

# Run the book build inside the container, with the repo folders mounted.
# NOTE: The image ENTRYPOINT always starts an interactive bash and ignores extra args.
# We override the entrypoint here so we can run a non-interactive command.
docker run --rm \
  -v "${PWD}/md2pdfLib:/md2pdfLib" \
  -v "${PWD}/data:/data" \
  -h mypandoc \
  --entrypoint /bin/bash \
  "$IMAGE" \
  -lc ". /md2pdf/bin/activate && chmod +x /md2pdfLib/book/scripts/compile_with_glossaries_and_nomenclature.sh && /md2pdfLib/book/scripts/compile_with_glossaries_and_nomenclature.sh"
