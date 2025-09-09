from invoke import task
from scripts.misc.helpers import cmd_exists
from scripts.tools.general import install_requirements
from paths import BASE_DIR
def install(c):
    """Installs stow."""
    if not cmd_exists("stow"):
        install_requirements(c)
    with c.cd(BASE_DIR):
        c.run("stow .")
