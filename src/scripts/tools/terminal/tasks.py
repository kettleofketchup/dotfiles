from invoke import Collection, task

from . import kitty, ghostty, autoenv, bat, fzf, plugins, zoxide,ohmyposh, lsd, tdrop

ns = Collection("terminal")
packages = [ghostty, kitty, autoenv, zoxide, ohmyposh, lsd, bat, fzf, plugins, tdrop]
for module in packages:
    ns.add_collection(Collection.from_module(module), name=module.__name__.split(".")[-1])


@task
def install_all(c):
    """Installs all terminal tools."""
    for module in packages:
        c.run(f"invoke terminal.{module.__name__.split('.')[-1]}.install")

ns.add_task(install_all, "all")