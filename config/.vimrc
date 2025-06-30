execute pathogen#infect()

syntax on

set encoding=utf-8
set ruler
" set nowrap
set nowrapscan

set ai
set modeline
set number

set bs=2

set binary
set ruler
set history=512
set showcmd

set expandtab
set ts=2
set sw=2
set softtabstop=2

setl autoread
set shortmess=a

set hlsearch

set noswapfile

set wrap linebreak breakindent showbreak=↪\ "
" set textwidth=80

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

au BufNewFile,BufRead *.py
  \ set tabstop=4 |
  \ set softtabstop=4 |
  \ set sw=4 |
  \ set autoindent |
  \ setfiletype python

au FileType * autocmd BufWritePre <buffer> :%s/\s\+$//e

filetype plugin on

let g:arduino_dir = "$HOME/opt/arduino"

let s:vim_ai_general_endpoint_url = "https://litellm.local.xiam.dev/v1/chat/completions"
let s:vim_ai_token_file_path = "~/.config/litellm.token"

let s:vim_ai_model_chat = "openai/o4-mini"
let s:vim_ai_model_edit = s:vim_ai_model_chat
let s:vim_ai_model_complete = s:vim_ai_model_chat

" vim-ai default settings
let s:vim_ai_max_tokens = 0
let s:vim_ai_max_completion_tokens = 0
let s:vim_ai_enable_auth = 1
let s:vim_ai_temperature = 0.1
let s:vim_ai_request_timeout = 120

" vim-ai general prompt.
let s:vim_ai_initial_prompt =<< trim END
You are a programming assistant that helps with coding tasks.
Ensure your responses are clear, concise, and directly address the user's query.
When providing code, use plain text without Markdown formatting unless specifically requested.
If no programming language is specified, assume Python.
END

" specific lines for code-related prompts
let s:vim_ai_code_prompt =<< trim END
Generate code in plain text format without Markdown formatting.
Do not include explanatory text before or after the code.
Do not use code fences (```) or other formatting markers.
If context is necessary, use language-appropriate inline comments.
Your entire response should be valid, executable code.
END

" specific prompt for chat
let s:vim_ai_chat_specific_prompt =<< trim END
I will present you with code or a question, and you should provide helpful analysis, explanations, or answers.
Feel free to use formatting to enhance readability when explaining concepts.
END

" specific prompt for edit
let s:vim_ai_edit_specific_prompt =<< trim END
I will present you with code that needs modification based on specific instructions.
Return the complete modified code, preserving the structure and style of the original.
Highlight or comment on the changes you've made.
END

" specific prompt for complete
let s:vim_ai_complete_specific_prompt =<< trim END
I will provide partial code or a description of what needs to be implemented.
Complete the code in a way that is consistent with the existing style and logic.
Ensure the completed code is functional and follows best practices.
END

let s:vim_ai_chat_prompt = join([s:vim_ai_initial_prompt, s:vim_ai_chat_specific_prompt], "\n")
let s:vim_ai_edit_prompt = join([s:vim_ai_initial_prompt, s:vim_ai_edit_specific_prompt, s:vim_ai_code_prompt], "\n")
let s:vim_ai_complete_prompt = join([s:vim_ai_initial_prompt, s:vim_ai_complete_specific_prompt, s:vim_ai_code_prompt], "\n")

" :AIChat
let s:vim_ai_chat_config = #{
\  engine: "chat",
\  prompt: "",
\  options: #{
\    model: s:vim_ai_model_chat,
\    temperature: s:vim_ai_temperature,
\    endpoint_url: s:vim_ai_general_endpoint_url,
\    enable_auth: s:vim_ai_enable_auth,
\    token_file_path: s:vim_ai_token_file_path,
\    max_tokens: s:vim_ai_max_tokens,
\    max_completion_tokens: s:vim_ai_max_completion_tokens,
\    stream: 1,
\    selection_boundary: "```",
\    initial_prompt: s:vim_ai_chat_prompt,
\    request_timeout: s:vim_ai_request_timeout,
\  },
\  ui: #{
\    open_chat_command: "preset_tab",
\    scratch_buffer_keep_open: 0,
\    code_syntax_enabled: 1,
\    populate_options: 0,
\    force_new_chat: 0,
\    paste_mode: 1,
\  },
\}

" :AIEdit
let s:vim_ai_edit_config = #{
\  engine: "chat",
\  prompt: "",
\  options: #{
\    model: s:vim_ai_model_edit,
\    temperature: s:vim_ai_temperature,
\    endpoint_url: s:vim_ai_general_endpoint_url,
\    enable_auth: s:vim_ai_enable_auth,
\    token_file_path: s:vim_ai_token_file_path,
\    max_tokens: s:vim_ai_max_tokens,
\    max_completion_tokens: s:vim_ai_max_completion_tokens,
\    stream: 1,
\    selection_boundary: "```",
\    initial_prompt: s:vim_ai_edit_prompt,
\    request_timeout: s:vim_ai_request_timeout,
\  },
\  ui: #{
\    paste_mode: 1,
\  },
\}

" :AI
let s:vim_ai_complete_config = #{
\  prompt: "",
\  engine: "chat",
\  options: #{
\    model: s:vim_ai_model_complete,
\    temperature: s:vim_ai_temperature,
\    endpoint_url: s:vim_ai_general_endpoint_url,
\    enable_auth: s:vim_ai_enable_auth,
\    token_file_path: s:vim_ai_token_file_path,
\    max_tokens: s:vim_ai_max_tokens,
\    max_completion_tokens: s:vim_ai_max_completion_tokens,
\    stream: 1,
\    selection_boundary: "```",
\    initial_prompt: s:vim_ai_complete_prompt,
\    request_timeout: s:vim_ai_request_timeout,
\  },
\  ui: #{
\    paste_mode: 1,
\  },
\}

let g:vim_ai_chat = s:vim_ai_chat_config
let g:vim_ai_complete = s:vim_ai_complete_config
let g:vim_ai_edit = s:vim_ai_edit_config

let g:vim_ai_roles_config_file = '~/.config/vim-ai/roles.ini'

"let g:vim_ai_debug_log_file = "/tmp/vim_ai_debug.log"
"let g:vim_ai_debug = 1

nnoremap <C-J> :AIChat<CR>
