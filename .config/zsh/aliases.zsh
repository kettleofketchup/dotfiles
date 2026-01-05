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
else
  alias ls='ls --color=auto'
  alias tree='tree --color=auto'
fi


if command -v bat >/dev/null 2>&1; then
  alias cat='bat --style=header,header-filename,header-filesize,grid'
fi

if command -v rg >/dev/null 2>&1; then
  alias grep='rg'
fi
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

# get top process eating memory
alias psmem='ps auxf | sort -nr -k 4 | head -5'

# get top process eating cpu ##
alias pscpu='ps auxf | sort -nr -k 3 | head -5'

# systemd
alias mach_list_systemctl="systemctl list-unit-files --state=enabled"

case "$(uname -s)" in

Darwin)
	# echo 'Mac OS X'
	alias ls='ls -G'
	;;

Linux)
	alias ls='ls --color=auto'
	;;

CYGWIN* | MINGW32* | MSYS* | MINGW*)
	# echo 'MS Windows'
	;;
*)
	# echo 'Other OS'
	;;
esac
