import os
import requests
from invoke import task
from scripts.misc import cmd_exists, print_success, print_error, is_windows 
@task
def install(c):
    """Installs nvm."""
    if cmd_exists("nvm"):
        print_success("nvm is already installed.")
        return
    
    nvm_version = requests.get(
        "https://api.github.com/repos/nvm-sh/nvm/releases/latest", timeout=60
    ).json()["tag_name"]
    c.run(
        f'curl -o- "https://raw.githubusercontent.com/nvm-sh/nvm/{nvm_version}/install.sh" | bash'
    )
    c.run(f"source $HOME/.nvm/nvm.sh && nvm install --lts && nvm use --lts")
