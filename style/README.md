# Kataglyphis brand style

`brand.json` is the **single source of truth** for every colour and font used by
the CV, the book, the beamer slides, the PowerPoint deck and the docs website.
Nothing else defines a brand value; everything below is generated from it.

Every colour token declared here is consumed by something — a test fails if you
add one and nothing reads it, so `brand.json` cannot fill up with values that
only look central. The two exceptions are `white` and `black`, which exist as
alias targets (`"text_on_accent": "@white"`).

## Changing the brand

```bash
$EDITOR style/brand.json
python style/generate_style.py --write
```

CI runs `python style/generate_style.py --check` and fails if any generated file
drifted, so a hand-edit to a derived file cannot survive review.

Values of the form `"@other_key"` are aliases, so a literal is never written
twice (`"text_on_accent": "@white"`). `colors_dark` may alias into `colors`.

## Sections

| Section | Drives |
| --- | --- |
| `colors` / `colors_dark` | Brand identity: accent, links, surfaces (LaTeX, CSS) |
| `syntax` / `syntax_dark` | Code highlighting, shared by the PDFs (Pandoc) and the website (Pygments) |
| `fonts` | Main + mono font, for LaTeX, Pandoc and the web |

`syntax` is the light/print palette and `syntax_dark` the dark one. All PDF
documents (book, slides, pptx) render with the **dark** palette for a single
brand code-block look. The website uses **both** — it switches with the site's
light/dark toggle.
Which token gets bold or italic is structural and lives in `SYNTAX_TOKENS` /
`PYGMENTS_TOKENS` in `generate_style.py`, not here; `brand.json` stays a pure
colour/font file.

## Generated files — do not edit by hand

| File | Consumer |
| --- | --- |
| `md2pdfLib/style/brand-colors.tex` | LaTeX: `brandAccent`, `brandLink`, plus `greenAccent`/`myGreenAccent`/`basecolor`/`linkcolor` aliases |
| `md2pdfLib/style/brand-fonts.tex` | LaTeX: `\brandSetMainFont`, `\brandSetMonoFont` |
| `md2pdfLib/pandoc/base.yml`, `md2pdfLib/presentation/pandoc/metadata.yml` | Pandoc: `mainfont`, `monofont`, `monofontoptions`, `linkcolor`, `urlcolor`, `citecolor` (between `# generated:brand:` markers) |
| `sphinx-kataglyphis-theme/.../_static/css/custom.css` | Web: `--brand-*` custom properties (between `/* generated:brand-tokens: */` markers) |
| `md2pdfLib/themes/pygments.theme` | Pandoc code highlighting, dark — used by **all** documents (book, slides, pptx) |
| `sphinx-kataglyphis-theme/sphinx_kataglyphis/highlight.py` | Pygments styles `kataglyphis-light` / `kataglyphis-dark` — the **website**'s code highlighting |
| `style/brand.css` | Any web project that is not the Sphinx theme (the Flutter site): `--brand-*` tokens, link it directly |
| `style/brand.tokens.json` | Anything: `brand.json` with aliases resolved |
| `sphinx-kataglyphis-theme/sphinx_kataglyphis/brand.tokens.json` | Same, shipped inside the pip package |
| `md2pdfLib/style/brand.tokens.json` | Same, reachable from the build container (it mounts only `md2pdfLib/` and `data/`) |

## Reusing the brand in another project

### Python

```bash
pip install -e ./external/Kataglyphis-DocumANTation/sphinx-kataglyphis-theme
```

```python
from sphinx_kataglyphis import brand

brand()["colors"]["accent"]       # the brand accent
brand()["colors"]["link"]         # link colour, light theme
brand()["colors_dark"]["link"]    # ... and dark
brand()["fonts"]["main"]          # 'Roboto'
```

### Sphinx docs

`setup_theme()` already puts the brand stylesheet on `html_static_path` and
`html_css_files`. Nothing to copy:

```python
from sphinx_kataglyphis import setup_theme
setup_theme(globals(), repository_url="https://github.com/org/repo")
```

Style your own rules with the tokens rather than literals:

```css
.my-thing { color: var(--brand-accent-strong); border: 1px solid var(--brand-surface-border); }
```

`setup_theme()` also points `pygments_light_style` / `pygments_dark_style` at the
shared `kataglyphis-light` / `kataglyphis-dark` styles, so code blocks on the
site match the book. Installing the theme registers them with Pygments, so they
work in any Pygments consumer, not just Sphinx:

```python
from pygments.styles import get_style_by_name
get_style_by_name("kataglyphis-dark")
```

### LaTeX

Put the style directory on the LaTeX search path, then `\input` by bare name —
documents never hardcode a path to this repo:

```bash
TEXINPUTS="/path/to/Kataglyphis-DocumANTation/md2pdfLib/style:" lualatex mydoc.tex
```

```latex
\input{brand-colors.tex}   % brandAccent, brandLink, linkcolor, basecolor, ...
\input{brand-fonts.tex}    % \brandSetMainFont, \brandSetMonoFont
```

Both files are safe to `\input` more than once. `brand-colors.tex` needs
`xcolor` loaded; `brand-fonts.tex` needs `fontspec`.

### PowerPoint

A pptx takes its colours and fonts only from a `--reference-doc`, which is a
binary deck. Rather than commit one — brand values in a file nothing can diff
or drift-check — `md2pdfLib/presentation/pptx/make_reference.py` builds it from
these tokens at build time, by patching the Office theme inside pandoc's own
default reference deck. It is a build artifact and is never committed:

```bash
python md2pdfLib/presentation/pptx/make_reference.py data/out/reference.pptx
```

The twelve Office colour slots are the one place the brand meets PowerPoint's
vocabulary; `accent1` is the brand accent, `hlink` the brand link. If pandoc
ever changes its default deck's layout the build fails loudly rather than
emitting a half-branded deck.

### A website that is not Sphinx

Link the standalone token sheet and use the custom properties. Never copy a hex
value into the site — that is how the site ended up one digit off the brand
(`#69f0ae` instead of `#6af0ad`):

```html
<link rel="stylesheet" href="brand.css">
```

```css
.loading { background: linear-gradient(45deg, var(--brand-white), var(--brand-accent)); }
```

### Any other language

Read `style/brand.tokens.json` (or the copy inside the installed Python
package). It is plain JSON with every alias already resolved — no alias support
needed — and carries **every** section of `brand.json`, including the syntax
palettes, so a non-LaTeX, non-Sphinx consumer can match the book's code
colours too:

```json
{
  "colors":      { "accent": "#6af0ad", ... },
  "colors_dark": { ... },
  "syntax":      { "keyword": "#d73a49", ... },
  "syntax_dark": { "keyword": "#ff7b72", ... },
  "fonts":       { "main": "Roboto", ... }
}
```

## Deliberately not brand-wide

These are per-document values that live with the document, not in `brand.json`:

- `shadecolor` is now defined in `brand-colors.tex` as `brandSyntaxBg` (the
  dark syntax palette bg, `#0d1117`). Every document shares the same
  code-block background — no per-document override needed.
- Neutral greys and blacks used for CV body text and headings.
- `fonts.mono` names a TeX font (Latin Modern Mono) and is **not** emitted to
  CSS, because no browser has it; the web keeps the generic monospace stack.
- `md2pdfLib/presentation/template/latex/smile/` is a vendored upstream theme
  (its own submodule) and is left alone. Its semantic palette (red/blue/…) is
  not brand; only its generic `green` is remapped to `brandAccentDeep` by the
  beamer template, because the `examples` blocks use it in a brand-identity
  role. Note: smile's `listings` option (88 lines of `lstdefinestyle` code) is
  **never activated** — `beamerthemeawesome.sty` does not pass `[listings]` to
  `\RequirePackage{smile}`, so that entire module is dead code in the
  vendored submodule.

The upstream CV template's `green`/`red`/`indigo`/`orange`/`monochrome` class
options, which each hardcoded a `basecolor` that would have overridden the
brand accent, have been removed from `myCV_METADATA.cls` — the accent is not a
per-document choice.
