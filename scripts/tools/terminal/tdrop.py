from scripts.misc.helpers import run_sudo
from . import print_success, print_error, console, print
from . import is_darwin, is_windows, is_linux, is_ubuntu_22, is_ubuntu_24, is_ubuntu
from . import cmd_exists, download_file
from . import config, Config
from pathlib import Path


from invoke import task
tdrop_dir = Path.home() / ".tdrop"

def clone(c):
    if tdrop_dir.exists():
        print_success("tdrop is already installed.")
        c.run(f"cd {tdrop_dir} && git pull", pty=True)
        return
    if not cmd_exists("git"):
        install()
        print_error("git is not installed. Please install git first.")
        return
    c.run(f"git clone https://github.com/noctuid/tdrop.git {tdrop_dir.resolve()}", pty=True)
    if not tdrop_dir.exists():
        print_error("tdrop directory does not exist. Cloning failed.")
        return
    
@task
def install(c):
    if cmd_exists("tdrop"):
        print_success("tdrop installed successfully.")
        return

    clone(c)
    run_sudo(c, f"bash -c 'cd {tdrop_dir.resolve()} && make install'")
    if cmd_exists("tdrop"):
        print_success("tdrop installed successfully.")
    else:
        print_error("tdrop installation failed.")