# Development recipes

# Bootstrap the development environment
dev:
    echo "Setting up development environment..."
    # TODO: Add project-specific setup steps
    # Examples:
    #   npm install
    #   pip install -r requirements.txt
    #   cargo build
    echo "Done!"

# Build the offline bundle: zinit snapshot + dotfiles.tar
pack-offline:
    bin/zinit-pack.sh
    tar --exclude='dotfiles/dotfiles.tar' \
        --exclude='dotfiles/.worktrees' \
        --exclude='dotfiles/.cache' \
        -cf "$HOME/dotfiles/dotfiles.tar" \
        -C "$HOME" dotfiles
    echo "Built: $HOME/dotfiles/dotfiles.tar ($(du -h "$HOME/dotfiles/dotfiles.tar" | cut -f1))"
