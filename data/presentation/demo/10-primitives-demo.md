# Primitives demo

::: {.block title="Admonitions from Markdown"}
Write `::: {.note title="..."}` in your slides. The Lua filter maps it
to a beamer `block` environment. No raw LaTeX needed.
:::

::: {.alertblock title="Watch out"}
Common pitfall: barrier stage/access mismatch is the most frequent
Vulkan synchronization bug.
:::

::: {.examples title="Supported types"}
- `note`, `warning`, `tip`, `important` — coloured admonitions
- `definition`, `theorem`, `lemma`, `corollary`, `proof` — math environments
- `block`, `alertblock`, `examples` — beamer blocks (slides only)
- Code blocks with `{.listing title="filename"}` — titled code frames
:::
