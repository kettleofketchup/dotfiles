from .platforms import is_darwin, is_linux
import requests
from invoke import Context
from scripts.misc.config import config
from pathlib import Path
from .console import print
def cmd_exists(command:str) -> bool:
    """Check if a command exists on the remote system."""
    if not is_linux() and not is_darwin():
        return False
    c = Context()
    result = c.run(f"command -v {command}", warn=True, hide=True)
    return result.ok


def run_sudo(c: Context, command: str):
    """Run a command with sudo privileges."""
    c.config.sudo.password = config.get_password()
    if is_darwin():
        c.sudo(f"{command}", pty=True, password=config.get_password())
    elif is_linux():
        print(f"[green]Running sudo cmd: {command}[/green]")
        c.sudo(f"{command}", password=config.get_password(), )
    else:
        raise EnvironmentError("Unsupported platform for sudo command.")

def download_file(url, filename: Path):
    print(f"Downloading {filename.name}...")
    resp = requests.get(url, stream=True, timeout=30)
    resp.raise_for_status()

    with filename.open("wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)


