Build Pipeline
==============

Book and dissertation
---------------------

The ``book`` and ``diss`` targets use the same staged pipeline:

1. Pandoc reads Markdown chapters and produces ``data/out/*.tex``.
2. LuaLaTeX runs once to create auxiliary files.
3. ``biber`` resolves bibliography data.
4. ``makeglossaries`` builds glossary output.
5. ``makeindex`` builds nomenclature output.
6. LuaLaTeX runs twice more to resolve references and produce the final PDF.

Presentation
------------

The ``beamer`` target uses Pandoc's PDF generation flow directly:

1. Update the local Beamer theme copy.
2. Run Pandoc with the custom Beamer template.
3. Let Pandoc drive repeated LuaLaTeX passes until the PDF is stable.

CV
--

The ``cv`` target is a direct LuaLaTeX build:

1. Run LuaLaTeX once to create auxiliary files.
2. Run LuaLaTeX a second time to stabilize the output.

Strict warning checks
---------------------

Strict mode can be enabled with ``STRICT_WARNINGS=1`` for the shared container
wrapper, or with ``--strict-warnings`` for the glossary build script.

When strict mode is enabled, the final log is inspected and the build fails on
warnings or bad-box diagnostics.
