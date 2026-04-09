# Clipboard image + Windows path helpers for zsh (WSL and Linux)

if [[ -n ${__KETTLE_WSL_CLIPBOARD_IMAGE_LOADED:-} ]]; then
  return 0
fi
typeset -g __KETTLE_WSL_CLIPBOARD_IMAGE_LOADED=1

_pasteimg_err() {
  print -u2 -- "pasteimg: $*"
}

_pasteimg_timestamp() {
  date +%Y%m%d-%H%M%S
}

_pasteimg_abs_path() {
  local p="$1"
  if [[ "$p" == /* ]]; then
    print -r -- "$p"
  else
    print -r -- "$PWD/$p"
  fi
}

_pasteimg_windows_save() {
  local target_linux="$1"
  local target_win ps_target

  if ! command -v powershell.exe >/dev/null 2>&1; then
    _pasteimg_err "powershell.exe not found (expected in WSL)"
    return 1
  fi

  if ! target_win=$(wslpath -w -- "$target_linux" 2>/dev/null); then
    _pasteimg_err "failed to convert path for Windows: $target_linux"
    return 1
  fi

  ps_target=${target_win//\'/\'\'}

  powershell.exe -NoProfile -NonInteractive -Sta -Command "\
    \$ErrorActionPreference = 'Stop'; \
    Add-Type -AssemblyName System.Windows.Forms; \
    Add-Type -AssemblyName System.Drawing; \
    if (-not [System.Windows.Forms.Clipboard]::ContainsImage()) { exit 10 } ; \
    \$img = [System.Windows.Forms.Clipboard]::GetImage(); \
    if (\$null -eq \$img) { exit 11 } ; \
    try { \
      \$img.Save('$ps_target', [System.Drawing.Imaging.ImageFormat]::Png) \
    } finally { \
      \$img.Dispose() \
    } ; \
    exit 0" >/dev/null 2>&1

  case $? in
    0) return 0 ;;
    10|11)
      _pasteimg_err "Windows clipboard does not contain an image"
      return 3
      ;;
    *)
      _pasteimg_err "failed to read image from Windows clipboard"
      return 4
      ;;
  esac
}

_pasteimg_linux_save() {
  local target="$1"

  if command -v wl-paste >/dev/null 2>&1; then
    if wl-paste --no-newline --type image/png >"$target" 2>/dev/null; then
      [[ -s "$target" ]] && return 0
    fi
  fi

  if command -v xclip >/dev/null 2>&1; then
    if xclip -selection clipboard -t image/png -o >"$target" 2>/dev/null; then
      [[ -s "$target" ]] && return 0
    fi
  fi

  rm -f -- "$target"
  _pasteimg_err "clipboard image not available (need wl-paste or xclip, and an image in clipboard)"
  return 3
}

_pasteimg_save() {
  local target="$(_pasteimg_abs_path "$1")"
  local parent="${target:h}"

  mkdir -p -- "$parent" 2>/dev/null || {
    _pasteimg_err "cannot create directory: $parent"
    return 1
  }

  if [[ -n ${WSL_DISTRO_NAME:-} || -n ${WSL_INTEROP:-} ]]; then
    _pasteimg_windows_save "$target" || return $?
  else
    _pasteimg_linux_save "$target" || return $?
  fi

  print -r -- "$target"
}

_pasteimg_tmp_name() {
  print -r -- "clip-$(_pasteimg_timestamp)-$RANDOM.png"
}

_pasteimg_here_name() {
  print -r -- "clipboard-$(_pasteimg_timestamp).png"
}

_pasteimg_resolve_target() {
  local default_dir="$1"
  local default_name="$2"
  local input="$3"
  local target

  if [[ -z "$input" ]]; then
    target="$default_dir/$default_name"
  elif [[ -d "$input" || "$input" == */ ]]; then
    target="${input%/}/$default_name"
  else
    target="$input"
  fi

  print -r -- "$target"
}

pasteimg() {
  local target
  target="$(_pasteimg_resolve_target "/tmp" "$(_pasteimg_tmp_name)" "$1")"
  _pasteimg_save "$target"
}

pasteimg_here() {
  local name="${1:-$(_pasteimg_here_name)}"
  _pasteimg_save "$PWD/$name"
}

pasteimg_name() {
  local name="$1"
  if [[ -z "$name" ]]; then
    _pasteimg_err "usage: pasteimg-name <name-or-filename>"
    return 2
  fi
  if [[ "$name" != *.* ]]; then
    name+=".png"
  fi
  pasteimg_here "$name"
}

winpath2wsl() {
  local raw drive rest

  if (( $# == 0 )); then
    print -u2 -- "winpath2wsl: usage: winpath2wsl <windows-path>"
    return 2
  fi

  raw="$*"
  raw="${raw#\"}"
  raw="${raw%\"}"
  raw="${raw#\'}"
  raw="${raw%\'}"

  if command -v wslpath >/dev/null 2>&1; then
    local converted
    if converted=$(wslpath -u -- "$raw" 2>/dev/null); then
      print -r -- "$converted"
      return 0
    fi
  fi

  if [[ "$raw" == [A-Za-z]:[\\/]* ]]; then
    drive="${raw[1,1]}"
    rest="${raw[3,-1]}"
    rest="${rest##[\\/]}"
    rest="${rest//\\//}"
    if [[ -n "$rest" ]]; then
      print -r -- "/mnt/${(L)drive}/$rest"
    else
      print -r -- "/mnt/${(L)drive}"
    fi
    return 0
  fi

  print -u2 -- "winpath2wsl: invalid Windows path: $raw"
  return 1
}

alias pasteimg-here='pasteimg_here'
alias pasteimg-name='pasteimg_name'

_pasteimg_or_convert_widget() {
  emulate -L zsh
  local buf="$BUFFER"
  local converted img

  if [[ "$buf" == [A-Za-z]:[\\/]* || "$buf" == \"[A-Za-z]:[\\/]*\" || "$buf" == \'[A-Za-z]:[\\/]*\' ]]; then
    converted=$(winpath2wsl "$buf" 2>/dev/null) || {
      zle -M "winpath2wsl failed"
      return 1
    }
    BUFFER="$converted"
    CURSOR=${#BUFFER}
    return 0
  fi

  img=$(pasteimg 2>/dev/null) || {
    zle -M "clipboard image not found"
    return 1
  }
  LBUFFER+="$img"
}

if [[ -o interactive ]] && (( $+functions[zle] )); then
  zle -N pasteimg-or-convert _pasteimg_or_convert_widget
fi
