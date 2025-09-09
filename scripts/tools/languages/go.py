import os
import requests
from invoke import task

from scripts.misc.helpers import run_sudo
from scripts.misc import cmd_exists, print, print_error, print_success


@task
def install(c):
    """Installs Go."""
    if cmd_exists("go"):
        print_success("Go is already installed.")
        return
    go_url = requests.get("https://go.dev/VERSION?m=text", timeout=60).text.strip()
    go_version = go_url.split("\n")[0]
    go_file = f"{go_version}.linux-amd64.tar.gz"
    c.run(f"curl -LO https://go.dev/dl/{go_file}")
    run_sudo(c, f"rm -rf /usr/local/go")
    run_sudo(c, f"tar -C /usr/local -xzf {go_file}")
    run_sudo(c, f"rm {go_file}")
    run_sudo(c, f"chown -R {os.getlogin()} /usr/local/go")
    run_sudo(c, f"chmod +x /usr/local/go/bin/go")

    if cmd_exists("go"):
        print_success("Go installed successfully.")
    else:
        print_error("Go installation failed.")

