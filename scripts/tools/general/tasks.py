from invoke import Collection, task

from . import install_fonts, install_requirements, install_stow

ns = Collection("general")


@task
def install_all(c):
    """Installs all general tools."""
    install_requirements(c)
    install_fonts(c)
    install_stow(c)