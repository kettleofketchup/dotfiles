from invoke import task
from . import is_darwin, print_success, print_error, cmd_exists, is_linux, is_ubuntu
def install(c):
    if cmd_exists("autoenv"):
        print_success("autoenv is already installed.")
        return
    if cmd_exists("npm"):
        c.run("npm install -g autoenv", pty=True)

    elif is_darwin():
        c.run("brew install autoenv", pty=True)
    elif is_linux():
        c.run("sudo apt install autoenv", pty=True)
    else:  
        print_error("Unsupported OS. Only Ubuntu and macOS are supported.")
        return