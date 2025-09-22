#!/bin/sh

alias nvimrc='nvim ~/.config/nvim/'
alias nman='bob'
alias sshk="kitty +kitten ssh"
# alias lvim="env TERM=wezterm lvim"
# alias nvim="env TERM=wezterm nvim"


# Colorize grep output (good for log files)
#!/bin/zsh
alias tree='lsd --tree --config-file="$HOME/.ls.config"'
alias cat='bat --style=header,header-filename,header-filesize,grid'
alias vim='nvim'
alias c='clear'


alias grep='grep --color=auto'
alias egrep='egrep --color=auto'
alias fgrep='fgrep --color=auto'




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
