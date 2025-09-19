from invoke import Collection, task
from . import go, nvm, python, rust

ns = Collection("languages")

for module in [go, nvm, python, rust]:
    ns.add_collection(Collection.from_module(module), name=module.__name__.split(".")[-1])






@task
def install_all(c):
    """Installs all general tools."""
    for module in [go, nvm, python, rust]:
        c.run(f"invoke languages.{module.__name__.split('.')[-1]}.install")