# Kataglyphis brand style

`brand.json` is the **single source of truth** for every colour and font of the CV, the book, the
beamer slides, the PowerPoint deck and the docs website. Nothing else defines a brand value;
everything below is generated from it.

Every colour token declared here has a consumer: a test fails when one is added that nothing
reads, so `brand.json` cannot fill up with values that only look central. The exceptions are
`white` and `black`, which exist as alias targets.

## Changing the brand

```bash
$EDITOR style/brand.json
python style/generate_style.py --write
```

CI runs `python style/generate_style.py --check` and fails when a generated file drifted, so a
hand-edit to a derived file cannot survive review.

A value of the form `"@other_key"` is an alias, so no literal is written twice
(`"text_on_accent": "@white"`). `colors_dark` may alias into `colors`.

## Sections

| Section | Drives |
| --- | --- |
| `colors` / `colors_dark` | Brand identity: accent, links, surfaces (LaTeX, CSS) |
| `syntax` / `syntax_dark` | Code highlighting, shared by the PDFs (Pandoc) and the website (Pygments) |
| `fonts` | Main + mono font, for LaTeX, Pandoc and the web |
| `identity` | Author name, e-mail addresses, URL, GitHub/LinkedIn/YouTube handles, institute, copyright year — into `brand-identity.tex`, the Pandoc `author`/`institute` keys and `brand()["identity"]` |

`syntax` is the light/print palette, `syntax_dark` the dark one. Every PDF document (book, slides,
pptx) renders with the **dark** palette, for one brand code-block look. The website uses **both**
and switches with its light/dark toggle. Which token is bold or italic is structure, set in
`SYNTAX_TOKENS` / `PYGMENTS_TOKENS` in `generate_style.py`; `brand.json` holds colour, font and
identity values, never structure.

## Generated files — do not edit by hand

| File | Consumer |
| --- | --- |
| `md2pdfLib/style/brand-colors.tex` | LaTeX: `brandAccent`, `brandLink`, plus `greenAccent`/`myGreenAccent`/`basecolor`/`linkcolor` aliases |
| `md2pdfLib/style/brand-fonts.tex` | LaTeX: `\brandSetMainFont`, `\brandSetMonoFont` |
| `md2pdfLib/style/brand-identity.tex` | LaTeX: `\brandName`, `\brandEmail`, `\brandGithub`, `\brandUrl`, `\brandInstitute`, plus the `\myname` / `\myurl` / `\githubBase` aliases the book class and beamer header already used |
| `md2pdfLib/pandoc/base.yml`, `md2pdfLib/presentation/pandoc/metadata.yml`, `md2pdfLib/example/pandoc/metadata.yml` | Pandoc: `author`, `mainfont`, `monofont`, `monofontoptions`, `linkcolor`, `urlcolor`, `citecolor` — plus `institute` on the presentation only (between `# generated:brand:` markers) |
| `sphinx-kataglyphis-theme/.../_static/css/custom.css` | Web: `--brand-*` custom properties (between `/* generated:brand-tokens: */` markers) |
| `docs-tooling/source_templates/sphinx-book/custom.css` | None since 2026-10-19: a verbatim copy of the file above, kept beside the unused `conf_base.py` until both are deleted |
| `md2pdfLib/themes/pygments.theme` | Pandoc code highlighting, dark — used by **all** documents (book, slides, pptx) |
| `sphinx-kataglyphis-theme/sphinx_kataglyphis/highlight.py` | Pygments styles `kataglyphis-light` / `kataglyphis-dark` — the **website**'s code highlighting |
| `style/brand.css` | Any web project that is not the Sphinx theme (the Flutter site): `--brand-*` tokens, link it directly |
| `style/dartdoc.css` | Dart API docs: appended to `dart doc`'s own `styles.css` by ANTfrastructure's `linux/scripts/lib/dartdoc-build.sh` |
| `style/brand.tokens.json` | Anything: `brand.json` with aliases resolved |
| `sphinx-kataglyphis-theme/sphinx_kataglyphis/brand.tokens.json` | Same, shipped inside the pip package |
| `md2pdfLib/style/brand.tokens.json` | Same, reachable from the build container (it mounts only `md2pdfLib/` and `data/`) |

## Reusing the brand in another project

### Python

```bash
pip install -e ./third_party/DocumANTation/sphinx-kataglyphis-theme
```

```python
from sphinx_kataglyphis import brand

brand()["colors"]["accent"]  # the brand accent
brand()["colors"]["link"]  # link colour, light theme
brand()["colors_dark"]["link"]  # ... and dark
brand()["fonts"]["main"]  # 'Roboto'
```

### Sphinx docs

`setup_theme()` already puts the brand stylesheet on `html_static_path` and `html_css_files`;
nothing to copy:

```python
from sphinx_kataglyphis import setup_theme

setup_theme(globals(), repository_url="https://github.com/org/repo")
```

Style your own rules with the tokens, not literals:

```css
.my-thing { color: var(--brand-accent-strong); border: 1px solid var(--brand-surface-border); }
```

`setup_theme()` also points `pygments_light_style` / `pygments_dark_style` at the shared
`kataglyphis-light` / `kataglyphis-dark` styles, so the site's code blocks match the book.
Installing the theme registers them with Pygments, so any Pygments consumer can use them, not
just Sphinx:

```python
from pygments.styles import get_style_by_name

get_style_by_name("kataglyphis-dark")
```

### LaTeX

Put the style directory on the LaTeX search path and `\input` by bare name; a document never
hardcodes a path to this repo:

```bash
TEXINPUTS="/path/to/DocumANTation/md2pdfLib/style:" lualatex mydoc.tex
```

```latex
\input{brand-colors.tex}   % brandAccent, brandLink, linkcolor, basecolor, ...
\input{brand-fonts.tex}    % \brandSetMainFont, \brandSetMonoFont
```

Both files are safe to `\input` more than once. `brand-colors.tex` needs `xcolor` loaded;
`brand-fonts.tex` needs `fontspec`.

### PowerPoint

A pptx takes its colours and fonts only from a `--reference-doc`, a binary deck. Committing one
would put brand values in a file nothing can diff or drift-check, so
`md2pdfLib/presentation/pptx/make_reference.py` builds it from these tokens at build time, by
patching the Office theme inside pandoc's own default reference deck. It is a build artifact,
never committed:

```bash
python md2pdfLib/presentation/pptx/make_reference.py data/out/reference.pptx
```

The twelve Office colour slots are where the brand meets PowerPoint's vocabulary: `accent1` is the
brand accent, `hlink` the brand link. If pandoc changes its default deck's layout, the build fails
loudly instead of emitting a half-branded deck.

### A website that is not Sphinx

Link the standalone token sheet and use the custom properties. Never copy a hex value into the
site; that is how the site ended up one digit off the brand (`#69f0ae` instead of `#6af0ad`):

```html
<link rel="stylesheet" href="brand.css">
```

```css
.loading { background: linear-gradient(45deg, var(--brand-white), var(--brand-accent)); }
```

### Any other language

Read `style/brand.tokens.json` (or the copy inside the installed Python package): plain JSON with
every alias resolved, so no alias support is needed. It carries **every** section of
`brand.json`, the syntax palettes included, so a non-LaTeX, non-Sphinx consumer can match the
book's code colours too:

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

These values live with their document, not in `brand.json`:

- Neutral greys and blacks for CV body text and headings.
- `fonts.mono` names a TeX font (Latin Modern Mono) and is **not** emitted to CSS, because no
  browser has it; the web keeps the generic monospace stack.
- `md2pdfLib/third_party/smile/` is a vendored upstream theme (its own submodule), left alone. Its
  semantic palette (red/blue/…) is not brand; the beamer template remaps only its generic `green`
  to `brandAccentDeep`, because the `examples` blocks use it in a brand-identity role. smile's
  `listings` option (88 lines of `lstdefinestyle` code) is **never activated**:
  `beamerthemeawesome.sty` does not pass `[listings]` to `\RequirePackage{smile}`, so that module
  is dead code in the vendored submodule.

`shadecolor` is no longer per-document: `brand-colors.tex` defines it as `brandSyntaxBg` (the dark
syntax palette bg, `#0d1117`), so every document shares one code-block background.

The upstream CV template's `green`/`red`/`indigo`/`orange`/`monochrome` class options each
hardcoded a `basecolor` that would have overridden the brand accent; they are removed from
`myCV_METADATA.cls`, because the accent is not a per-document choice.
