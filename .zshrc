

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

zi for \
    from'gh-r' \
    sbin'**/cmake -> cmake' \
    sbin'**/ctest -> ctest' \
    sbin'**/cpack -> cpack' \
  @Kitware/CMake

zi for \
    from'gh-r' \
    sbin'bin/lua-language-server -> lua-language-server' \
  @LuaLS/lua-language-server


zi for \
    from'gh-r' \
    sbin'lua* -> checkmake' atclone" ./checkmake* completion zsh > _checkmake" atpull"%atclone" as"completion" \
  @checkmake/checkmake
# zinit for \
#     as'null' \
#     configure'--disable-utf8proc --prefix=$PWD --quiet' \
#     make'linux install'\
#     sbin'lua -> lua' \
#   @lua/lua



zinit as"null" wait lucid from"gh-r" for \
    sbin"lsd"     lsd-rs/lsd \
    sbin"fd"      @sharkdp/fd \
    sbin"bat" atclone"./bat*/bat --completion zsh > _bat" atpull"%atclone" as"completion"     @sharkdp/bat \
    sbin"fzf"     junegunn/fzf \
    sbin"rg" atclone"./rip*/rg --generate=complete-zsh > _rg" atpull"%atclone" as"completion"     @BurntSushi/ripgrep \
    sbin"**/lazygit" @jesseduffield/lazygit \
    # sbin"kettle"  kettleofkethchup/kettle


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
    sbin'just' \
  @casey/just


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


zi for \
    from'gh-r' \
    sbin"**/gh" atclone"./**/gh completion -s zsh > _gh" atpull"%atclone" as"completion"\
  cli/cli


zinit ice depth=1 id-as"tpm" lucid \
    atclone"mkdir -p ~/.tmux/plugins && ln -sfn \$PWD ~/.tmux/plugins/tpm" \
    atpull'%atclone'
zinit load tmux-plugins/tpm



### --- Yazi File Manager via zinit ---

# Yazi file manager
zinit ice from"gh-r" as"program" \
    pick"yazi" pick"ya" \
    sbin'ya -> ya' \
    sbin'yazi -> yazi' \

zinit light sxyazi/yazi
# Clone the plugins monorepo
zinit ice from "gh-r" \
    atclone"mkdir -p ~/.config/yazi/plugins && ln -sfn {dir} ~/.config/yazi/plugins/plugins-repo" \
    atpull"%atclone"
zinit light yazi-rs/plugins

# Starship plugin for Yazi
zinit ice \
    atclone"mkdir -p ~/.config/yazi/plugins && ln -sfn \$PWD ~/.config/yazi/plugins/starship.yazi" \
    atpull"%atclone" \
    as"null"
zinit light Rolv-Apneseth/starship.yazi


# zinit ice wait"0" atclone"mkdir -p ~/.config/yazi/plugins && ln -sf {dir} ~/.config/yazi/plugins/starship" \
#     atpull"%atclone"
# zinit light yazi-rs/plugins:starship guit

# # Image preview plugin
# zinit ice wait"0" atclone"mkdir -p ~/.config/yazi/plugins && ln -sf {dir} ~/.config/yazi/plugins/image" \
#     atpull"%atclone"
# zinit light yazi-rs/plugins:image

# End Yazi setup



zinit ice wait lucid atinit"zicompinit; zicdreplay"
zinit light zdharma-continuum/fast-syntax-highlighting

zinit ice wait lucid atload"!_zsh_autosuggest_start"

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
    OMZP::uv \
    OMZP::colored-man-pages




zinit wait"1" lucid for \
    OMZP::git \
    zsh-users/zsh-completions \
    OMZP::fzf \


zinit wait"2" lucid for \
  olets/git-prompt-kit \
  olets/zsh-transient-prompt \
  "hlissner/zsh-autopair" \
  zsh-users/zsh-autosuggestions \
  OMZ::lib/clipboard.zsh \
  OMZP::npm \
  zap-zsh/supercharge



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

[[ -f ~/.config/zsh/plugins.zsh ]] && zinit snippet ~/.config/zsh/plugins.zsh
[[ -f ~/.config/zsh/history.zsh ]] && zinit snippet ~/.config/zsh/history.zsh

[[ -f ~/.config/zsh/keys.zsh ]] && zinit snippet ~/.config/zsh/keys.zsh
[[ -f ~/.config/zsh/settings.zsh ]] && zinit snippet ~/.config/zsh/settings.zsh


[[ -f ~/.config/zsh/styles.zsh ]] && zinit snippet ~/.config/zsh/styles.zsh
[[ -f ~/.config/zsh/exports.zsh ]] && zinit snippet ~/.config/zsh/exports.zsh
[[ -f ~/.config/zsh/aliases.zsh ]] && zinit snippet ~/.config/zsh/aliases.zsh

# zinit load "zap-zsh/atmachine"
#[[ -f ~/.config/zsh/aliases.zsh ]] && source ~/.config/zsh/aliases.zsh
#[[ -f ~/.config/zsh/exports.zsh ]] && source ~/.config/zsh/exports.zsh



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



# eval "$(fzf --zsh)"
eval "$(zoxide init --cmd z zsh)"
# Bracketed paste mode, fixes multiline pastes
autoload -Uz bracketed-paste-magic
zle -N bracketed-paste bracketed-paste-magic



# bun
export BUN_INSTALL="$HOME/.bun"
export PATH="$BUN_INSTALL/bin:$PATH"
# bun completions
[ -s "/home/kettle/.bun/_bun" ] && source "/home/kettle/.bun/_bun"

# just completions (patched for module support)
if [[ -f ~/.config/just/completions.zsh ]]; then
    zinit snippet ~/.config/just/completions.zsh

fi

if [ -z "$TMUX" ]; then
  tmux attach || tmux new-session
  exit
fi

export NVM_DIR="$HOME/.config/nvm"

[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion

if [ -f "$HOME/.config/kettle/kettle.zshrc" ]; then
  source "$HOME/.config/kettle/kettle.zshrc"
fi

zinit ice as"command" from"gh-r" \
          atclone"./starship init zsh > init.zsh; ./starship completions zsh > _starship" \
          atpull"%atclone" src"init.zsh"
zinit load starship/starship


# opencode
export PATH=$HOME/.opencode/bin:$PATH
