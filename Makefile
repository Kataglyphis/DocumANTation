.PHONY: book diss beamer pptx cv cv-all

IMAGE ?= pandoc_all
STRICT_WARNINGS ?= 0
# cv only: english (default) or german. Both come from the same sources.
CV_LANG ?= english

book diss beamer pptx cv:
	IMAGE="$(IMAGE)" STRICT_WARNINGS="$(STRICT_WARNINGS)" CV_LANG="$(CV_LANG)" ./scripts/build_in_container.sh $@

# Both published CV variants, the pair linked from jonasheinle.de.
cv-all:
	$(MAKE) cv CV_LANG=english
	$(MAKE) cv CV_LANG=german

# There is deliberately no standalone update-sty target: the theme refresh
# (md2pdfLib/presentation/scripts/update_own_sty.sh) only makes sense inside a
# build container, and the beamer target already runs it there. Run standalone
# in a --rm container, its texmf changes were discarded with the container.
