

### Added by Zinit's installer
if [[ ! -f $HOME/.local/share/zinit/zinit.git/zinit.zsh ]]; then
    print -P "%F{33} %F{220}Installing %F{33}ZDHARMA-CONTINUUM%F{220} Initiative Plugin Manager (%F{33}zdharma-continuum/zinit%F{220})…%f"
    command mkdir -p "$HOME/.local/share/zinit" && command chmod g-rwX "$HOME/.local/share/zinit"
    command git clone https://github.com/zdharma-continuum/zinit "$HOME/.local/share/zinit/zinit.git" && \
        print -P "%F{33} %F{34}Installation successful.%f%b" || \
        print -P "%F{160} The clone has failed.%f%b"
    echo "export PATH=\"$HOME/.local/share/zinit/polaris/bin:$PATH\"" >> "$HOME/.bashrc"
fi


# Load zinit
source ${XDG_DATA_HOME:-$HOME/.local/share}/zinit/zinit.git/zinit.zsh
zinit light-mode for \
    zdharma-continuum/zinit-annex-as-monitor \
    zdharma-continuum/zinit-annex-bin-gem-node \
    zdharma-continuum/zinit-annex-patch-dl \
    zdharma-continuum/zinit-annex-rust
autoload -Uz _zinit
(( ${+_comps} )) && _comps[zinit]=_zinit

# Load a few important annexes, without Turbo
# (this is currently required for annexes)



### End of Zinit's installer chunk
export PATH=$HOME/bin:/usr/local/bin:$PATH
local sanitized_in='${~ctxt[hpre]}"${${in//\\ / }/#\~/$HOME}"'

setopt promptsubst
PS1="READY >" # provide a simple prompt till the theme loads
zinit light Aloxaf/fzf-tab

zinit as"null" wait lucid from"gh-r" for \
    sbin"lsd"     lsd-rs/lsd \
    sbin"fd"      @sharkdp/fd \
    sbin"bat" atclone"./bat*/bat --completion zsh > _bat" atpull"%atclone" as"completion"     @sharkdp/bat \
    sbin"fzf"     junegunn/fzf \
    sbin"rg" atclone"./rip*/rg --generate=complete-zsh > _rg" atpull"%atclone" as"completion"     @BurntSushi/ripgrep \
    sbin"kettle"  kettleofkethchup/kettle



zinit for \
    atclone'golangci-lint completion zsh > _golangci-lint' \
    from'gh-r' \
    sbin'golangci-lint' \
  @golangci/golangci-lint

zinit ice as"program" pick"yank" make
zinit light mptre/yank    

zinit for \
    as'null' \
    configure'--disable-utf8proc --prefix=$PWD --quiet' \
    make'PREFIX=$PWD --quiet install'\
    sbin \
  @tmux/tmux

zinit for \
    as'null' \
    configure'--prefix=$PWD' \
    make'PREFIX=$ZPFX install'\
    sbin \
  @eradman/entr

zi for \
    from'gh-r' \
    sbin'* -> jq' \
    nocompile \
  @jqlang/jq

zi for \
    from'gh-r' \
    sbin'**/nvim -> nvim' \
    ver'nightly' \
  neovim/neovim

zi for \
    as'completions' \
    atclone'buildx* completion zsh > _buildx' \
    from"gh-r" \
    sbin'!buildx-* -> buildx' \
  @docker/buildx 

zinit build for @aspiers/stow

zinit for \
    as'null' \
    make'PREFIX=$PWD --quiet install'\
    sbin \
  @cli/cli

zinit ice depth=1 id-as"tpm" lucid \
    atclone"mkdir -p ~/.tmux/plugins && ln -sfn $PWD ~/.tmux/plugins/tpm" \
    atpull'!git -C ~/.tmux/plugins/tpm pull --ff-only'
zinit load tmux-plugins/tpm




zinit ice wait lucid atinit"zicompinit; zicdreplay"
zinit light zdharma-continuum/fast-syntax-highlighting

zinit ice wait lucid atload"!_zsh_autosuggest_start"
zinit load zsh-users/zsh-autosuggestions

zinit for \
    as'null' \
    cmake'.' \
    make'install' \
    sbin \
  @posva/catimg

zinit wait lucid for \
  as"completion" \
    OMZP::docker/completions/_docker \
    OMZP::docker-compose/_docker-compose \
    OMZP::ssh \
    OMZP::invoke \
    OMZP::npm \
    OMZP::uv \
    OMZP::colored-man-pages \




zinit wait"1" lucid for \
    OMZP::git \
    zsh-users/zsh-completions \
    OMZP::fzf \
    zap-zsh/supercharge 


zinit wait"2" lucid for \
  olets/git-prompt-kit \
  olets/zsh-transient-prompt \
  "hlissner/zsh-autopair" \
  OMZ::lib/clipboard.zsh \


zsnippet_reload() {
  local file="$1"
  local id="${2:-${file:t}}"
  local stamp="${file:h}/.${id}-stamp"

  zinit ice id-as"$id" \
      atload"[[ $file -nt $stamp ]] && { source $file; touch $stamp; }"
  zinit snippet "$file"

}
TRANSIENT_PROMPT_TRANSIENT_PROMPT='%B%(?.%F{green}❯.%F{red}❯)%f%b $LAST_EXIT $LAST_DURATION '


autoload -Uz add-zsh-hook





# zinit load "zap-zsh/atmachine"
[[ -f ~/.config/zsh/aliases.zsh ]] && source ~/.config/zsh/aliases.zsh
[[ -f ~/.config/zsh/exports.zsh ]] && source ~/.config/zsh/exports.zsh



autoload -U compinit; compinit




# Shell integrations




# Uncomment the following line to use case-sensitive completion.
CASE_SENSITIVE="false"

# Uncomment the following line to use hyphen-insensitive completion.
# Case-sensitive completion must be off. _ and - will be interchangeable.
HYPHEN_INSENSITIVE="true"



# Uncomment the following line if pasting URLs and other text is messed up.
# DISABLE_MAGIC_FUNCTIONS="true"


# Uncomment the following line to disable auto-setting terminal title.
DISABLE_AUTO_TITLE="false"

# Uncomment the following line to enable command auto-correction.
ENABLE_CORRECTION="true"

# Uncomment the following line to display red dots whilst waiting for completion.
# You can also set it to another string to have that shown instead of the default red dots.
# e.g. COMPLETION_WAITING_DOTS="%F{yellow}waiting...%f"
# Caution: this setting can cause issues with multiline prompts in zsh < 5.7.1 (see #5765)
COMPLETION_WAITING_DOTS="true"

# Uncomment the following line if you want to disable marking untracked files
# under VCS as dirty. This makes repository status check for large repositories
# much, much faster.
# DISABLE_UNTRACKED_FILES_DIRTY="true"

# Uncomment the following line if you want to change the command execution time
# stamp shown in the history command output.
# You can set one of the optional three formats:
# "mm/dd/yyyy"|"dd.mm.yyyy"|"yyyy-mm-dd"
# or set a custom format using the strftime function format specifications,
# see 'man strftime' for details.
# HIST_STAMPS="mm/dd/yyyy"

# Would you like to use another custom folder than $ZSH/custom?
# ZSH_CUSTOM=/path/to/new-custom-folder

# Which plugins would you like to load?
# Standard plugins can be found in $ZSH/plugins/
# Custom plugins may be added to $ZSH_CUSTOM/plugins/
# Example format: plugins=(rails git textmate ruby lighthouse)
# Add wisely, as too many plugins slow down shell startup.
# plugins=(fzf-tab fzf tmux zsh-syntax-highlighting zsh-autosuggestions autoenv git npm tmux uv ssh sudo
# docker-compose docker
# copyfile

# )


# source $ZSH/oh-my-zsh.sh

# User configuration

# export MANPATH="/usr/local/man:$MANPATH"

# You may need to manually set your language environment
# export LANG=en_US.UTF-8

# Preferred editor for local and remote sessions
# if [[ -n $SSH_CONNECTION ]]; then
#   export EDITOR='vim'
# else
#   export EDITOR='mvim'
# fi

# Compilation flags
# export ARCHFLAGS="-arch x86_64"

# Set personal aliases, overriding those provided by oh-my-zsh libs,
# plugins, and themes. Aliases can be placed here, though oh-my-zsh
# users are encouraged to define aliases within the ZSH_CUSTOM folder.
# For a full list of active aliases, run `alias`.
#
# Example aliases
# alias zshconfig="mate ~/.zshrc"
# alias ohmyzsh="mate ~/.oh-my-zsh"

# Generated for envman. Do not edit.
# [ -s "$HOME/.config/envman/load.sh" ] && source "$HOME/.config/envman/load.sh"

# # To customize prompt, run `p10k configure` or edit ~/.p10k.zsh.
# [[ ! -f ~/.p10k.zsh ]] || source ~/.p10k.zsh


# Keybindings
# bindkey -e
# bindkey '^p' history-search-backward
# bindkey '^n' history-search-forward
# bindkey '^[w' kill-region
bindkey '^A' beginning-of-line
bindkey '^E' end-of-line
bindkey '^U' backward-kill-line
bindkey '^K' kill-line
bindkey '^W' backward-kill-word
bindkey '^H' backward-delete-char

# History
HISTSIZE=1000
HISTFILE=~/.zsh_history
SAVEHIST=$HISTSIZE
HISTDUP=erase
setopt appendhistory
setopt sharehistory
setopt hist_ignore_space
setopt hist_ignore_all_dups
setopt hist_save_no_dups
setopt hist_ignore_dups
setopt hist_find_no_dups

local extract="
in=\${\${\"\$(<{f})\"%\$'\0'*}#*\$'\0'}
local -A ctxt=(\"\${(@ps:\2:)CTXT}\")
"
# Completion styling
zstyle ':completion:*' matcher-list 'm:{a-z}={A-Za-z}'

zstyle ':completion:*:descriptions' format '[%d]'
zstyle ':completion:*' list-colors "${(s.:.)LS_COLORS}"


zstyle ':completion:*' menu no
zstyle ':fzf-tab:*' fzf-command ftb-tmux-popup


# zstyle ':fzf-tab:*' show-group full

# zstyle ':fzf-tab:*' single-group full
# zstyle ':fzf-tab:*' prefix ''
# bindkey '\t' expand-or-complete # fzf-tab reads it during initialization



LSD_COMMAND_PREVIEW='lsd --tree --depth 1 --group-directories-first --color=always --icon=always $realpath'
CAT_COMMAND_PREVIEW='bat --pager=never --color=always --line-range 0:30 $realpath'

compdef _gnu_generic fzf
compdef _gnu_generic lsd
compdef _gnu_generic pip
compdef _gnu_generic bat

export FZF_DEFAULT_OPTS="--preview='$HOME/bin/fzf.zsh {}' --height=100% --preview-window=right:40% --header='[CTRL-c or ESC to quit] | [CTRL-ALT-p: Toggle Preview]' --preview-label='File Preview [CTRL-ALT-P to hide]' --preview-label-pos='3:bottom' --bind='ctrl-alt-p:toggle-preview'"

FZF_PREVIEW_ZSTYLE="fzf-preview 'fzf.zsh $realpath'"


command -v ag > /dev/null && export FZF_DEFAULT_COMMAND='ag'
#for when running  ** anything
# _fzf_comprun() {
#   local command=$1
#   shift

#   case \
#    "$" in cd|z|zoxide|ls|lsd) fzf --preview 'lsd --tree --depth 1 --group-directories-first --color=always --icon=always {}'  "$@" ;; \
#    export|unset) fzf --preview "eval 'echo \$'{}"         "$@" ;; \
#    ssh)          fnzf --preview 'dig {}'                   "$@" ;; \
#     *)            fzf --preview 'bat -n --color=always {}' "$@" ;;  \
#   esac
# }



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


# eval "$(fzf --zsh)"
eval "$(zoxide init --cmd z zsh)"

if [ -z "$TMUX" ]; then
  tmux attach || tmux new-session
  exit
fi
#if command -v zellij >/dev/null 2>&1; then
 # eval "$(zellij setup --generate-auto-start zsh)"
#fi

#echo 'eval "$(zellij setup --generate-auto-start zsh)"' >> ~/.zshrc

            



#source local file if it exists


# if ! grep -q '@hyperupcall/autoenv/activate.sh' "${ZDOTDIR:-$HOME}/.zprofile.local" 2>/dev/null; then
#   printf '%s\n' "source $(npm root -g)/@hyperupcall/autoenv/activate.sh" >> "${ZDOTDIR:-$HOME}/.zprofile.local"
# f

if [ -f "$HOME/.config/kettle/kettle.zshrc" ]; then
  source "$HOME/.config/kettle/kettle.zshrc"
fi

zinit ice as"command" from"gh-r" \
          atclone"./starship init zsh > init.zsh; ./starship completions zsh > _starship" \
          atpull"%atclone" src"init.zsh"
zinit light starship/starship


if [ -f "$HOME/.local/share/zinit/bat" ]; then
  source "$HOME/.local/share/zinit/kettle/kettle.zshrc"
fisource /home/kettle/.config/kettle/kettle.zshrc
