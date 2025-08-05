#!/bin/bash -x
base_repo_url=https://github.com

REPO_OH_MY_ZSH="${base_repo_url}/ohmyzsh/ohmyzsh.git"
REPO_FZF="${base_repo_url}/Aloxaf/fzf-tab.git"
REPO_ZSH_AUTOCOMPLETE="${base_repo_url}/marlonrichert/zsh-autocomplete.git"
REPO_ZSH_SUGGETIONS="${base_repo_url}/zsh-users/zsh-autosuggestions.git"
REPO_ZSH_SYNTAX_HIGHLIGHTING="${base_repo_url}/zsh-users/zsh-syntax-highlighting.git"
REPO_TPM="${base_repo_url}/tmux-plugins/tpm.git"
REPO_TMUX_SENSIBLE="${base_repo_url}/tmux-plugins/tmux-sensible.git"
REPO_TMUX_POWERLINE="${base_repo_url}/erikw/tmux-powerline.git"

OHMYZSH_CUSTOM=${ZSH_CUSTOM:-~/.oh-my-zsh/custom}

rm -rf .oh-my-zsh
rm -rf .tmux/plugins/tmux-sensible
rm -rf .tmux/plugins/tmux-powerline
rm -rf .tmux/plugins/tmux-power
rm -rf .tmux/plugins/tpm

echo "ASSUMING WORKING DIRECTORY OF dotfiles"
git clone $REPO_OH_MY_ZSH .oh-my-zsh
cp -r powerlevel10k .oh-my-zsh/custom/themes/powerlevel10k

cp bin/gitstatusd-linux-x86_64 .oh-my-zsh/custom/themes/powerlevel10k/gitstatus/usrbin/gitstatusd-linux-x86_64
cp bin/gitstatusd-linux-x86_64 powerlevel10k/gitstatus/usrbin/gitstatusd-linux-x86_64 
git clone $REPO_FZF "${OHMYZSH_CUSTOM}/plugins/fzf-tab"
git clone $REPO_ZSH_SUGGETIONS "${OHMYZSH_CUSTOM}/plugins/zsh-autosuggestions"
git clone $REPO_ZSH_AUTOCOMPLETE "${OHMYZSH_CUSTOM}/plugins/zsh-autocomplete"
git clone $REPO_ZSH_SYNTAX_HIGHLIGHTING "${OHMYZSH_CUSTOM}/plugins/zsh-syntax-highlighting"
git clone $REPO_TMUX_POWERLINE .tmux/plugins/tmux-powerline
git clone $REPO_TPM .tmux/plugins/tpm
git clone $REPO_TMUX_SENSIBLE .tmux/plugins/tmux-sensible

