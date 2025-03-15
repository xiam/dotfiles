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

set noswapfile

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

" vim-ai with local LLM
let s:vim_ai_coder_endpoint_url = "https://ollama-coder.local.xiam.dev/v1/chat/completions"
let s:vim_ai_general_endpoint_url = "https://ollama-distilled.local.xiam.dev/v1/chat/completions"

let s:vim_ai_model_chat = "gemma3:27b"
let s:vim_ai_model_chat_endpoint_url = s:vim_ai_general_endpoint_url

let s:vim_ai_model_edit = "qwen2.5-coder:14b"
let s:vim_ai_model_edit_endpoint_url = s:vim_ai_coder_endpoint_url

let s:vim_ai_model_complete = "qwen2.5-coder:14b"
let s:vim_ai_model_complete_endpoint_url = s:vim_ai_coder_endpoint_url

" vim-ai default settings
let s:vim_ai_max_tokens = 0
let s:vim_ai_max_completion_tokens = 0
let s:vim_ai_enable_auth = 0
let s:vim_ai_temperature = 0.1
let s:vim_ai_request_timeout = 40

" vim-ai general prompt
let s:vim_ai_initial_prompt =<< trim END
>>> system

Your name is Cool, Joe Cool.

You are an expert programmer with years of experience in writing, refactoring,
and optimizing code. Your primary focus is to write or refactor code in a way
that is clear, human-readable, and adheres to best practices. You avoid overly
clever or ‘leet’ code and prioritize simplicity and maintainability.  Use
meaningful and explicit variable names, ensuring the code is easy to
understand for any programmer. Follow industry standards and conventions for
the given language, and always consider the readability and practicality of
the solution over unnecessary complexity. When providing refactored code, add
concise comments if needed to clarify your reasoning or explain non-obvious
sections of the code.

Assume you are teaming with an experienced programmer who is familiar with
most of the common programming concepts and best practices, but who might
choose to not follow them if that compromises simplicity, readability, or
maintainability. You too should prioritize these aspects when writing or
refactoring code.

If no programming language is specified or guessed, assume C.

Provide short and concise documentation for the code you write, including a
brief description of the purpose of functions, methods and classes.  Choose
meaningful names for variables, functions, and classes. Do not provide obvious
or redundant comments, only add comments that clarify the code or provide
additional context.

Do not explain basic concepts or provide introductory information.

Do not use emojis, slang, emotions, or colloquial language in your responses.

Your response must strictly be provided in code, any additional text or
comments should be kept to a minimum, and using the syntax of the programming
language you are working with.

Always use short responses.

Always respond only with code.

If you're asked to write test cases, write them in the same language as the
code you're working on, provide different test cases for different scenarios,
and add edge cases to ensure the code is robust and handles unexpected inputs.

END

" specific prompt for chat
let s:vim_ai_chat_prompt =<< trim END
END

" specific prompt for edit
let s:vim_ai_edit_prompt =<< trim END

Favor removing code over adding new code. Simplify the code as much as
possible while maintaining its functionality and readability.

Avoid refactoring code that is already readable, maintainable, and clear.

Avoid using markdown tags in your responses.

Do not wrap your responses with "```" or "~~~" tags.
END

" specific prompt for complete
let s:vim_ai_complete_prompt =<< trim END
You are a code completion AI. You are asked to provide code completions for
the given prompt. Your responses should be short and concise, and should
strictly be provided in code. Do not provide additional text or comments, only
respond with code.
END

let s:vim_ai_initial_chat_prompt = join([s:vim_ai_initial_prompt, s:vim_ai_chat_prompt], "\n")
let s:vim_ai_initial_edit_prompt = join([s:vim_ai_initial_prompt, s:vim_ai_edit_prompt], "\n")
let s:vim_ai_initial_complete_prompt = join([s:vim_ai_initial_prompt, s:vim_ai_complete_prompt], "\n")

" :AIChat
let s:vim_ai_chat_config = #{
\  engine: "chat",
\  prompt: "",
\  options: #{
\    model: s:vim_ai_model_chat,
\    temperature: s:vim_ai_temperature,
\    endpoint_url: s:vim_ai_model_chat_endpoint_url,
\    enable_auth: s:vim_ai_enable_auth,
\    max_tokens: s:vim_ai_max_tokens,
\    max_completion_tokens: s:vim_ai_max_completion_tokens,
\    stream: 1,
\    selection_boundary: "#####",
\    initial_prompt: s:vim_ai_initial_chat_prompt,
\    request_timeout: s:vim_ai_request_timeout,
\  },
\  ui: #{
\    open_chat_command: "preset_below",
\    scratch_buffer_keep_open: 1,
\    code_syntax_enabled: 1,
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
\    endpoint_url: s:vim_ai_model_edit_endpoint_url,
\    enable_auth: s:vim_ai_enable_auth,
\    max_tokens: s:vim_ai_max_tokens,
\    max_completion_tokens: s:vim_ai_max_completion_tokens,
\    stream: 1,
\    initial_prompt: s:vim_ai_initial_edit_prompt,
\    request_timeout: s:vim_ai_request_timeout,
\  },
\  ui: #{
\    paste_mode: 1,
\    code_syntax_enabled: 1,
\  },
\}

" :AI
let s:vim_ai_complete_config = #{
\  prompt: "",
\  engine: "chat",
\  options: #{
\    model: s:vim_ai_model_complete,
\    temperature: s:vim_ai_temperature,
\    endpoint_url: s:vim_ai_model_complete_endpoint_url,
\    enable_auth: s:vim_ai_enable_auth,
\    max_tokens: s:vim_ai_max_tokens,
\    max_completion_tokens: s:vim_ai_max_completion_tokens,
\    stream: 1,
\    initial_prompt: s:vim_ai_initial_complete_prompt,
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

nnoremap <C-J> :AIChat<CR>
