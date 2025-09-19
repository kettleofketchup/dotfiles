from invoke import task

from scripts.misc import is_darwin, print_success, print_error,cmd_exists

def install(c):
    if not is_darwin():
        return
    
    if cmd_exists("brew"):
        return
 
    c.run(
        '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"',
        pty=True,
    )
    print_success("Installed Homebrew...")
