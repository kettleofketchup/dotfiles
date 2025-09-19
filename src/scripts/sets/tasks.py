from invoke import Collection, task
from scripts.tools.terminal import (  install_autoenv,
        install_bat,
        install_fzf,
        install_kitty,
        install_lsd,
        install_ohmyposh,
        install_plugins,
        install_zoxide,
        install_all as install_terminal_all
)
from scripts.tools.languages import (  install_go,install_all, install_nvm, install_python, install_rust, install_all as install_languages_all
)
from scripts.tools.general import (  install_fonts, install_requirements, install_all as install_general_all, install_stow
)
from scripts.misc import print, print_error, print_success


ns = Collection("sets")

@task
def general(c):
    """Sets up a general server."""
    install_general_all(c)
    install_languages_all(c)
    install_terminal_all(c)

    print_success("General setup complete!", c)





