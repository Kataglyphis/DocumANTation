# CV

The content of Jonas Heinle's CV. The layout lives elsewhere: the
`myCV_METADATA` class is in `md2pdfLib/cv/template/latex/`, with the book and
presentation templates, and reaches this directory through `TEXINPUTS`.

## Building

```bash
./scripts/build_in_container.sh cv                  # English
CV_LANG=german ./scripts/build_in_container.sh cv   # German
make cv-all                                         # both
```

Output lands in `data/out/CV_Jonas_Heinle_<language>.pdf` — the filenames the
CV is published under on jonasheinle.de, so the deliverables are reproducible
rather than committed binaries. Nothing in this directory is a build artifact.

Add `STRICT_WARNINGS=1` to fail the build on LaTeX warnings and bad boxes. CI
runs both languages that way.

## Bilingual sources

There is one CV, not two. Every section file carries both variants:

```latex
\IfLanguageName{english}{Experiences}{Berufserfahrung}
```

`CV_LANG` passes a class option that sets the babel main language and the
`datetime2` style. **Edit both branches when you change a section** — CI builds
both languages strictly, so German text that overruns a column the English text
fits will fail there.

French is loaded for `\foreignlanguage` but is not a main-language choice: the
sections carry no French text. Adding it means a third branch everywhere, so
`\IfLanguageName` would want replacing with something that scales.

## Layout

| File | Contents |
| --- | --- |
| `cv.tex` | Document root: header, contact details, section order |
| `section_*.tex` | One section each, in the order `cv.tex` inputs them |
| `images/` | Header photo. Keep it small — this file *is* the PDF's size |

`section_references.tex` is deliberately not input; `cv.tex` keeps the line
commented so references can be switched back on for applications that ask.

The photo is drawn with `fill overzoom image` into a box roughly 4.95cm wide,
so ~1000px across is already past what print needs. It was once committed at
4611x3294, which made a two-page CV a 3.8 MB attachment.

## Attribution

The `myCV_METADATA` class derives from Christophe Roger's
[YAAC / Awesome Source CV](https://github.com/darwiin/yaac-another-awesome-cv),
itself based on a template by Alessandro Plasmati. The class is distributed
under the LPPL and the section templates under CC BY-SA 4.0; both headers carry
the original notices, which must stay.

Colours and fonts are **not** set here — they come from `style/brand.json`
through `brand-colors.tex` and `brand-fonts.tex`, shared with the book, the
slides and the website. See `style/README.md`.
