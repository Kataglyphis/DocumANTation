DOC_TARGETS = book beamer demo example pptx cv letter
WATCH_TARGETS = beamer book cv demo example

.PHONY: $(DOC_TARGETS) cv-all cv-mistral-rse cv-mistral-platform cv-amd-hpc cv-terabase-cv cv-parallel-ai letter-parallel-ai cv-c12-automation letter-c12-automation cv-tissium-automation cv-runware-creative letter-runware-creative cv-snap-bci cv-zendar-optim cv-realtime-vision cv-realtime-vision-german $(addprefix watch-,$(WATCH_TARGETS))

IMAGE ?= pandoc_all
.PHONY: cv-scaleway-software
.PHONY: cv-chipiron-ai
.PHONY: letter-chipiron-ai
.PHONY: letter-skillcorner-cv
.PHONY: cv-scaleway-backend letter-scaleway-backend
STRICT_WARNINGS ?= 0
# cv only: english (default) or german. Both come from the same sources.
CV_LANG ?= english
# cv only: section set and summary, one file per target in data/cv/profiles/; orthogonal to CV_LANG.
CV_PROFILE ?= default
# cv only: <suffix> of CV_<First>_<Last>_<suffix> (the name comes from style/brand.json); empty means the language.
CV_JOB_SUFFIX ?=
# cv only: full output basename, overriding the generated one entirely.
CV_JOB ?=

$(DOC_TARGETS):
	IMAGE="$(IMAGE)" STRICT_WARNINGS="$(STRICT_WARNINGS)" CV_LANG="$(CV_LANG)" CV_PROFILE="$(CV_PROFILE)" CV_JOB_SUFFIX="$(CV_JOB_SUFFIX)" CV_JOB="$(CV_JOB)" ./scripts/build_in_container.sh $@

# Both published CV variants, the pair linked from jonasheinle.de.
cv-all:
	$(MAKE) cv CV_LANG=english
	$(MAKE) cv CV_LANG=german

# Keep application filenames stable across reproducible builds.
cv-scaleway-software:
	$(MAKE) cv CV_PROFILE=scaleway-software CV_JOB_SUFFIX=Scaleway_Software_Engineer

cv-scaleway-backend:
	$(MAKE) cv CV_LANG=english CV_PROFILE=scaleway-backend CV_JOB_SUFFIX=Scaleway_Backend_Python_DevOps

letter-scaleway-backend:
	$(MAKE) letter CV_LANG=english CV_PROFILE=scaleway-backend CV_JOB_SUFFIX=Scaleway_Backend_Python_DevOps

cv-chipiron-ai:
	$(MAKE) cv CV_LANG=english CV_PROFILE=chipiron-ai CV_JOB_SUFFIX=Chipiron_AI_Engineer

letter-chipiron-ai:
	$(MAKE) letter CV_LANG=english CV_PROFILE=chipiron-ai CV_JOB_SUFFIX=Chipiron_AI_Engineer

letter-skillcorner-cv:
	$(MAKE) letter CV_LANG=english CV_PROFILE=skillcorner-cv CV_JOB_SUFFIX=SkillCorner_Computer_Vision_Scientist

# Application: Research Software Engineer, Mistral AI (Paris).
cv-mistral-rse:
	$(MAKE) cv CV_PROFILE=mistral-rse CV_JOB_SUFFIX=Mistral_RSE

# Application: Platform Engineer, Research Platform team, Mistral AI (Paris/Warsaw/London).
cv-mistral-platform:
	$(MAKE) cv CV_PROFILE=mistral-platform CV_JOB_SUFFIX=Mistral_Platform

# Application: Lead HPC/AI Computational Scientist / Engineer, AMD GENCI Center of Excellence (Paris).
cv-amd-hpc:
	$(MAKE) cv CV_PROFILE=amd-hpc CV_JOB_SUFFIX=AMD_HPC

# Application: Computer Vision Engineer, Bamboo, Terabase Energy (Paris); not _CV, CV_..._CV.pdf reads as a typo.
cv-terabase-cv:
	$(MAKE) cv CV_PROFILE=terabase-cv CV_JOB_SUFFIX=Terabase

# Application: AI Engineer, Parallel (Paris).
cv-parallel-ai:
	$(MAKE) cv CV_PROFILE=parallel-ai CV_JOB_SUFFIX=Parallel_AI

# Cover letters typeset data/cv/letters/<CV_PROFILE>.tex with the CV profile of the same name.
letter-parallel-ai:
	$(MAKE) letter CV_PROFILE=parallel-ai CV_JOB_SUFFIX=Parallel_AI

# Application: AI Automation Engineer, C12 Quantum Electronics (Paris).
cv-c12-automation:
	$(MAKE) cv CV_PROFILE=c12-automation CV_JOB_SUFFIX=C12_AI_Automation

letter-c12-automation:
	$(MAKE) letter CV_PROFILE=c12-automation CV_JOB_SUFFIX=C12_AI_Automation

# Application: AI & Automation Lead, TISSIUM (Paris).
cv-tissium-automation:
	$(MAKE) cv CV_PROFILE=tissium-automation CV_JOB_SUFFIX=Tissium_AI_Automation

# Application: Creative Engineer / AI Creative Technologist, Runware (France, remote).
cv-runware-creative:
	$(MAKE) cv CV_PROFILE=runware-creative CV_JOB_SUFFIX=Runware_Creative

letter-runware-creative:
	$(MAKE) letter CV_PROFILE=runware-creative CV_JOB_SUFFIX=Runware_Creative

# Application: Software Engineer, C++, Brain-Computer Interface team, Snap Inc. (Paris).
cv-snap-bci:
	$(MAKE) cv CV_PROFILE=snap-bci CV_JOB_SUFFIX=Snap_BCI

# Application: Machine Learning Engineer, Model Optimization, Zendar (Paris).
cv-zendar-optim:
	$(MAKE) cv CV_PROFILE=zendar-optim CV_JOB_SUFFIX=Zendar_ML_Optimization

# Recruiter contact: real-time video pipelines, client not named (Germany).
cv-realtime-vision:
	$(MAKE) cv CV_PROFILE=realtime-vision CV_JOB_SUFFIX=Realtime_Vision

cv-realtime-vision-german:
	$(MAKE) cv CV_PROFILE=realtime-vision CV_LANG=german CV_JOB_SUFFIX=Realtime_Vision_German

# watch-<target> rebuilds via entr; $(eval), not a watch-% rule, which make skips for .PHONY targets.
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

# No standalone update-sty target: in a --rm container its texmf changes are discarded; beamer runs it.
