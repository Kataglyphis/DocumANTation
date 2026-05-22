Kataglyphis-mdToPdf Documentation
=================================

.. rst-class:: hero-section

Containerized Markdown-to-PDF builds for books, dissertations, presentations, and CVs with Pandoc and LuaLaTeX.

- Reproducible container workflows built around ``nerdctl`` and shared wrapper scripts
- Shared Pandoc presets and LaTeX templates for print, slide, and CV outputs
- Optional strict warning checks for logs, glossaries, bibliography, and nomenclature

.. grid:: 2
   :gutter: 2

   .. grid-item-card:: Overview
      :link: overview
      :link-type: doc

      Repository structure, document types, shared components, and important entry points.

   .. grid-item-card:: Getting Started
      :link: getting-started
      :link-type: doc

      Prerequisites, clone instructions, container image setup, and the fastest build commands.

   .. grid-item-card:: Build Pipeline
      :link: build-pipeline
      :link-type: doc

      How Pandoc, LuaLaTeX, bibliography, glossary, and nomenclature steps fit together.

   .. grid-item-card:: Project Information
      :link: project-info
      :link-type: doc

      Development tooling, dependencies, contribution flow, license, and contact details.

Common Commands
---------------

.. code-block:: bash

   nerdctl build . -t pandoc_all
   ./scripts/build_in_container.sh book
   ./scripts/build_in_container.sh diss
   ./scripts/build_in_container.sh beamer
   ./scripts/build_in_container.sh cv


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   overview
   getting-started
   build-pipeline
   project-info
