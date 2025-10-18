
execute pathogen#infect()

syntax on

set encoding=utf-8
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

let s:vim_ai_endpoint_url = "https://litellm.local.xiam.dev/v1/chat/completions"
let s:vim_ai_token_file_path = "~/.config/litellm.token"

let s:vim_ai_default_model = "anthropic/claude-haiku-4-5"

let s:vim_ai_model_chat = s:vim_ai_default_model
let s:vim_ai_model_edit = s:vim_ai_default_model
let s:vim_ai_model_complete = s:vim_ai_default_model

" vim-ai default settings
let s:vim_ai_max_tokens = 0
let s:vim_ai_max_completion_tokens = 0
let s:vim_ai_enable_auth = 1
let s:vim_ai_request_timeout = 120

" vim-ai general prompt.
let s:vim_ai_prompt =<< trim END
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

let s:vim_ai_chat_prompt = join([s:vim_ai_prompt, s:vim_ai_chat_specific_prompt], "\n")
let s:vim_ai_edit_prompt = join([s:vim_ai_prompt, s:vim_ai_edit_specific_prompt, s:vim_ai_code_prompt], "\n")
let s:vim_ai_prompt_complete = join([s:vim_ai_prompt, s:vim_ai_complete_specific_prompt, s:vim_ai_code_prompt], "\n")

let s:vim_ai_selection_boundary = "\n#####\n"

" :AIChat
let s:vim_ai_chat_config = #{
\  engine: "chat",
\  prompt: "",
\  options: #{
\    model: s:vim_ai_model_chat,
\    endpoint_url: s:vim_ai_endpoint_url,
\    enable_auth: s:vim_ai_enable_auth,
\    token_file_path: s:vim_ai_token_file_path,
\    max_tokens: s:vim_ai_max_tokens,
\    max_completion_tokens: s:vim_ai_max_completion_tokens,
\    stream: 1,
\    selection_boundary: s:vim_ai_selection_boundary,
\    initial_prompt: s:vim_ai_chat_prompt,
\    request_timeout: s:vim_ai_request_timeout,
\  },
\  ui: #{
\    open_chat_command: "preset_tab",
\    scratch_buffer_keep_open: 1,
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
\    endpoint_url: s:vim_ai_endpoint_url,
\    enable_auth: s:vim_ai_enable_auth,
\    token_file_path: s:vim_ai_token_file_path,
\    max_tokens: s:vim_ai_max_tokens,
\    max_completion_tokens: s:vim_ai_max_completion_tokens,
\    stream: 1,
\    selection_boundary: s:vim_ai_selection_boundary,
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
\    endpoint_url: s:vim_ai_endpoint_url,
\    enable_auth: s:vim_ai_enable_auth,
\    token_file_path: s:vim_ai_token_file_path,
\    max_tokens: s:vim_ai_max_tokens,
\    max_completion_tokens: s:vim_ai_max_completion_tokens,
\    stream: 1,
\    selection_boundary: s:vim_ai_selection_boundary,
\    initial_prompt: s:vim_ai_prompt_complete,
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

" Key mappings for vim-ai
let mapleader = " "

" Makes a function global so it can be called from mappings.
" This finds the project root (based on .git) to get a reliable relative path.
function! GetRelativePath()
  let git_root = finddir('.git', expand('%:p:h') . ';')
  if !empty(git_root)
    let project_root = fnamemodify(git_root, ':h')
    " Use resolve() for symlinks and handle Windows paths
    let full_path = resolve(expand('%:p'))
    let root_path = resolve(project_root)
    return substitute(full_path, '^' . escape(root_path, '\') . '[/\\]', '', '')
  else
    return expand('%:.') " Fallback for non-git directories
  endif
endfunction

" Ctrl+J in Normal mode opens a blank chat.
nnoremap <C-J> :AIChat<CR>

" Ctrl+J in Visual mode sends the raw selection for a quick explanation.
vnoremap <C-J> :AIChat Explain this:<CR>

" <leader>af -> AI File: Load the file and ask for a summary.
nnoremap <leader>af :execute '%AIChat Analyze the following file (`' . GetRelativePath() . '`) and provide a one-sentence summary of its purpose.'<CR>

" <leader>as -> AI Selection: Load the selection and ask for a summary.
vnoremap <leader>as :AIChat Analyze this selection and provide a one-sentence summary of its purpose.<CR>

" <leader>ae -> AI Explain: Explain the selected code in detail.
vnoremap <leader>ae :AIChat Explain the following code in detail:<CR>

" <leader>aR -> AI Refactor: Refactor this code selection
vnoremap <leader>aR :AIChat Refactor this code selection for better readability, feel free to use vertical space. Remove superfluous comments, keep only those that are useful. Do not change anything else.<CR>
nnoremap <leader>aR :execute '%AIChat Refactor this file (`' . GetRelativePath() . '`) for better readability. Break long lines, use vertical space, and improve structure. Remove superfluous comments, keep only those that are useful. Do not change functionality or variable names.'<CR>

" <leader>ar -> AI Review (Selection): Code review on the selection.
vnoremap <leader>ar :AIChat Review this code selection for potential issues and improvements. Respond with a concise summary and a numbered list of issues and suggestions.<CR>

" <leader>ac -> AI Complete (File) Review: Code review on the entire file.
nnoremap <leader>ac :execute '%AIChat Perform a thorough code review of the following file (`' . GetRelativePath() . '`). Focus on critical problems first, then suggest improvements. Respond with a concise summary and a numbered list of findings.'<CR>

" <leader>a. -> AI Continue: Continue generating from the last response.
nnoremap <leader>a. :AIChat Please continue where you left off.<CR>

" <leader>al -> AI Learn: Explain like I'm a beginner
vnoremap <leader>al :AIChat Explain this code as if I'm a beginner programmer. Break it down step-by-step with simple terms:<CR>

" <leader>av -> AI Validate: Check for security issues and vulnerabilities
vnoremap <leader>av :AIChat Review this code for security vulnerabilities, potential exploits, or unsafe practices. Be thorough and specific:<CR>

" <leader>aM -> AI Multi: Load multiple files for context
" Usage: Open files in buffers, then run this to load them all
function! LoadAllBuffersToAI()
  let context = "I'm providing multiple files for context:\n\n"
  let buffers = filter(range(1, bufnr('$')), 'buflisted(v:val) && getbufvar(v:val, "&filetype") != ""')

  if empty(buffers)
    echo "No buffers to load. Open some files first."
    return
  endif

  " Check total size to prevent overwhelming the AI
  let total_size = 0
  for buf in buffers
    let total_size += len(join(getbufline(buf, 1, '$'), "\n"))
  endfor

  if total_size > 100000
    let confirm = input('Large context (' . total_size . ' chars). Continue? (y/n): ')
    if confirm != 'y'
      return
    endif
  endif

  for buf in buffers
    " Use getbufline without switching buffers
    let filepath = fnamemodify(bufname(buf), ':.')
    let lines = getbufline(buf, 1, '$')
    let context .= "File: `" . filepath . "`\n\n#####\n" . join(lines, "\n") . "\n#####\n\n"
  endfor

  execute 'AIChat ' . context . 'Describe how these files relate to each other and summarize their overall purpose. Be concise.'
endfunction

nnoremap <leader>aM :call LoadAllBuffersToAI()<CR>

" <leader>ad -> AI Review diff: Review unstaged changes
" <leader>aS -> AI Review staged: Review staged changes (capital S to avoid conflict)
function! ReviewGitDiff(staged)
  " Get the appropriate diff
  if a:staged
    let diff_output = system('git diff --cached ' . shellescape(expand('%:p')))
    let diff_type = "staged changes"
  else
    let diff_output = system('git diff ' . shellescape(expand('%:p')))
    let diff_type = "unstaged changes"
  endif

  " Check if there's actually a diff
  if empty(diff_output)
    echo "No " . diff_type . " to review in this file"
    return
  endif

  " Check for git errors
  if v:shell_error != 0
    echo "Error getting git diff. Is this file in a git repository?"
    return
  endif

  " Build the prompt with the diff
  let prompt = "Review the following git " . diff_type . " for the file `" . GetRelativePath() . "`:\n\n"
  let prompt .= "```diff\n" . diff_output . "\n```\n\n"
  let prompt .= "Please provide:\n"
  let prompt .= "1. Potential bugs or issues\n"
  let prompt .= "2. Code improvement suggestions\n"
  let prompt .= "3. Any security concerns\n"
  let prompt .= "Be concise and specific."

  " Send to AI with proper escaping
  execute 'AIChat ' . prompt
endfunction

nnoremap <leader>ad :call ReviewGitDiff(0)<CR>
nnoremap <leader>aS :call ReviewGitDiff(1)<CR>

" <leader>aD -> AI Git review: Review ALL uncommitted changes in the repo
function! ReviewAllGitChanges()
  let diff_output = system('git diff')

  if empty(diff_output)
    echo "No uncommitted changes in the repository"
    return
  endif

  if v:shell_error != 0
    echo "Error getting git diff. Are you in a git repository?"
    return
  endif

  " For large diffs, warn the user
  let line_count = len(split(diff_output, '\n'))
  let char_count = len(diff_output)
  if line_count > 500 || char_count > 50000
    let confirm = input('Large diff (' . line_count . ' lines, ' . char_count . ' chars). Continue? (y/n): ')
    if confirm != 'y'
      return
    endif
  endif

  let prompt = "Review all uncommitted changes in this repository and provide a summary:\n\n"
  let prompt .= "```diff\n" . diff_output . "\n```\n\n"
  let prompt .= "Provide:\n"
  let prompt .= "1. Summary of changes\n"
  let prompt .= "2. Any potential issues\n"
  let prompt .= "3. Suggested commit message\n"

  execute 'AIChat ' . prompt
endfunction

nnoremap <leader>aD :call ReviewAllGitChanges()<CR>

" <leader>aq -> AI Question: Ask for a professional opinion
vnoremap <leader>aq :AIChat What do you think about this draft?<CR>
nnoremap <leader>aq :execute '%AIChat What do you think about the draft in this file (`' . GetRelativePath() . '`)?'<CR>

" Model selection mappings - using AI namespace to avoid conflicts
" <leader>aC -> Chat with Claude model
nnoremap <leader>aC :AIChat /claude<Space>
vnoremap <leader>aC :AIChat /claude<Space>

" <leader>aO -> Chat with OpenAI model
nnoremap <leader>aO :AIChat /openai<Space>
vnoremap <leader>aO :AIChat /openai<Space>

" <leader>aG -> Chat with Gemini model
nnoremap <leader>aG :AIChat /gemini<Space>
vnoremap <leader>aG :AIChat /gemini<Space>

" <leader>aL -> Chat with LLaMA model
nnoremap <leader>aL :AIChat /llama<Space>
vnoremap <leader>aL :AIChat /llama<Space>

" <leader>ax -> Stop the current AI response
nnoremap <leader>ax :AIStopChat<CR>
vnoremap <leader>ax :AIStopChat<CR>

" <leader>a, -> Rerun the last AI command
nnoremap <leader>a, :AIRedo<CR>
vnoremap <leader>a, :AIRedo<CR>

" <leader>ah -> Show help for key mappings
function! ShowAIHelp()
  " Create a new scratch buffer for the help content
  new
  setlocal buftype=nofile bufhidden=wipe noswapfile nowrap
  setlocal filetype=markdown

  " Add the help content
  let help_text = [
    \ '# vim-ai Key Mappings Help',
    \ '',
    \ '## Quick Access',
    \ '`<C-J>`         Open AI chat (normal) / Explain selection (visual)',
    \ '',
    \ '## File Operations',
    \ '`<leader>af`    **A**I **F**ile - Summarize entire file',
    \ '`<leader>ac`    **A**I **C**omplete review - Full code review of file',
    \ '`<leader>aR`    **A**I **R**efactor - Refactor file/selection for readability',
    \ '',
    \ '## Selection Operations (Visual Mode)',
    \ '`<leader>as`    **A**I **S**election - Summarize selected code',
    \ '`<leader>ae`    **A**I **E**xplain - Explain selection in detail',
    \ '`<leader>ar`    **A**I **r**eview - Review selected code',
    \ '`<leader>al`    **A**I **L**earn - Explain like I''m a beginner',
    \ '`<leader>av`    **A**I **V**alidate - Check for security issues',
    \ '`<leader>aq`    **A**I **Q**uestion - Get opinion on draft',
    \ '',
    \ '## Git Integration',
    \ '`<leader>ad`    **A**I **d**iff - Review unstaged changes in file',
    \ '`<leader>aS`    **A**I **S**taged - Review staged changes in file',
    \ '`<leader>aD`    **A**I **D**iff all - Review ALL uncommitted changes',
    \ '',
    \ '## Multi-File Context',
    \ '`<leader>aM`    **A**I **M**ulti - Load all open buffers for context',
    \ '',
    \ '## Model Selection',
    \ '`<leader>aC`    Chat with **C**laude',
    \ '`<leader>aO`    Chat with **O**penAI',
    \ '`<leader>aG`    Chat with **G**emini',
    \ '`<leader>aL`    Chat with **L**LaMA',
    \ '',
    \ '## Control Commands',
    \ '`<leader>a.`    Continue last response',
    \ '`<leader>a,`    Redo last AI command',
    \ '`<leader>ax`    Stop current AI response',
    \ '',
    \ '## Close Help',
    \ 'Press `q` to close this help window',
    \ ]

  " Insert the help text
  call setline(1, help_text)

  " Set cursor at the top and make buffer non-modifiable
  normal! gg
  setlocal nomodifiable

  " Map 'q' to close the help buffer
  nnoremap <buffer> q :close<CR>

  " Set nice colors if available
  if has('syntax')
    syntax match AIHelpHeader /^#.*/
    syntax match AIHelpKey /`[^`]*`/
    syntax match AIHelpBold /\*\*[^*]*\*\*/

    hi def link AIHelpHeader Title
    hi def link AIHelpKey Identifier
    hi def link AIHelpBold Statement
  endif
endfunction

" Command to show help
command! AIHelp call ShowAIHelp()

" Mapping to show help
nnoremap <leader>ah :AIHelp<CR>
