DOC_TARGETS = book beamer demo example pptx cv
WATCH_TARGETS = beamer book cv demo example

.PHONY: $(DOC_TARGETS) cv-all cv-mistral-rse $(addprefix watch-,$(WATCH_TARGETS))

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

$(DOC_TARGETS):
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
#
# One recipe, generated per target, so the entr check and the install hint are
# written once instead of once per target. Adding a watchable target is the two
# data lines below and its name in WATCH_TARGETS.
#
# Generated with $(eval) rather than written as a `watch-%:` pattern rule:
# make skips implicit-rule search for .PHONY targets, so a pattern rule plus
# the .PHONY line above silently produces "Nothing to be done for watch-book"
# -- the watcher never starts, and nothing reports why.
WATCH_DIR_beamer = data/presentation
WATCH_EXT_beamer = md
WATCH_DIR_book = data/book
WATCH_EXT_book = md
WATCH_DIR_cv = data/cv
WATCH_EXT_cv = tex
WATCH_DIR_demo = data/presentation/demo
WATCH_EXT_demo = md
WATCH_DIR_example = data/example
WATCH_EXT_example = md

define WATCH_RULE
watch-$(1):
	@command -v entr >/dev/null 2>&1 || { echo "entr not found — install with: apt install entr / brew install entr"; exit 1; }
	@echo "Watching $$(WATCH_DIR_$(1))/**/*.$$(WATCH_EXT_$(1)) — rebuilds on every change"
	find $$(WATCH_DIR_$(1)) -name '*.$$(WATCH_EXT_$(1))' | entr -c $$(MAKE) $(1)
endef

$(foreach target,$(WATCH_TARGETS),$(eval $(call WATCH_RULE,$(target))))

# There is deliberately no standalone update-sty target: the theme refresh
# (md2pdfLib/presentation/scripts/update_own_sty.sh) only makes sense inside a
# build container, and the beamer target already runs it there. Run standalone
# in a --rm container, its texmf changes were discarded with the container.
