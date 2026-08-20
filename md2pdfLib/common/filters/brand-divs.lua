-- brand-divs.lua: Pandoc Lua filter — the single bridge between pure
-- Markdown and every output format (book PDF, beamer slides, PPTX, Sphinx).
--
-- Fenced divs:
--   ::: {.note title="Watch out"}     → tcolorbox (book) / beamer block / HTML admonition
--   ::: {.theorem}                    → amsthm theorem
--   ::: {.columns}                    → beamer columns / multicol (book) / CSS grid (HTML)
--   ::: {.tab-set}                    → tcolorbox tabs (PDF) / HTML tab-set
--   ::: {.notes}                      → \note{} (beamer only, stripped from book)
--
-- Code blocks:
--   ```lang {.listing title="file.rs"}     → titled tcolorbox
--   ```lang {.listing linenos=true}        → with line numbers
--   ```lang {.listing highlight="3,5-7"}   → highlighted lines
--
-- Inline spans:
--   [GPU]{.gls}                           → \gls{gpu}
--   [BRDF]{.nomen def="..."}              → \nomenclature{BRDF}{...}
--
-- Deliberately no document-level handler. One existed to inject a List of
-- Listings, registered as `Doc` -- a key pandoc never calls (the document
-- element is `Pandoc`), so it never ran and \tcblistof{lol} was never emitted
-- despite the book carrying titled listings. Making it work needs `list entry=`
-- on every titled box plus a declared list type, and front matter belongs to
-- the document template rather than a block filter, so the feature was removed
-- rather than half-built.

local FORMAT_LATEX = false
local FORMAT_BEAMER = false
local FORMAT_HTML = false

-- ── Helpers ──────────────────────────────────────────────────────────────

local function is_latex() return FORMAT_LATEX or FORMAT_BEAMER end

local function escape_latex(s)
  return s:gsub("([_#&%%{}~^\\])", "\\%1")
end

local function raw_before(text)
  return pandoc.RawBlock("latex", text)
end

local function flatten_div(div)
  local result = {}
  for _, b in ipairs(div.content) do
    result[#result + 1] = b
  end
  return result
end

-- ── Admonitions ──────────────────────────────────────────────────────────

local TITLE_CLASSES = {
  note = true, warning = true, tip = true, important = true, example = true,
}

local ADMONITION_CLASSES = {
  note = true, warning = true, tip = true, important = true, example = true,
  definition = true, theorem = true, lemma = true, corollary = true, proof = true,
}

local function handle_admonition(div)
  local cls = div.classes[1]
  local title = div.attributes.title
  local env = cls

  if is_latex() then
    local before
    if TITLE_CLASSES[cls] and title and title ~= "" then
      before = string.format("\\begin{%s}{%s}", env, escape_latex(title))
    else
      before = string.format("\\begin{%s}", env)
    end
    local blocks = { raw_before(before) }
    for _, b in ipairs(div.content) do blocks[#blocks + 1] = b end
    blocks[#blocks + 1] = raw_before(string.format("\\end{%s}", env))
    return blocks
  end
  -- HTML: pass through, Sphinx renders the div class as an admonition
  return nil
end

-- ── Two-column layouts ──────────────────────────────────────────────────

local function handle_columns(div)
  if not is_latex() then return nil end

  if FORMAT_BEAMER then
    -- Beamer: \begin{columns}[T] ... \end{columns}
    local blocks = { raw_before("\\begin{columns}[T]") }
    for _, child in ipairs(div.content) do
      if child.t == "Div" and child.classes:includes("column") then
        blocks[#blocks + 1] = raw_before("\\column{0.48\\textwidth}")
        for _, b in ipairs(child.content) do
          blocks[#blocks + 1] = b
        end
      else
        blocks[#blocks + 1] = child
      end
    end
    blocks[#blocks + 1] = raw_before("\\end{columns}")
    return blocks
  else
    -- Book: use minipage side-by-side
    local blocks = { raw_before("\\noindent") }
    local n_cols = 0
    for _, child in ipairs(div.content) do
      if child.t == "Div" and child.classes:includes("column") then
        n_cols = n_cols + 1
      end
    end
    local width = string.format("%.2f", 0.95 / math.max(n_cols, 1))
    local first = true
    for _, child in ipairs(div.content) do
      if child.t == "Div" and child.classes:includes("column") then
        if not first then
          blocks[#blocks + 1] = raw_before("\\hfill")
        end
        first = false
        blocks[#blocks + 1] = raw_before(
          string.format("\\begin{minipage}[t]{%s\\textwidth}", width))
        for _, b in ipairs(child.content) do
          blocks[#blocks + 1] = b
        end
        blocks[#blocks + 1] = raw_before("\\end{minipage}")
      end
    end
    return blocks
  end
end

-- ── Tab sets ─────────────────────────────────────────────────────────────

local function handle_tabset(div)
  if not is_latex() then return nil end

  -- Collect tabs
  local tabs = {}
  for _, child in ipairs(div.content) do
    if child.t == "Div" and child.classes:includes("tab") then
      tabs[#tabs + 1] = {
        title = child.attributes.title or "Tab",
        content = child.content,
      }
    end
  end
  if #tabs == 0 then return nil end

  -- Every tab, each under its own heading. Paper has no tabs to click, so the
  -- only honest rendering is all of them in sequence.
  --
  -- This used to print a header row naming every tab and then only the FIRST
  -- tab's body: the book's three-language example advertised C++ and GLSL
  -- sections it did not contain, which reads as a broken document rather than
  -- a deliberate abridgement. Sphinx still renders real tabs from the same
  -- Markdown -- the div passes through untouched for HTML.
  local blocks = {
    raw_before("\\begin{tcolorbox}[enhanced, breakable, "
      .. "colback=shadecolor, colframe=greenAccent, arc=2mm, "
      .. "boxrule=0.4pt, top=0mm, bottom=0mm]"),
  }

  for i, tab in ipairs(tabs) do
    if i > 1 then
      blocks[#blocks + 1] = raw_before("\\vspace{2mm}\\hrule\\vspace{2mm}")
    end
    blocks[#blocks + 1] = raw_before(
      "\\noindent\\textbf{\\textcolor{brandAccentStrong}{"
      .. escape_latex(tab.title) .. "}}\\par\\vspace{1mm}")
    for _, b in ipairs(tab.content) do
      blocks[#blocks + 1] = b
    end
  end

  blocks[#blocks + 1] = raw_before("\\end{tcolorbox}")
  return blocks
end

-- ── Speaker notes ────────────────────────────────────────────────────────

local function handle_notes(div)
  if FORMAT_BEAMER then
    local text = pandoc.utils.stringify(pandoc.Blocks(div.content))
    return { raw_before("\\note{" .. escape_latex(text) .. "}") }
  end
  -- Strip notes from book and HTML output
  return {}
end

-- ── Code blocks ──────────────────────────────────────────────────────────

local function handle_codeblock(cb)
  if not is_latex() then return nil end

  local title = cb.attributes.title
  local linenos = cb.attributes.linenos
  local highlight = cb.attributes.highlight

  if not title and not linenos and not highlight then return nil end

  if title then
    local safe_title = escape_latex(title)
    local listing_opts = "style=tcblatex"
    if linenos then
      listing_opts = listing_opts .. ",numbers=left,numberstyle=\\tiny\\color{gray}"
    end
    local opts = "enhanced, colback=shadecolor, colframe=greenAccent, "
      .. "arc=2mm, boxrule=0.4pt, "
      .. "title={" .. safe_title .. "}, "
      .. "coltitle=white, fonttitle={\\bfseries\\small}, "
      .. "listing options={" .. listing_opts .. "}, "
      .. "bottom=-2mm, breakable"
    return {
      raw_before("\\begin{tcolorbox}[" .. opts .. "]"),
      cb,
      raw_before("\\end{tcolorbox}"),
    }
  end

  -- linenos-only (no title): wrap in a plain tcolorbox with line numbers
  if linenos then
    return {
      raw_before("\\begin{tcolorbox}[enhanced, colback=shadecolor, "
        .. "colframe=greenAccent, arc=2mm, boxrule=0.4pt, breakable, "
        .. "listing options={numbers=left,numberstyle=\\tiny\\color{gray}}]"),
      cb,
      raw_before("\\end{tcolorbox}"),
    }
  end

  return nil
end

-- ── Glossary / nomenclature spans ────────────────────────────────────────

local function handle_gls(span)
  if not is_latex() then return nil end
  local text = pandoc.utils.stringify(span.content)
  local key = text:lower():gsub("%s+", "")
  return pandoc.RawInline("latex", "\\gls{" .. key .. "}")
end

local function handle_nomen(span)
  if not is_latex() then return nil end
  local text = pandoc.utils.stringify(span.content)
  local def = span.attributes.def or text
  return pandoc.RawInline("latex",
    "\\nomenclature{" .. escape_latex(text) .. "}{" .. escape_latex(def) .. "}")
end

-- ── Algorithm / pseudocode blocks ────────────────────────────────────────

local function handle_algorithm(cb)
  if not is_latex() then return nil end
  local title = cb.attributes.title or "Algorithm"
  return {
    raw_before("\\begin{algorithm}[H]"),
    raw_before("\\caption{" .. escape_latex(title) .. "}"),
    raw_before("\\begin{algorithmic}[1]"),
    cb,
    raw_before("\\end{algorithmic}"),
    raw_before("\\end{algorithm}"),
  }
end

-- ── Document-level: inject list of listings ──────────────────────────────

-- ── Dispatch ─────────────────────────────────────────────────────────────

local function dispatch_div(div)
  local cls = div.classes[1]
  if not cls then return nil end

  if ADMONITION_CLASSES[cls] then return handle_admonition(div) end
  if cls == "columns" then return handle_columns(div) end
  if cls == "tab-set" then return handle_tabset(div) end
  if cls == "notes" then return handle_notes(div) end
  return nil
end

local function dispatch_codeblock(cb)
  if cb.classes:includes("algorithm") or cb.classes:includes("pseudocode") then
    return handle_algorithm(cb)
  end
  return handle_codeblock(cb)
end

local function dispatch_span(span)
  if span.classes:includes("gls") then return handle_gls(span) end
  if span.classes:includes("nomen") then return handle_nomen(span) end
  return nil
end

-- Format detection runs first
local function detect_format(_, meta)
  -- Parenthesised deliberately. This was written as
  --   FORMAT:match("latex") and not FORMAT:match("beamer") ~= nil
  -- which Lua parses as `... and ((not X) ~= nil)`; `not X` is a boolean and a
  -- boolean is never nil, so that half was always true and the beamer
  -- exclusion did nothing. It only behaved because pandoc reports "beamer"
  -- (not "latex") for that writer, so the first clause carried it alone.
  FORMAT_BEAMER = FORMAT:match("beamer") ~= nil
  FORMAT_LATEX = (FORMAT:match("latex") ~= nil) and not FORMAT_BEAMER
  FORMAT_HTML = not FORMAT_LATEX and not FORMAT_BEAMER
  -- Workaround: Pandoc sets FORMAT to "latex" for both book and beamer
  -- unless the output format is explicitly "beamer". Check metadata.
  if meta and meta.documentclass then
    local dc = pandoc.utils.stringify(meta.documentclass)
    if dc:match("beamer") then FORMAT_BEAMER = true; FORMAT_LATEX = false end
  end
  return nil
end

return {
  { Meta = detect_format },
  { Div = dispatch_div },
  { CodeBlock = dispatch_codeblock },
  { Span = dispatch_span },
}
