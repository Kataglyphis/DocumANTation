# Build Pipeline

The repository uses slightly different compilation flows depending on the document type, but the build steps stay consistent inside `data/out/`.

## Book

The `book` target runs a staged pipeline:

1. `pandoc` reads Markdown chapters and writes `data/out/*.tex`.
2. `lualatex` runs once, producing `.aux`, `.bcf`, `.glo` and `.nlo`.
3. `biber` resolves bibliography data.
4. `makeglossaries` builds glossary output.
5. `makeindex` builds nomenclature output.
6. `lualatex` runs twice more to resolve cross-references and produce the final PDF.

Every auxiliary tool runs inside `data/out/`, so nothing is written next to the
sources.

## Presentation

The `beamer` target uses Pandoc's PDF generation flow directly:

1. Update the local Beamer theme copy.
2. Run Pandoc with the custom Beamer template.
3. Let Pandoc drive repeated LuaLaTeX passes until the PDF is stable.

The `pptx` target renders the same markdown as a PowerPoint deck:

1. `make_reference.py` builds a brand-themed `reference.pptx` from `style/brand.json`:
   the Office colour scheme and fonts, plus the beamer look ported into the
   slide layouts — a white title slide with the beamer title page's image in a
   slanted right-hand wedge, bold small-caps titles, section pages
   accent-on-dark, an accent separator rule under content titles, and the
   footline strip with its accent block.
2. Pandoc renders the deck against that reference document.
3. `finalize_deck.py` finishes what Pandoc leaves undone: it re-attaches media
   that only a layout references, unwraps Microsoft-only `mc:AlternateContent`
   so every viewer renders the content, injects the footline slide numbers,
   and (via `style_code.py`) lifts each code block into the beamer code box —
   dark fill, accent frame, sized to fit instead of running off the slide.
4. In strict mode, `verify_brand.py` fails the build if the emitted deck's
   colours or theme fonts are not brand values.

## CV

The `cv` target is a direct LuaLaTeX build:

1. Run LuaLaTeX once to create auxiliary files.
2. Run LuaLaTeX a second time to stabilize the output.

Both runs write to `data/out/` with `-jobname=CV_Jonas_Heinle_<language>`, which
is the filename the CV is published under, so the deliverable is a build output
rather than a committed binary.

The CV is bilingual from one set of sources: every section file carries an
English and a German variant behind `\IfLanguageName`, and `CV_LANG` picks
which one is typeset by passing a class option through to `myCV_METADATA`.
It also selects the `datetime2` style, so a German CV does not print US dates.

```bash
CV_LANG=german ./scripts/build_in_container.sh cv
make cv-all   # both published variants
```

## Strict Warning Checks

Strict mode can be enabled with `STRICT_WARNINGS=1` for the shared container wrapper, or with `--strict-warnings` for the glossary build script.
When strict mode is enabled, the final log is inspected and the build fails on warnings or bad-box diagnostics.

## Related Commands

```bash
./scripts/build_in_container.sh book
./scripts/build_in_container.sh beamer
./scripts/build_in_container.sh pptx
./scripts/build_in_container.sh cv
./md2pdfLib/scripts/compile_with_glossaries.sh --type book
```
