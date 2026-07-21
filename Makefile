.PHONY: book diss beamer pptx cv cv-all update-sty

IMAGE ?= pandoc_all
STRICT_WARNINGS ?= 0
# cv only: english (default) or german. Both come from the same sources.
CV_LANG ?= english
ENTRYPOINT := --entrypoint ""
VOLUMES := -v "$(CURDIR)/md2pdfLib:/md2pdfLib" -v "$(CURDIR)/data:/data"
RUN := nerdctl run --rm $(ENTRYPOINT) $(VOLUMES) $(IMAGE)
ACTIVATE := . md2pdf/bin/activate

book diss beamer pptx cv:
	IMAGE="$(IMAGE)" STRICT_WARNINGS="$(STRICT_WARNINGS)" CV_LANG="$(CV_LANG)" ./scripts/build_in_container.sh $@

# Both published CV variants, the pair linked from jonasheinle.de.
cv-all:
	$(MAKE) cv CV_LANG=english
	$(MAKE) cv CV_LANG=german

update-sty:
	$(RUN) sh -c '$(ACTIVATE) && chmod +x md2pdfLib/presentation/scripts/update_own_sty.sh && ./md2pdfLib/presentation/scripts/update_own_sty.sh'
