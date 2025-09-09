from invoke import task
from scripts.misc.helpers import run_sudo


@task
def install(c):
    """Installs Python."""
    run_sudo(c, "apt update -y")
    run_sudo(c, "apt install python3 python3-pip python3-venv -y")
