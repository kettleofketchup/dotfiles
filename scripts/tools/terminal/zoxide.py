from scripts.misc import cmd_exists, is_darwin, is_linux, is_ubuntu, print_error, print_success,is_windows

from invoke import task

@task
def install(c):
    if cmd_exists("zoxide"):
        print_success("Zoxide is already installed.")
        return
    if is_windows():
        print_error("Zoxide installation on Windows is not supported yet.")
        return
    
    c.run('curl -sSfL https://raw.githubusercontent.com/ajeetdsouza/zoxide/main/install.sh | sh', pty=True)
    if cmd_exists("zoxide"):
        print_success("Zoxide installed.")
