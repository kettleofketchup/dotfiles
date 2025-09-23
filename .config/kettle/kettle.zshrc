source $HOME/.config/kettle/completions/kettle.zsh
export PATH=$PATH:$HOME/go/bin

if command -v golangci-lint >/dev/null; then
    eval "$(golangci-lint completion zsh)"
fi

export PATH="$HOME/go/bin:$PATH"



if command -v npm >/dev/null; then
  if [ -n "$NPM_ROOT" ] && [ -f "$NPM_ROOT/@hyperupcall/autoenv/activate.sh" ]; then
    source "$NPM_ROOT/@hyperupcall/autoenv/activate.sh"
  fi
fi 

if [ -f $HOME/.autoenv/activate.sh ]; then
  source $HOME/.autoenv/activate.sh
fi