# Enable Powerlevel10k instant prompt. Should stay close to the top of ~/.zshrc.
# Initialization code that may require console input (password prompts, [y/n]
# confirmations, etc.) must go above this block; everything else may go below.
if [[ -r "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh" ]]; then
  source "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh"
fi

#ZSH_THEME="powerlevel10k/powerlevel10k"
# If you come from bash you might have to change  your $PATH.
export PATH=$HOME/bin:/usr/local/bin:$PATH
local sanitized_in='${~ctxt[hpre]}"${${in//\\ / }/#\~/$HOME}"'

# Path to your oh-my-zsh installation.
export ZSH="$HOME/.oh-my-zsh"

# Set name of the theme to load --- if set to "random", it will
# load a random theme each time oh-my-zsh is loaded, in which case,
# to know which specific one was loaded, run: echo $RANDOM_THEME
# See https://github.com/ohmyzsh/ohmyzsh/wiki/Themes
# ZSH_THEME="robbyrussell"

# Set list of themes to pick from when loading at random
# Setting this variable when ZSH_THEME=random will cause zsh to load
# a theme from this variable instead of looking in $ZSH/themes/
# If set to an empty array, this variable will have no effect.
# ZSH_THEME_RANDOM_CANDIDATES=( "robbyrussell" "agnoster" )

# Uncomment the following line to use case-sensitive completion.
# CASE_SENSITIVE="true"

# Uncomment the following line to use hyphen-insensitive completion.
# Case-sensitive completion must be off. _ and - will be interchangeable.
# HYPHEN_INSENSITIVE="true"

# Uncomment one of the following lines to change the auto-update behavior
# zstyle ':omz:update' mode disabled  # disable automatic updates
# zstyle ':omz:update' mode auto      # update automatically without asking
# zstyle ':omz:update' mode reminder  # just remind me to update when it's time

# Uncomment the following line to change how often to auto-update (in days).
# zstyle ':omz:update' frequency 13

# Uncomment the following line if pasting URLs and other text is messed up.
# DISABLE_MAGIC_FUNCTIONS="true"

# Uncomment the following line to disable colors in ls.
# DISABLE_LS_COLORS="true"

# Uncomment the following line to disable auto-setting terminal title.
# DISABLE_AUTO_TITLE="true"

# Uncomment the following line to enable command auto-correction.
# ENABLE_CORRECTION="true"

# Uncomment the following line to display red dots whilst waiting for completion.
# You can also set it to another string to have that shown instead of the default red dots.
# e.g. COMPLETION_WAITING_DOTS="%F{yellow}waiting...%f"
# Caution: this setting can cause issues with multiline prompts in zsh < 5.7.1 (see #5765)
# COMPLETION_WAITING_DOTS="true"

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
autoload -Uz compinit && compinit
plugins=(fzf-tab zsh-syntax-highlighting zsh-autosuggestions git invoke npm tmux uv autoenv)


source $ZSH/oh-my-zsh.sh

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
[ -s "$HOME/.config/envman/load.sh" ] && source "$HOME/.config/envman/load.sh"

# To customize prompt, run `p10k configure` or edit ~/.p10k.zsh.
[[ ! -f ~/.p10k.zsh ]] || source ~/.p10k.zsh


# Keybindings
bindkey -e
bindkey '^p' history-search-backward
bindkey '^n' history-search-forward
bindkey '^[w' kill-region


# History
HISTSIZE=5000
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
# zstyle ':completion:*' list-colors "${(s.:.)LS_COLORS}"
zstyle ':completion:*' menu no
# zstyle ':fzf-tab:*' show-group full

# zstyle ':fzf-tab:*' single-group full
# zstyle ':fzf-tab:*' prefix ''
# bindkey '\t' expand-or-complete # fzf-tab reads it during initialization
LSD_COMMAND_PREVIEW='lsd --tree --depth 1 --group-directories-first --color=always --icon=always $realpath'
CAT_COMMAND_PREVIEW='bat --pager=never --color=always --line-range 0:30 $realpath'

fzf_preview() {
  if [ -d $1 ]; then echo $LSD_COMMAND_PREVIEW; return; fi
  case $1 in
    *.jpg|*.jpeg|*.png|*.gif) echo 'svix -a' ;;

    
  esac
}

#for when running  ** anything
_fzf_comprun() {
  local command=$1
  shift

  case \
   "$" in cd|z|zoxide|ls|lsd) fzf --preview 'lsd --tree --depth 1 --group-directories-first --color=always --icon=always {}'  "$@" ;; \
   export|unset) fzf --preview "eval 'echo \$'{}"         "$@" ;; \
   ssh)          fzf --preview 'dig {}'                   "$@" ;; \
    *)            fzf --preview 'bat -n --color=always {}' "$@" ;;  \
  esac
}

compdef _gnu_generic fzf
compdef _gnu_generic lsd
compdef _gnu_generic pip
compdef _gnu_generic bat
# compdef _gnu_generic ssh


zstyle ':fzf-tab:complete:cd:*' fzf-preview 'fzf.zsh $realpath'
zstyle ':fzf-tab:complete:__zoxside_z:*'fzf-preview 'fzf.zsh $realpath'
zstyle ':fzf-tab:complete:z:*' fzf-preview 'fzf.zsh $realpath'
zstyle ':fzf-tab:complete:ls:*' fzf-preview 'fzf.zsh $realpath'
zstyle ':fzf-tab:complete:lsd:*' fzf-preview 'fzf.zsh $realpath'

zstyle ':fzf-tab:complete:cat:*' fzf-preview 'fzf.zsh $realpath'

zstyle ':fzf-tab:complete:bat:*' fzf-preview 'fzf.zsh $realpath'
zstyle ':fzf-tab:complete:kill:argument-rest' extra-opts --preview=$extract'ps --pid=$in[(w)1] -o cmd --no-headers -w -w' --preview-window=down:3:wrap


# Aliases
alias ls='lsd --group-directories-first --color=always --icon=always'
alias vim='nvim'
alias c='clear'
alias cat='bat --style="grid,header"'
alias z='zoxide'
# Shell integrations
# eval "$(fzf --zsh)"
eval "$(zoxide init zsh)"

export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion


if [ -f "$HOME/.cargo/env" ]; then
  source "$HOME/.cargo/env"
fi

#if command -v zellij >/dev/null 2>&1; then
 # eval "$(zellij setup --generate-auto-start zsh)"
#fi

#echo 'eval "$(zellij setup --generate-auto-start zsh)"' >> ~/.zshrc


if command -v oh-my-posh  >/dev/null 2>&1; then
  eval "$(oh-my-posh init zsh --config ~/.omp.json)"
fi                                                                                       
                      

#eval "$(zellij setup --generate-auto-start zsh)"
source '/home/kettle/.nvm/versions/node/v22.14.0/lib/node_modules/@hyperupcall/autoenv/activate.sh'
