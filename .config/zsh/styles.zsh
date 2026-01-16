
local extract="
in=\${\${\"\$(<{f})\"%\$'\0'*}#*\$'\0'}
local -A ctxt=(\"\${(@ps:\2:)CTXT}\")
"
# Completion styling
zstyle ':completion:*' matcher-list 'm:{a-z}={A-Za-z}'
zstyle ':completion:*:descriptions' format "%U%B%d%b%u"
zstyle ':completion:*:messages' format "%F{green}%d%f"

#zstyle ':completion:*:descriptions' format '[%d]'
zstyle ':completion:*' list-colors "${(s.:.)LS_COLORS}"
zstyle ':completion:*:warnings' format ' %F{red}-- no matches found --%f'


zstyle ':completion:*' menu no
zstyle ':fzf-tab:*' fzf-command ftb-tmux-popup


# zstyle ':fzf-tab:*' show-group full

# zstyle ':fzf-tab:*' single-group full
# zstyle ':fzf-tab:*' prefix ''
# bindkey '\t' expand-or-complete # fzf-tab reads it during initialization



LSD_COMMAND_PREVIEW='lsd --tree --depth 1 --group-directories-first --color=always --icon=always $realpath'
CAT_COMMAND_PREVIEW='bat --pager=never --color=always --line-range 0:30 $realpath'


export NORMAL_MODE_TEXT_DEFAULT="🧭"
export INSERT_MODE_TEXT_DEFAULT="✏️"

zstyle ':fzf-tab:*' use-fzf-default-opts yes
# switch group using `<` and `>`
zstyle ':fzf-tab:*' switch-group '<' '>'

zstyle ':fzf-tab:*' fzf-command ftb-tmux-popup

zstyle ':fzf-tab:*' popup-min-size 400 400

zstyle ':fzf-tab:*' fzf-command ftb-tmux-popup

# compdef _gnu_generic ssh


zstyle ':fzf-tab:complete:ln:*' fzf-preview 'fzf.zsh $realpath'
zstyle ':fzf-tab:complete:file:*' fzf-preview 'fzf.zsh $realpath'
zstyle ':fzf-tab:complete:mv:*' fzf-preview 'fzf.zsh $realpath'
zstyle ':fzf-tab:complete:pip:*' fzf-preview 'fzf.zsh $realpath'
zstyle ':fzf-tab:complete:cd:*' fzf-preview 'fzf.zsh $realpath'
zstyle ':fzf-tab:complete:__zoxide_z:*' fzf-preview 'fzf.zsh $realpath'
zstyle ':fzf-tab:complete:zoxide:*' fzf-preview 'fzf.zsh $realpath'
zstyle ':fzf-tab:complete:z:*' fzf-preview 'fzf.zsh $realpath'
zstyle ':fzf-tab:complete:ls:*' fzf-preview 'fzf.zsh $realpath'
zstyle ':fzf-tab:complete:lsd:*' fzf-preview 'fzf.zsh $realpath'

zstyle ':fzf-tab:complete:cat:*' fzf-preview 'fzf.zsh $realpath'

zstyle ':fzf-tab:complete:bat:*' fzf-preview 'fzf.zsh $realpath'
zstyle ':fzf-tab:complete:systemctl-*:*' fzf-preview 'SYTSTEMD_COLORS=1 systemctl status $word'
zstyle ':fzf-tab:complete:kill:argument-rest' extra-opts --preview=$extract'ps --pid=$in[(w)1] -o cmd --no-headers -w -w' --preview-window=down:3:wrap

zstyle ':completion:*:*:(|g)make::targets' call-command true
zstyle ':completion:*:*:(|g)make:*' tag-order targets

# eval "$(fzf --zsh)"
eval "$(zoxide init --cmd z zsh)"


