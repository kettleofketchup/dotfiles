from invoke import task
from ...misc import cmd_exists, print_success,print_error, is_windows

@task
def install(c):
    """Installs Rust."""
    if cmd_exists("rustc"):
        print_success("Rust is already installed.")
        return

    if is_windows():
        print_error("Please install Rust manually from https://www.rust-lang.org/tools/install")
        return
    

    c.run("curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y")

    print_success("Rust installed")
