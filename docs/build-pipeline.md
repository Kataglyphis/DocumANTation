# Build Pipeline

Each document type has its own flow; every flow builds inside `data/out/`.

## Book

1. `pandoc` reads the Markdown chapters and writes `data/out/*.tex`.
2. `lualatex` runs once, producing `.aux`, `.bcf`, `.glo` and `.nlo`.
3. `biber` resolves the bibliography.
4. `makeglossaries` builds the glossary.
5. `makeindex` builds the nomenclature.
6. `lualatex` runs twice more to resolve cross-references and produce the final PDF.

Every auxiliary tool runs inside `data/out/`, so nothing is written next to the sources.

## Presentation

`beamer` uses Pandoc's own PDF flow:

1. Update the local Beamer theme copy.
2. Run Pandoc with the custom Beamer template.
3. Pandoc repeats the LuaLaTeX passes until the PDF is stable.

`pptx` renders the same markdown as a PowerPoint deck:

1. `make_reference.py` builds a brand-themed `reference.pptx` from `style/brand.json`: the Office
   colour scheme and fonts, plus the beamer look ported into the slide layouts — a white title
   slide with the beamer title page's image in a slanted right-hand wedge, bold small-caps
   titles, section pages accent-on-dark, an accent separator rule under content titles, and the
   footline strip with its accent block.
2. Pandoc renders the deck against that reference document.
3. `finalize_deck.py` finishes what Pandoc leaves undone: it re-attaches media that only a layout
   references, unwraps Microsoft-only `mc:AlternateContent` so every viewer renders the content,
   injects the footline slide numbers, and (via `style_code.py`) lifts each code block into the
   beamer code box — dark fill, accent frame, sized to fit instead of running off the slide.
4. In strict mode, `verify_brand.py` fails the build if the deck's colours or theme fonts are not
   brand values.

The deck must look right in viewers that never re-lay it out:

- Code and title sizes are computed, not left to `normAutofit`: LibreOffice honours a stored
  `fontScale` only when it agrees with its own measurement.
- The slide number is a plain text shape: LibreOffice ignores slide-level `sldNum` placeholders.
- Unwrapping `mc:AlternateContent` re-declares the Choice's namespace prefixes on `<p:sld>`, or
  PowerPoint demands a repair.
- Pandoc's repeated `cNvPr` ids within a slide are renumbered, because ECMA-376 requires them
  unique.

## CV

`cv` is a direct LuaLaTeX build:

1. LuaLaTeX runs once to create the auxiliary files.
2. LuaLaTeX runs a second time to stabilize the output.

Both runs write to `data/out/` with `-jobname=CV_Jonas_Heinle_<language>`, the filename the CV is
published under, so the deliverable is a build output, not a committed binary. A tailored profile
(`CV_PROFILE`, one file per application in `data/cv/profiles/`) swaps the language for its
`CV_JOB_SUFFIX`.

`letter` is the same two-pass build over the same class and profile, with the cover letter
`data/cv/letters/<CV_PROFILE>.tex` as its body; it writes
`Cover_Letter_Jonas_Heinle_<suffix>.pdf`.

The CV is bilingual from one set of sources: every section file carries an English and a German
variant behind `\IfLanguageName`, and `CV_LANG` passes a class option through to `myCV_METADATA`
that picks one. It also selects the `datetime2` style, so a German CV does not print US dates.

```bash
CV_LANG=german ./scripts/build_in_container.sh cv
make cv-all   # both published variants
```

## Strict Warning Checks

`STRICT_WARNINGS=1` enables strict mode for the container wrapper, `--strict-warnings` for the
glossary build script. The final log is then inspected, and the build fails on warnings or
bad-box diagnostics. For the book, an underfull `\hbox` and tcolorbox's "Using nobreak failed"
hint are reported and counted but not fatal. The full list:
[AGENTS.md § What the strict gate fails on](https://github.com/Kataglyphis/DocumANTation/blob/develop/AGENTS.md#what-the-strict-gate-fails-on).

## Related Commands

```bash
./scripts/build_in_container.sh book
./scripts/build_in_container.sh beamer
./scripts/build_in_container.sh demo
./scripts/build_in_container.sh example
./scripts/build_in_container.sh pptx
./scripts/build_in_container.sh cv
CV_PROFILE=parallel-ai ./scripts/build_in_container.sh letter
./md2pdfLib/scripts/compile_with_glossaries.sh --type book
```
