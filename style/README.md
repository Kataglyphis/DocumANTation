# Kataglyphis brand style

`brand.json` is the **single source of truth** for every colour and font used by
the CV, the book, the presentation and the docs website. Nothing else defines a
brand value; everything below is generated from it.

## Changing the brand

```bash
$EDITOR style/brand.json
python style/generate_style.py --write
```

CI runs `python style/generate_style.py --check` and fails if any generated file
drifted, so a hand-edit to a derived file cannot survive review.

Values of the form `"@other_key"` are aliases, so a literal is never written
twice (`"text_on_accent": "@white"`). `colors_dark` may alias into `colors`.

## Generated files — do not edit by hand

| File | Consumer |
| --- | --- |
| `md2pdfLib/style/brand-colors.tex` | LaTeX: `brandAccent`, `brandLink`, plus `greenAccent`/`myGreenAccent`/`basecolor`/`linkcolor` aliases |
| `md2pdfLib/style/brand-fonts.tex` | LaTeX: `\brandSetMainFont`, `\brandSetMonoFont` |
| `md2pdfLib/pandoc/base.yml`, `md2pdfLib/presentation/pandoc/metadata.yml` | Pandoc: `mainfont`, `monofont`, `monofontoptions`, `linkcolor`, `urlcolor`, `citecolor` (between `# generated:brand:` markers) |
| `sphinx-kataglyphis-theme/.../_static/css/custom.css` | Web: `--brand-*` custom properties (between `/* generated:brand-tokens: */` markers) |
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

- Code/listing palettes (`mygreen`, `mymauve`, `amber` in `bookclass.cls`,
  `Light` in `inline_code.tex`, `shadecolor`) — syntax-highlighting colours, not
  brand identity.
- Neutral greys and blacks used for CV body text and headings.
- `fonts.mono` names a TeX font (Latin Modern Mono) and is **not** emitted to
  CSS, because no browser has it; the web keeps the generic monospace stack.
- The `green`/`red`/`indigo`/`orange`/`monochrome` class options in
  `myCV_METADATA.cls` each hardcode their own `basecolor` and would override the
  brand accent. The CV does not pass any of them, so it uses the brand; treat
  them as legacy.
- `md2pdfLib/presentation/template/latex/smile/` is a vendored upstream theme
  (its own submodule) and is left alone.
