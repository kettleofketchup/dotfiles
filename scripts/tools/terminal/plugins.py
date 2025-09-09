from invoke import task


@task
def install(c):
    """Installs zsh and tmux plugins."""
    base_repo_url = "https://github.com"
    repos = {
        "ohmyzsh/ohmyzsh": ".oh-my-zsh",
        "Aloxaf/fzf-tab": ".oh-my-zsh/custom/plugins/fzf-tab",
        "marlonrichert/zsh-autocomplete": ".oh-my-zsh/custom/plugins/zsh-autocomplete",
        "zsh-users/zsh-autosuggestions": ".oh-my-zsh/custom/plugins/zsh-autosuggestions",
        "zsh-users/zsh-syntax-highlighting": ".oh-my-zsh/custom/plugins/zsh-syntax-highlighting",
        "tmux-plugins/tpm": ".tmux/plugins/tpm",
        "tmux-plugins/tmux-sensible": ".tmux/plugins/tmux-sensible",
        "erikw/tmux-powerline": ".tmux/plugins/tmux-powerline",
    }

    for repo, dest in repos.items():
        c.run(f"rm -rf {dest}", pty=True)
        c.run(f"git clone {base_repo_url}/{repo}.git {dest}", pty=True)

    c.run("cp -r powerlevel10k .oh-my-zsh/custom/themes/powerlevel10k", pty=True)
    c.run(
        "cp bin/gitstatusd-linux-x86_64 .oh-my-zsh/custom/themes/powerlevel10k/gitstatus/usrbin/gitstatusd-linux-x86_64",
        pty=True,
    )
    c.run(
        "cp bin/gitstatusd-linux-x86_64 powerlevel10k/gitstatus/usrbin/gitstatusd-linux-x86_64",
        pty=True,
    )
