function _fd_select() {
  local -a opts
  case "$1" in
    'f')
      opts=(--preview="bat --pager=never --color=always --line-range :30 {}" --preview-window=right:70%)
      ;;
    'd')
      opts=(--preview='lsd --group-directories-first {}' --preview-window=right:50%)
      ;;
  esac
  _fd_filter $1 "$2" | fzf \
    --ansi $opts \
    --select-1 \
    --exit-0 \
    --layout=reverse --height=75% \
    --tiebreak=begin --bind=tab:down,btab:up,change:top \
    --cycle --query="$(basename "$2")"
}
