from . import print_success, print_error, console, print
from . import is_darwin, is_windows, is_linux, is_ubuntu_22, is_ubuntu_24, is_ubuntu
from . import cmd_exists, download_file
from . import config, Config
from pathlib import Path


from invoke import task
fzf_dir = Path.home() / ".fzf"

def clone(c):
  
    if not cmd_exists("git"):
        install()
        print_error("git is not installed. Please install git first.")
        return
    c.run(f"git clone --depth 1 https://github.com/junegunn/fzf.git {fzf_dir.resolve()}", pty=True)
    if not fzf_dir.exists():
        print_error("fzf directory does not exist. Cloning failed.")
        return
    
@task
def install(c):
    clone(c)
    with c.cd(fzf_dir):
        c.run("./install --bin", pty=True)
