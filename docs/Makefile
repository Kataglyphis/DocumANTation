# Minimal Makefile for Sphinx documentation.
#
# The same recipe `sphinx-kataglyphis scaffold` writes into a new project, so
# this repo's own docs build the way the scaffold tells everyone else to build
# theirs. `-M` dispatches on the goal, so `make html`, `make clean` and any
# other builder Sphinx supports all work without a target apiece.

SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = .
BUILDDIR      = _build
%:
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
