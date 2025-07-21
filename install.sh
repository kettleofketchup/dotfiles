sudo apt install ruby-full curl git build-essential stow zsh -y

curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

sudo dpkg -i bin/*.deb 
cargo install --locked zellij
curl -s https://ohmyposh.dev/install.sh | bash -s
curl -sSfL https://raw.githubusercontent.com/ajeetdsouza/zoxide/main/install.sh | sh

stow . 

git clone https://github.com/Aloxaf/fzf-tab ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/fzf-tab
git clone https://github.com/zsh-users/zsh-syntax-highlighting.git ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-syntax-highlighting
git clone https://github.com/zsh-users/zsh-autosuggestions ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-autosuggestions
git clone --depth=1 https://github.com/romkatv/powerlevel10k.git "${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}/themes/powerlevel10k"
# Install autoenv
wget --show-progress -o /dev/null -O- 'https://raw.githubusercontent.com/hyperupcall/autoenv/main/scripts/install.sh' | sh





cargo install lsd
