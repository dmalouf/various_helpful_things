set number
set nocompatible
syntax on
""set clipboard=unnamedplus

set tabstop=4
set softtabstop=4

""colorscheme elflord
if exists('$TMUX')
  set term=screen-256color
endif

" Add file-name to status-bar
set laststatus=2
set statusline+=%F\ %M\ %Y\ %R
set statusline+=%=
set statusline+=row:\ %l\ col:\ %c\ percent:\ %p

" Because vim likes to mess with Python files
autocmd Filetype python setlocal expandtab! tabstop=4 shiftwidth=4

filetype plugin indent on

" Add highlighting if/when using 'vimdiff'
if &diff
    highlight! link DiffText MatchParen
endif


" ### TMUX stuff (from tangosource.com/blog/a-tmux-crash-course-tips-and-tweaks/)

" # Let cursor change when in TMUX (vs. staying a big block)
if exists('$ITERM_PROFILE')
  if exists('$TMUX') 
    let &t_SI = "\<Esc>[3 q"
	let &t_EI = "\<Esc>[0 q"
  else
    let &t_SI = "\<Esc>]50;CursorShape=1\x7"
    let &t_EI = "\<Esc>]50;CursorShape=0\x7"
  endif
end

" # paste/nopaste depending on in or out of TMUX
function! WrapForTmux(s)
  if !exists('$TMUX')
    return a:s
  endif

  let tmux_start = "\<Esc>Ptmux;"
  let tmux_end = "\<Esc>\\"

  return tmux_start . substitute(a:s, "\<Esc>", "\<Esc>\<Esc>", 'g') . tmux_end
endfunction

let &t_SI .= WrapForTmux("\<Esc>[?2004h")
let &t_EI .= WrapForTmux("\<Esc>[?2004l")

function! XTermPasteBegin()
  set pastetoggle=<Esc>[201~
  set paste
  return ""
endfunction

inoremap <special> <expr> <Esc>[200~ XTermPasteBegin()

" From https://catonmat.net/sudo-vim -- this makes ':sudow' write (like ':w') the current file
"   even if one did not open the current file with sudo, fixed by https://vi.stackexchange.com/a/22743
cabbrev <expr> sudow getcmdtype() ==# ':' && getcmdline() ==# 'sudow' ? 'w !sudo tee % >/dev/null' : 'sudow'


 

" ### end TMUX stuff (from tangosource.com/blog/a-tmux-crash-course-tips-and-tweaks/)

" Store 'undo' history in a specific folder
set undofile
set undodir=~/.vim/undo_history


" Python-specific tabs/spaces/line-endings. From: https://realpython.com/vim-and-python-a-match-made-in-heaven/
au BufNewFile, BufRead *.py
    \ set tabstop=4
    \ set softtabstop=4
    \ set shiftwidth=4
	\ set textwidth=120
    \ set expandtab
    \ set autoindent
    \ set fileformat=unix


