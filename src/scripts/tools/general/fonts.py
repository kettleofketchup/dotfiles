from invoke import task


@task
def install(c):
    """Installs fonts."""
    c.run("mkdir -p ~/.local/share/fonts/", pty=True)
    c.run("cp fonts/*.ttf ~/.local/share/fonts/", pty=True)
    c.run("fc-cache -f -v", pty=True)
