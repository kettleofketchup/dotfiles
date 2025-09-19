from invoke import run, task
from scripts.misc import is_ubuntu, is_darwin, console, print, print_success, print_error, config, cmd_exists, is_linux, download_file
import requests
from invoke.context import Context
from pathlib import Path
GITHUB_API = "https://api.github.com/repos/ghostty-org/ghostty/releases/latest"
SCHEMA = "org.gnome.settings-daemon.plugins.media-keys"
PATH = "/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/"
SCRIPT = Path.home() / "bin" / "ghostty-toggle.sh"
NAME = "Ghostty Toggle"
KEY = "F1"

from invoke import task
from pathlib import Path
from scripts.misc.helpers import run_sudo
from scripts.tools.general.mac.brew import install as install_brew
def get_asset_url():
    resp = requests.get(GITHUB_API, timeout=10)
    resp.raise_for_status()
    release = resp.json()
    system = config.os.lower()
    urls = []

    for asset in release["assets"]:
        name = asset["name"].lower()
        if is_linux() and name.endswith(".deb"):
            urls.append((asset["browser_download_url"], name))
        elif is_darwin() and (name.endswith(".dmg") or name.endswith(".tar.gz")):
            urls.append((asset["browser_download_url"], name))


    if not urls:
        print_error(f"No suitable Ghostty asset found for {system}")

    return urls[0]  # just grab the first match





@task
def bind_f1(c):
    """
    Bind F1 to toggle Ghostty.
    """
    if not SCRIPT.exists():
        print(f"❌ Error: {SCRIPT} not found. Make sure toggle-ghostty exists.")
        return

    if not SCRIPT.is_file() or not SCRIPT.stat().st_mode & 0o111:
        print(f"❌ Error: {SCRIPT} is not executable. Run: chmod +x {SCRIPT}")
        return

    # Register the custom binding path
    c.run(f"gsettings set {SCHEMA} custom-keybindings \"['{PATH}']\"")

    # Configure the binding
    c.run(f"gsettings set {SCHEMA}.custom-keybinding:{PATH} name \"{NAME}\"")
    c.run(f"gsettings set {SCHEMA}.custom-keybinding:{PATH} command \"{SCRIPT}\"")
    c.run(f"gsettings set {SCHEMA}.custom-keybinding:{PATH} binding \"{KEY}\"")

    print(f"✅ Bound {KEY} to {SCRIPT}")


@task
def unbind_f1(c):
    """
    Remove F1 binding for Ghostty.
    """
    c.run(f"gsettings reset {SCHEMA} custom-keybindings")
    c.run(f"gsettings reset-recursively {SCHEMA}.custom-keybinding:{PATH}")

    print(f"🗑️  Unbound {KEY} from {SCRIPT}")


@task
def install(c):
    c: Context
    if not is_linux() and not is_darwin():
        print_error("Unsupported OS. Only Ubuntu and macOS are supported.")
        return
    
    if cmd_exists('ghostty'):
        print_success("ghostty is already installed.")
        return
    if is_darwin():
        install_brew(c)
        if cmd_exists('brew'):
            c.run("brew install ghostty")
            return
        else:
            print_error("Homebrew is not installed. Cannot install ghostty.")   
            return
            
    elif is_ubuntu():
        run_sudo(f"snap install ghostty --classic")
    else:
        print_error("Unsupported OS. Only Ubuntu and macOS are supported.")

