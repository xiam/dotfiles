execute pathogen#infect()
syntax on

set encoding=utf-8
set ruler
set nowrap
set nowrapscan

set ai
set modeline
set number

set bs=2

set binary
set ruler
set history=200
set showcmd

set expandtab
set ts=2
set sw=2
set softtabstop=2

setl autoread
set shortmess=a

set hlsearch

nnoremap <C-T> :tabnew<CR>:e .<CR>
nnoremap <C-P> :tabprev<CR>
nnoremap <C-N> :tabnext<CR>
nnoremap <C-V> :vsplit .<CR>
nnoremap <C-H> :split .<CR>
nnoremap <C-Q> :q<CR>

au BufNewFile,BufRead Makefile*,*.go set noexpandtab
au BufWritePost *.go !go fmt <afile>

au BufNewFile,BufRead *.thtml setfiletype php
au BufNewFile,BufRead *.tpl setfiletype php
au BufNewFile,BufRead *.ctp setfiletype php
au BufNewFile,BufRead *.module setfiletype php

au BufRead,BufNewFile *.ino setfiletype arduino
au BufRead,BufNewFile *.pde setfiletype processing

au BufNewFile,BufRead *.markdown,*.mdown,*.mkd,*.mkdn,*.mdwn,*.md  set ft=markdown

au FileType * autocmd BufWritePre <buffer> :%s/\s\+$//e

filetype plugin on

let g:arduino_dir = "$HOME/opt/arduino"
