from ...misc import is_ubuntu, is_darwin, cmd_exists, print_error, print_success, is_windows
from invoke import task
from ..languages.rust import install as install_rust
@task
def install(c):
    if is_windows():
        print_error("Please install lsd manually from https://github.com/lsd-rs/lsd")
        return
    if cmd_exists("lsd"):
        print_success("lsd is already installed.")
        return
    if not cmd_exists("cargo"):
        install_rust(c)

    c.run("cargo install lsd", pty=True)