# CV

The content of Jonas Heinle's CV. The layout lives elsewhere: the
`myCV_METADATA` class is in `md2pdfLib/cv/template/latex/`, with the book and
presentation templates, and reaches this directory through `TEXINPUTS`.

## Building

```bash
./scripts/build_in_container.sh cv                  # English
CV_LANG=german ./scripts/build_in_container.sh cv   # German
make cv-all                                         # both
make cv-mistral-rse                                 # Research Software Engineer, Mistral
make cv-mistral-platform                            # Platform Engineer, Mistral Research Platform
make cv-amd-hpc                                     # Lead HPC/AI Computational Scientist, AMD GENCI CoE
make cv-terabase-cv                                 # Computer Vision Engineer, Bamboo, Terabase Energy
make cv-parallel-ai                                 # AI Engineer, Parallel
make letter-parallel-ai                             # its cover letter
make cv-c12-automation                              # AI Automation Engineer, C12 Quantum Electronics
make letter-c12-automation                          # its cover letter
```

Output lands in `data/out/CV_Jonas_Heinle_<language>.pdf` — the filenames the
CV is published under on jonasheinle.de, so the deliverables are reproducible
rather than committed binaries. Nothing in this directory is a build artifact.

## Profiles

`CV_PROFILE` selects which sections a build shows and which summary sits above
them; one file per target in `profiles/`, and `default` is the CV published on
jonasheinle.de. It is orthogonal to `CV_LANG` — every profile builds in both
languages. Tailoring an application means adding a profile, never editing
`cv.tex` or copying a section file. See `profiles/README.md`.

## Cover letters

A cover letter is this CV document with a letter as its body, not a second
template. `./scripts/build_in_container.sh letter` (or `make letter-<name>`)
builds `letters/<CV_PROFILE>.tex` with the CV profile of the same name, so the
letter gets the CV's class, fonts, colours, footer and header, down to that
application's tagline and relocation line. It cannot drift from its CV.
Output: `data/out/Cover_Letter_<First>_<Last>_<CV_JOB_SUFFIX>.pdf`.

| File | Contents |
| --- | --- |
| `letters/<name>.tex` | One letter per application: redefines `\cvBody` as the letter and `\cvfootertitle` as "Cover Letter" |
| `md2pdfLib/cv/template/latex/brand-letter.tex` | The layout: `\cvletterhead{<place, date>}{<recipient>}{<subject>}` and `\cvletterclosing{<closing>}`, which signs with `\brandName` |

A new application's letter is a copy of an existing `letters/*.tex`,
renamed after its CV profile, plus a `letter-<name>` target in the Makefile.
Adjust the text to the posting. As everywhere in these sources, a replaced
sentence goes into a `%` comment beside its replacement and is never
deleted: another application may want it back. The identity rule holds here
too: sign with `\brandName`, never the literal name.

Add `STRICT_WARNINGS=1` to fail the build on LaTeX warnings and bad boxes, and
build both languages that way before publishing: CI has compiled no LaTeX since
2026-08-20, so nothing else will.

## Bilingual sources

There is one CV, not two. Every section file carries both variants:

```latex
\IfLanguageName{english}{Experiences}{Berufserfahrung}
```

`CV_LANG` passes a class option that sets the babel main language and the
`datetime2` style. **Edit both branches when you change a section**, and build
both languages strictly (`STRICT_WARNINGS=1`): German text that overruns a column
the English text fits fails only the German build.

French is loaded for `\foreignlanguage` but is not a main-language choice: the
sections carry no French text. Adding it means a third branch everywhere, so
`\IfLanguageName` would want replacing with something that scales.

## Layout

| File | Contents |
| --- | --- |
| `cv.tex` | Document root: header and contact details. The section order lives in the profile |
| `profiles/*.tex` | One per target: the tagline and the ordered section list |
| `section_*.tex` | One section each, shared by every profile |
| `section_headline_*.tex` | Per-profile summary; the one place wording is tailored |
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
