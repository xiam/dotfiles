" Tokyo Night colorscheme for Vim
" Minimal version matching tmux/zsh theme

set background=dark
hi clear
if exists("syntax_on")
  syntax reset
endif
let g:colors_name = "tokyo-night"

" Enable truecolor if supported
if has('termguicolors')
  set termguicolors
endif

" Color palette
let s:bg       = "#1a1b26"
let s:bg_light = "#24283b"
let s:fg       = "#a9b1d6"
let s:comment  = "#565f89"
let s:select   = "#3b4261"
let s:blue     = "#7aa2f7"
let s:cyan     = "#7dcfff"
let s:purple   = "#bb9af7"
let s:green    = "#9ece6a"
let s:yellow   = "#e0af68"
let s:orange   = "#ff9e64"
let s:red      = "#f7768e"

" Helper function
function! s:hi(group, fg, bg, attr)
  let cmd = "hi " . a:group
  if a:fg != ""
    let cmd .= " guifg=" . a:fg
  endif
  if a:bg != ""
    let cmd .= " guibg=" . a:bg
  endif
  if a:attr != ""
    let cmd .= " gui=" . a:attr
  endif
  exec cmd
endfunction

" UI Elements
call s:hi("Normal",       s:fg,      s:bg,       "")
call s:hi("NormalFloat",  s:fg,      s:bg_light, "")
call s:hi("Cursor",       s:bg,      s:fg,       "")
call s:hi("CursorLine",   "",        s:bg_light, "none")
call s:hi("CursorLineNr", s:blue,    s:bg_light, "bold")
call s:hi("LineNr",       s:comment, "",         "")
call s:hi("SignColumn",   "",        s:bg,       "")
call s:hi("VertSplit",    s:select,  s:bg,       "")
call s:hi("StatusLine",   s:fg,      s:bg_light, "")
call s:hi("StatusLineNC", s:comment, s:bg_light, "")
call s:hi("TabLine",      s:comment, s:bg_light, "")
call s:hi("TabLineFill",  s:comment, s:bg,       "")
call s:hi("TabLineSel",   s:blue,    s:bg_light, "bold")
call s:hi("Pmenu",        s:fg,      s:bg_light, "")
call s:hi("PmenuSel",     s:bg,      s:blue,     "")
call s:hi("PmenuSbar",    "",        s:select,   "")
call s:hi("PmenuThumb",   "",        s:comment,  "")
call s:hi("Visual",       "",        s:select,   "")
call s:hi("Search",       s:bg,      s:yellow,   "")
call s:hi("IncSearch",    s:bg,      s:orange,   "")
call s:hi("MatchParen",   s:orange,  s:select,   "bold")
call s:hi("Folded",       s:comment, s:bg_light, "")
call s:hi("FoldColumn",   s:comment, s:bg,       "")
call s:hi("ColorColumn",  "",        s:bg_light, "")
call s:hi("NonText",      s:select,  "",         "")
call s:hi("SpecialKey",   s:select,  "",         "")
call s:hi("Directory",    s:blue,    "",         "")
call s:hi("Title",        s:blue,    "",         "bold")
call s:hi("Question",     s:green,   "",         "")
call s:hi("MoreMsg",      s:green,   "",         "")
call s:hi("WarningMsg",   s:yellow,  "",         "")
call s:hi("ErrorMsg",     s:red,     "",         "bold")

" Syntax highlighting
call s:hi("Comment",      s:comment, "",         "italic")
call s:hi("Constant",     s:orange,  "",         "")
call s:hi("String",       s:green,   "",         "")
call s:hi("Character",    s:green,   "",         "")
call s:hi("Number",       s:orange,  "",         "")
call s:hi("Boolean",      s:orange,  "",         "")
call s:hi("Float",        s:orange,  "",         "")
call s:hi("Identifier",   s:fg,      "",         "")
call s:hi("Function",     s:blue,    "",         "")
call s:hi("Statement",    s:purple,  "",         "")
call s:hi("Conditional",  s:purple,  "",         "")
call s:hi("Repeat",       s:purple,  "",         "")
call s:hi("Label",        s:purple,  "",         "")
call s:hi("Operator",     s:cyan,    "",         "")
call s:hi("Keyword",      s:purple,  "",         "")
call s:hi("Exception",    s:purple,  "",         "")
call s:hi("PreProc",      s:cyan,    "",         "")
call s:hi("Include",      s:purple,  "",         "")
call s:hi("Define",       s:purple,  "",         "")
call s:hi("Macro",        s:cyan,    "",         "")
call s:hi("PreCondit",    s:cyan,    "",         "")
call s:hi("Type",         s:cyan,    "",         "")
call s:hi("StorageClass", s:purple,  "",         "")
call s:hi("Structure",    s:cyan,    "",         "")
call s:hi("Typedef",      s:cyan,    "",         "")
call s:hi("Special",      s:cyan,    "",         "")
call s:hi("SpecialChar",  s:orange,  "",         "")
call s:hi("Tag",          s:blue,    "",         "")
call s:hi("Delimiter",    s:fg,      "",         "")
call s:hi("Debug",        s:red,     "",         "")
call s:hi("Underlined",   s:blue,    "",         "underline")
call s:hi("Error",        s:red,     "",         "")
call s:hi("Todo",         s:yellow,  s:bg,       "bold")

" Diff
call s:hi("DiffAdd",      s:green,   s:bg_light, "")
call s:hi("DiffChange",   s:yellow,  s:bg_light, "")
call s:hi("DiffDelete",   s:red,     s:bg_light, "")
call s:hi("DiffText",     s:blue,    s:select,   "")

" Git signs (if using signify or gitgutter)
call s:hi("SignifySignAdd",    s:green,  "", "")
call s:hi("SignifySignChange", s:yellow, "", "")
call s:hi("SignifySignDelete", s:red,    "", "")

" Spell
call s:hi("SpellBad",   s:red,    "", "undercurl")
call s:hi("SpellCap",   s:yellow, "", "undercurl")
call s:hi("SpellLocal", s:cyan,   "", "undercurl")
call s:hi("SpellRare",  s:purple, "", "undercurl")

" Cleanup
delfunction s:hi
