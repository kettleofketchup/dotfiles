from invoke import Program, context
import invoke
from scripts.tasks import ns
from rich.traceback import install
install(suppress=[invoke], show_locals=True)
