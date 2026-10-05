" Generated from theme.yml. Do not edit generated files.
set background=dark
hi clear
if exists('syntax_on') | syntax reset | endif
let g:colors_name = 'dotfiles'
let s:gui = &t_Co >= 256 || has('termguicolors')
hi Normal guifg=#dcd7ba guibg=#1f1f28 ctermfg=252 ctermbg=234
hi CursorLine guibg=#363646 ctermbg=236
hi CursorLineNr guifg=#e6c384 guibg=#363646 ctermfg=221 ctermbg=236
hi LineNr guifg=#a6a69c guibg=#1f1f28 ctermfg=145 ctermbg=234
hi Comment guifg=#a6a69c gui=italic ctermfg=145 cterm=italic
hi Constant guifg=#ffa066 ctermfg=215
hi String guifg=#98bb6c ctermfg=149
hi Identifier guifg=#7fb4ca ctermfg=109
hi Function guifg=#7e9cd8 ctermfg=110
hi Statement guifg=#957fb8 ctermfg=140
hi Type guifg=#7fb4ca ctermfg=109
hi Special guifg=#e6c384 ctermfg=221
hi Search guifg=#1f1f28 guibg=#e6c384 ctermfg=234 ctermbg=221
hi Visual guibg=#363646 ctermbg=236
hi Error guifg=#e82424 gui=bold ctermfg=203 cterm=bold
hi WarningMsg guifg=#e6c384 ctermfg=221
hi StatusLine guifg=#dcd7ba guibg=#2a2a37 ctermfg=252 ctermbg=236
hi StatusLineNC guifg=#a6a69c guibg=#1f1f28 ctermfg=145 ctermbg=234
hi VertSplit guifg=#2a2a37 guibg=#1f1f28 ctermfg=236 ctermbg=234
hi MatchParen guifg=#e6c384 gui=bold ctermfg=221 cterm=bold
hi Pmenu guifg=#dcd7ba guibg=#2a2a37 ctermfg=252 ctermbg=236
hi PmenuSel guifg=#1f1f28 guibg=#7e9cd8 ctermfg=234 ctermbg=110
hi NonText guifg=#54546d ctermfg=60
hi EndOfBuffer guifg=#54546d ctermfg=60
