-- Prefix slide titles with section numbers, beamer-style.
--
-- The awesome-beamer theme numbers frametitles itself ("1.4 Markdown-first
-- content"); pandoc's pptx writer has no equivalent, and --number-sections
-- does not touch pptx headings. This filter numbers H1 (sections, "2.") and
-- H2 (slides, "2.1") in the AST, so the slide titles AND the --toc slide both
-- carry the numbers. Applied only to the pptx preset -- beamer numbers itself.
local sec = 0
local sub = 0

function Header(el)
  if el.level == 1 then
    sec = sec + 1
    sub = 0
    el.content:insert(1, pandoc.Space())
    el.content:insert(1, pandoc.Str(sec .. "."))
  elseif el.level == 2 then
    sub = sub + 1
    el.content:insert(1, pandoc.Space())
    el.content:insert(1, pandoc.Str(sec .. "." .. sub))
  end
  return el
end
