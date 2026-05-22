Architecture
============

The project is split into content, shared build logic, and containerized tooling.

Repository layout
-----------------

.. code-block:: text

   data/        user-authored markdown, LaTeX headers, generated PDFs
   docs/        Sphinx documentation project
   md2pdfLib/   shared Python build logic, themes, templates, shell scripts
   scripts/     top-level helper wrappers for containerized builds

Important entry points
----------------------

``scripts/build_in_container.sh``
   Shared host-side wrapper for ``book``, ``diss``, ``beamer``, and ``cv``.

``md2pdfLib/build.py``
   Python CLI entry point for Pandoc-based document types.

``md2pdfLib/pandoc_builder.py``
   Shared command construction and execution for Pandoc builds.

``md2pdfLib/scripts/compile_with_glossaries.sh``
   Full LuaLaTeX, bibliography, glossary, and nomenclature pipeline for
   ``book`` and ``diss``.

``md2pdfLib/check_build_log.py``
   Optional strict warning checker for LaTeX logs and Pandoc JSON logs.

Document types
--------------

``book`` and ``diss``
   Markdown to LaTeX via Pandoc, then full TeX compilation with glossaries.

``beamer``
   Pandoc directly produces the presentation PDF through the custom Beamer
   template.

``cv``
   Direct LuaLaTeX build from the files in ``data/cv/``.
