from invoke import task


@task
def install(c):
    """Installs Kitty."""
    c.run(
        "ln -sf ~/.local/kitty.app/bin/kitty ~/.local/kitty.app/bin/kitten ~/.local/bin/",
        pty=True,
    )
    c.run(
        "cp ~/.local/kitty.app/share/applications/kitty.desktop ~/.local/share/applications/",
        pty=True,
    )
    c.run(
        "cp ~/.local/kitty.app/share/applications/kitty-open.desktop ~/.local/share/applications/",
        pty=True,
    )
    c.run(
        'sed -i "s|Icon=kitty|Icon=/home/$USER/.local/kitty.app/share/icons/hicolor/256x256/apps/kitty.png|g" ~/.local/share/applications/kitty*.desktop',
        pty=True,
    )
    c.run(
        'sed -i "s|Exec=kitty|Exec=/home/$USER/.local/kitty.app/bin/kitty|g" ~/.local/share/applications/kitty*.desktop',
        pty=True,
    )
