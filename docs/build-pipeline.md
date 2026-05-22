# Build Pipeline

The repository uses slightly different compilation flows depending on the document type, but the build steps stay consistent inside `data/out/`.

## Book and Dissertation

`book` and `diss` share the same staged pipeline:

1. `pandoc` reads Markdown chapters and writes `data/out/*.tex`.
2. `lualatex` runs once to create auxiliary files.
3. `biber` resolves bibliography data.
4. `makeglossaries` builds glossary output.
5. `makeindex` builds nomenclature output.
6. `lualatex` runs twice more to resolve cross-references and produce the final PDF.

```text
Markdown (.md) -> pandoc -> .tex
                 -> lualatex pass 1 -> .aux/.bcf/.glo/.nlo
                 -> biber
                 -> makeglossaries
                 -> makeindex
                 -> lualatex pass 2
                 -> lualatex pass 3 -> final PDF
```

## Presentation

The `beamer` target uses Pandoc's PDF generation flow directly:

1. Update the local Beamer theme copy.
2. Run Pandoc with the custom Beamer template.
3. Let Pandoc drive repeated LuaLaTeX passes until the PDF is stable.

## CV

The `cv` target is a direct LuaLaTeX build:

1. Run LuaLaTeX once to create auxiliary files.
2. Run LuaLaTeX a second time to stabilize the output.

## Strict Warning Checks

Strict mode can be enabled with `STRICT_WARNINGS=1` for the shared container wrapper, or with `--strict-warnings` for the glossary build script.
When strict mode is enabled, the final log is inspected and the build fails on warnings or bad-box diagnostics.

## Related Commands

```bash
./scripts/build_in_container.sh book
./scripts/build_in_container.sh diss
./scripts/build_in_container.sh beamer
./scripts/build_in_container.sh cv
./md2pdfLib/scripts/compile_with_glossaries.sh --type book
```
