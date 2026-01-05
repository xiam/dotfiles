# dotfiles

The settings I use for development.

This is my preferred stack:

* [zsh](http://www.zsh.org/)
* [vim](http://www.vim.org/)
* [tmux](http://tmux.sourceforge.net/)
* [git](http://git-scm.com/)

I have been using these tools for a long time and I am very happy with them.
Nothing fancy, just what I need and works for me.

## Installation

```
git clone https://github.com/xiam/dotfiles.git
cd dotfiles
make
```

## Quick Reference

### Vim

#### Tabs

| Key | Action |
|-----|--------|
| `Ctrl+T` | New tab (with file browser) |
| `Ctrl+N` | Next tab |
| `Ctrl+P` | Previous tab |

#### Splits

| Key | Action |
|-----|--------|
| `Ctrl+W \|` | Vertical split |
| `Ctrl+W -` | Horizontal split |
| `Ctrl+h/j/k/l` | Navigate splits (left/down/up/right) |
| `Ctrl+W p` | Previous split (last accessed) |
| `Ctrl+Q` | Close split |

#### Editing

| Key | Action |
|-----|--------|
| `jk` | Escape insert mode |
| `<Space>w` | Quick save |
| `<Space>/` | Clear search highlight |
| `u` | Undo |
| `Ctrl+R` | Redo |

#### vim-ai

| Key | Action |
|-----|--------|
| `Ctrl+J` | Open AI chat / Explain selection |
| `<Space>af` | Summarize file |
| `<Space>ar` | Review selection |
| `<Space>aR` | Refactor file/selection |
| `<Space>ad` | Review unstaged diff |
| `<Space>aS` | Review staged diff |
| `<Space>aC` | Chat with Claude |
| `<Space>aG` | Chat with Gemini |
| `<Space>ax` | Stop AI response |
| `<Space>ah` | Show all AI keybindings |

### Tmux

Prefix: `Ctrl+B`

#### Windows

| Key | Action |
|-----|--------|
| `prefix c` | New window |
| `prefix n` | Next window |
| `prefix p` | Previous window |
| `Alt+1-9` | Jump to window (no prefix) |
| `prefix &` | Kill window |

#### Panes

| Key | Action |
|-----|--------|
| `prefix \|` or `%` | Split vertical |
| `prefix -` or `"` | Split horizontal |
| `Alt+h/j/k/l` | Navigate panes (no prefix) |
| `Alt+arrows` | Navigate panes (no prefix) |
| `prefix ;` | Previous pane (last active) |
| `prefix o` | Next pane (cycle) |
| `prefix H/J/K/L` | Resize panes |
| `prefix z` | Toggle pane zoom |
| `prefix S` | Sync panes (type in all) |
| `prefix x` | Kill pane |

#### Session

| Key | Action |
|-----|--------|
| `prefix d` | Detach session |
| `prefix s` | List sessions |
| `prefix $` | Rename session |

#### Other

| Key | Action |
|-----|--------|
| `prefix r` | Reload config |
| `prefix m/M` | Mouse ON/OFF |

#### Copy mode (vi)

| Key | Action |
|-----|--------|
| `prefix [` | Enter copy mode |
| `v` | Begin selection |
| `y` | Copy and exit |
| `q` | Exit copy mode |

### Git

| Alias | Command |
|-------|---------|
| `git st` | `status -sb` |
| `git co` | `checkout` |
| `git br` | `branch` |
| `git ci` | `commit` |
| `git ca` | `commit --amend` |
| `git lg` | `log --oneline --graph` |
| `git lga` | `log --oneline --graph --all` |
| `git df` | `diff` |
| `git dfs` | `diff --staged` |
| `git unstage` | `reset HEAD --` |
| `git last` | `log -1 HEAD --stat` |
