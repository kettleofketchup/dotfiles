import os
import requests
from invoke import task

from scripts.misc.helpers import run_sudo


@task
def install(c):
    """Installs Go."""
    go_url = requests.get("https://go.dev/VERSION?m=text", timeout=60).text.strip()
    go_version = go_url.split("\n")[0]
    go_file = f"{go_version}.linux-amd64.tar.gz"
    c.run(f"curl -LO https://go.dev/dl/{go_file}")
    run_sudo(c, f"rm -rf /usr/local/go")
    run_sudo(c, f"tar -C /usr/local -xzf {go_file}")
    c.run(f"rm {go_file}")
