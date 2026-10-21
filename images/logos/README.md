# Repository logos

One logo per Kataglyphis repository: the same rounded tile, a dark tile in the repository's own
colour, the same mint *Cataglyphis* (all six legs on the thorax), and one prop for the topic.
Each repository keeps a copy as `images/logo.svg`, links it from its README header, and renders
its PNG, ICO and BMP icons (packages, app launchers, favicons) from it at the sizes those files
had. Its Sphinx docs set `html_logo` and `html_favicon` to that SVG in `docs/conf.py`, or
`docs/source/conf.py`, after `setup_theme()`, which otherwise sets the theme's shared wireframe.

| Repository | File | Motif |
| --- | --- | --- |
| Kataglyphis (profile) | `kataglyphis.svg` | the Sandläufer badge |
| ANTfrastructure | `antfrastructure.svg` | hauling a shipping container |
| OrchestrANT | `orchestrant.svg` | conducting with a baton |
| ModelANT | `modelant.svg` | a detection box, `ant 0.99` |
| OmniAccelerANT | `omniaccelerant.svg` | a sprint over a lightning bolt |
| AccelerANTgine | `accelerantgine.svg` | latte art |
| BeschleunigerBallett | `beschleunigerballett.svg` | a tutu on the RGB hello triangle |
| AssetANT | `assetant.svg` | the Cornell box |
| DocumANTation | `documantation.svg` | an open book with the ant as its figure |
| ANThology | `anthology.svg` | an app window and a phone |
| OxidANT | `oxidant.svg` | rusted, inside a gear |
| WebDavClient | `webdavclient.svg` | a file carried down from a cloud |
| jotrockenmitlocken | `jotrockenmitlocken.svg` | the portrait, *mit Locken* |

Redraw them with `python scripts/make_repo_logos.py` (stdlib only), then copy each changed file
into its repository's `images/logo.svg` and re-render that repository's icons from it, one
native raster per size (2026-10-21: headless Chromium). The `ant 0.99` label is Roboto Bold as
outlines, so no SVG needs a font.
