# Kataglyphis brand style

`brand.json` is the **single source of truth** for every colour and font used by
the CV, the book, the presentation and the docs website. Nothing else defines a
brand value; everything below is generated from it.

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

`syntax` is the light/print palette and `syntax_dark` the dark one. The book
renders with the light palette, the dissertation and slides with the dark one,
and the website uses **both** — it switches with the site's light/dark toggle.
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
| `md2pdfLib/themes/pygments-print.theme` | Pandoc code highlighting, light/print — used by the **book** |
| `md2pdfLib/themes/pygments.theme` | Pandoc code highlighting, dark — used by the **dissertation** and **slides** |
| `sphinx-kataglyphis-theme/sphinx_kataglyphis/highlight.py` | Pygments styles `kataglyphis-light` / `kataglyphis-dark` — the **website**'s code highlighting |
| `style/brand.tokens.json` | Anything: `brand.json` with aliases resolved |
| `sphinx-kataglyphis-theme/sphinx_kataglyphis/brand.tokens.json` | Same, shipped inside the pip package |

## Reusing the brand in another project

### Python

```bash
pip install -e ./external/Kataglyphis-DocumANTation/sphinx-kataglyphis-theme
```

```python
from sphinx_kataglyphis import brand

brand()["colors"]["accent"]       # '#6af0ad'
brand()["colors"]["link"]         # '#1ca06a'
brand()["colors_dark"]["link"]    # '#7df5ba'
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

### Any other language

Read `style/brand.tokens.json` (or the copy inside the installed Python
package). It is plain JSON with every alias already resolved — no alias support
needed:

```json
{ "colors": { "accent": "#6af0ad", ... }, "colors_dark": { ... }, "fonts": { ... } }
```

## Deliberately not brand-wide

These are per-document values that live with the document, not in `brand.json`:

- A few LaTeX listing helpers (`mygreen`, `mymauve`, `amber` in `bookclass.cls`,
  `shadecolor` in `data/book/latex/main.tex`) are per-document leftovers. The
  actual code highlighting comes from the `syntax` palettes above.
- Neutral greys and blacks used for CV body text and headings.
- `fonts.mono` names a TeX font (Latin Modern Mono) and is **not** emitted to
  CSS, because no browser has it; the web keeps the generic monospace stack.
- The `green`/`red`/`indigo`/`orange`/`monochrome` class options in
  `myCV_METADATA.cls` each hardcode their own `basecolor` and would override the
  brand accent. The CV does not pass any of them, so it uses the brand; treat
  them as legacy.
- `md2pdfLib/presentation/template/latex/smile/` is a vendored upstream theme
  (its own submodule) and is left alone.
