.PHONY: book diss beamer cv update-sty

IMAGE ?= pandoc_all
STRICT_WARNINGS ?= 0
ENTRYPOINT := --entrypoint ""
VOLUMES := -v "$(CURDIR)/md2pdfLib:/md2pdfLib" -v "$(CURDIR)/data:/data"
RUN := nerdctl run --rm $(ENTRYPOINT) $(VOLUMES) $(IMAGE)
ACTIVATE := . md2pdf/bin/activate

book diss beamer cv:
	IMAGE="$(IMAGE)" STRICT_WARNINGS="$(STRICT_WARNINGS)" ./scripts/build_in_container.sh $@

update-sty:
	$(RUN) sh -c '$(ACTIVATE) && chmod +x md2pdfLib/presentation/scripts/update_own_sty.sh && ./md2pdfLib/presentation/scripts/update_own_sty.sh'
