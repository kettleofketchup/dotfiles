from scripts.misc.platforms import is_windows
from . import cmd_exists, is_darwin, is_linux, is_ubuntu, print_error, print_success

from invoke import task

@task
def install(c):
    if cmd_exists("oh-my-posh"):
        print_success("Oh My Posh is already installed.")
        return

    if is_windows():
        print_error("Oh My Posh installation on Windows is not supported yet.")
        return        
    c.run('curl -s https://ohmyposh.dev/install.sh | bash -s -- -d ~/bin', pty=True)
    if cmd_exists("oh-my-posh"):
        print_success("Oh My Posh installed.")