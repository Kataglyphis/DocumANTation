.PHONY: book beamer pptx cv cv-all watch-beamer watch-book watch-cv

IMAGE ?= pandoc_all
STRICT_WARNINGS ?= 0
# cv only: english (default) or german. Both come from the same sources.
CV_LANG ?= english

book beamer pptx cv:
	IMAGE="$(IMAGE)" STRICT_WARNINGS="$(STRICT_WARNINGS)" CV_LANG="$(CV_LANG)" ./scripts/build_in_container.sh $@

# Both published CV variants, the pair linked from jonasheinle.de.
cv-all:
	$(MAKE) cv CV_LANG=english
	$(MAKE) cv CV_LANG=german

# Live-demo mode: rebuild on every source change. Requires `entr`
# (apt install entr / brew install entr). Pair with a PDF viewer that
# auto-reloads (zathura, evince, skim) for a live editing experience.
watch-beamer:
	@command -v entr >/dev/null 2>&1 || { echo "entr not found — install with: apt install entr / brew install entr"; exit 1; }
	@echo "Watching data/presentation/**/*.md — rebuilds on every change"
	find data/presentation -name '*.md' | entr -c $(MAKE) beamer

watch-book:
	@command -v entr >/dev/null 2>&1 || { echo "entr not found — install with: apt install entr / brew install entr"; exit 1; }
	@echo "Watching data/book/**/*.md — rebuilds on every change"
	find data/book -name '*.md' | entr -c $(MAKE) book

watch-cv:
	@command -v entr >/dev/null 2>&1 || { echo "entr not found — install with: apt install entr / brew install entr"; exit 1; }
	@echo "Watching data/cv/**/*.tex — rebuilds on every change"
	find data/cv -name '*.tex' | entr -c $(MAKE) cv

# There is deliberately no standalone update-sty target: the theme refresh
# (md2pdfLib/presentation/scripts/update_own_sty.sh) only makes sense inside a
# build container, and the beamer target already runs it there. Run standalone
# in a --rm container, its texmf changes were discarded with the container.
