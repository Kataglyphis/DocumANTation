.PHONY: book beamer pptx cv cv-all cv-mistral-rse watch-beamer watch-book watch-cv

IMAGE ?= pandoc_all
STRICT_WARNINGS ?= 0
# cv only: english (default) or german. Both come from the same sources.
CV_LANG ?= english
# cv only: which section set and summary to build, one file per target in
# data/cv/profiles/. Orthogonal to CV_LANG.
CV_PROFILE ?= default
# cv only: output basename. Empty means the script's default, which is the
# published CV_Jonas_Heinle_<language>. Tailored profiles set it explicitly --
# the filename is the first thing a recruiter sees.
CV_JOB ?=

book beamer pptx cv:
	IMAGE="$(IMAGE)" STRICT_WARNINGS="$(STRICT_WARNINGS)" CV_LANG="$(CV_LANG)" CV_PROFILE="$(CV_PROFILE)" CV_JOB="$(CV_JOB)" ./scripts/build_in_container.sh $@

# Both published CV variants, the pair linked from jonasheinle.de.
cv-all:
	$(MAKE) cv CV_LANG=english
	$(MAKE) cv CV_LANG=german

# Application: Research Software Engineer, Mistral AI (Paris).
cv-mistral-rse:
	$(MAKE) cv CV_PROFILE=mistral-rse CV_JOB=CV_Jonas_Heinle_Mistral_RSE

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
