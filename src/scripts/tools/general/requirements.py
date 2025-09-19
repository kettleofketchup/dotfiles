from invoke import task
from ...misc import is_darwin, is_windows, is_linux, is_ubuntu_22, is_ubuntu_24, print, print_success, print_error, is_ubuntu, config, console, run_sudo



def install_ubuntu_22(c):
    packages = ("stow zsh p7zip-full catimg chafa libevent-dev "
                "ncurses-dev libncurses-dev build-essential bison "
                "pkg-config tmux bat xdotool x11-utils ")
    run_sudo(c, "apt update -y")
    run_sudo(c, f"apt install {packages} -y")


def install_ubuntu_24(c):
    packages = ("stow zsh p7zip-full catimg chafa libevent-dev "
                "ncurses-dev libncurses-dev build-essential bison "
                "pkg-config tmux bat xdotool x11-utils ")
    run_sudo(c, "apt update -y")
    run_sudo(c, f"apt install {packages} -y")

def install_ubuntu(c):
    if not is_linux():
        return
    if not is_ubuntu():
        return
    if is_ubuntu_22():
        install_ubuntu_22(c)
    elif is_ubuntu_24():
        install_ubuntu_24(c)
    else:
        print_error("Unsupported Ubuntu version. Only 22.04 and 24.04 are supported.")
        return
    
def install_darwin(c):
    from .mac.brew import install as install_brew
    install_brew(c)
    c.run("brew install curl git build-essential stow zsh fzf imgcat")

@task
def install(c):
    if is_ubuntu:
        install_ubuntu(c)
    elif is_darwin:
        install_darwin(c)
    else:
        print_error("Unsupported OS. Only Ubuntu and macOS are supported.")
    return