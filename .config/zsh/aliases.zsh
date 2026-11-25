#!/bin/sh

alias nvimrc='nvim ~/.config/nvim/'
alias nman='bob'
alias sshk="kitty +kitten ssh"
# alias lvim="env TERM=wezterm lvim"
# alias nvim="env TERM=wezterm nvim"

# Colorize grep output (good for log files)
#!/bin/zsh

if command -v lsd >/dev/null 2>&1; then
  alias ls="lsd --config-file=\"$HOME/.ls.config\""
  alias tree='lsd --tree --config-file="$HOME/.ls.config"'
fi
if command -v bat >/dev/null 2>&1; then
  alias cat='bat --style=header,header-filename,header-filesize,grid'
fi

# if command -v rg >/dev/null 2>&1; then
#   alias grep='rg'
# fi
if command -v fd >/dev/null 2>&1; then
  alias find='fd'
fi


if command -v neovim >/dev/null 2>&1; then
  	alias vim ='neovim'
  	alias vi ='neovim'
	alias v ='neovim'
elif command -v nvim >/dev/null 2>&1; then
  alias vim='nvim'
  alias vi='nvim'
	alias v='nvim'
elif command -v vim >/dev/null 2>&1; then
  alias vi='vim'
	alias v='vim'
elif command -v vi >/dev/null 2>&1; then
	alias v='vi'
fi

alias egrep='egrep --color=auto'
alias fgrep='fgrep --color=auto'

alias c='clear'

if command -v nvim >/dev/null; then
  alias v='nvim'
else
  alias v='vim'
fi

if command -v just >/dev/null; then
  alias j='just'

fi
# get top process eating memory
alias psmem='ps auxf | sort -nr -k 4 | head -5'

# get top process eating cpu ##
alias pscpu='ps auxf | sort -nr -k 3 | head -5'

# systemd
alias mach_list_systemctl="systemctl list-unit-files --state=enabled"


# hunk PR review. `hunk gh pr` can't list PRs and ignores the gh login, so pick
# with fzf and hand it gh's token (needed for private repos and viewed-mark sync).
#   hpr            pick from open PRs in this repo
#   hpr -r         pick from PRs requesting your review, across all repos
#   hpr 123        open PR 123 directly
hunk() { GH_TOKEN="${GH_TOKEN:-$(gh auth token 2>/dev/null)}" command hunk "$@"; }
hpr() {
  if [[ -n $1 && $1 != -r ]]; then hunk gh pr "$@"; return; fi
  local pick
  if [[ $1 == -r ]]; then
    pick=$(gh search prs --review-requested=@me --state=open --limit 100 \
        --json url,repository,number,title,author \
        --template '{{range .}}{{.url}}{{"\t"}}{{.repository.nameWithOwner}}#{{.number}}{{"\t"}}{{.author.login}}{{"\t"}}{{.title}}{{"\n"}}{{end}}' |
      fzf --delimiter='\t' --with-nth=2.. --preview 'gh pr view {1}' --preview-window=right,60%,wrap) || return
  else
    pick=$(gh pr list --limit 100 \
        --json number,title,author,headRefName \
        --template '{{range .}}{{.number}}{{"\t"}}{{.author.login}}{{"\t"}}{{.headRefName}}{{"\t"}}{{.title}}{{"\n"}}{{end}}' |
      fzf --delimiter='\t' --preview 'gh pr view {1}' --preview-window=right,60%,wrap) || return
  fi
  hunk gh pr "${pick%%$'\t'*}"
}
