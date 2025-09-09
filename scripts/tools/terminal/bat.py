import platform
import tarfile
import requests
from invoke import task

from scripts.misc.helpers import run_sudo


@task
def install(c):
    """Installs bat."""
    uname_os = platform.system().lower()
    arch = platform.machine()
    if arch == "x86_64":
        arch = "x86_64"
    elif arch in ("arm64", "aarch64"):
        arch = "aarch64"
    else:
        raise Exception(f"Unsupported arch: {arch}")

    latest_json = requests.get(
        "https://api.github.com/repos/sharkdp/bat/releases/latest", timeout=60
    ).json()
    version = latest_json["tag_name"]

    if uname_os == "darwin":
        asset_pattern = f"bat-{version}-{arch}-apple-darwin.tar.gz"
    else:
        asset_pattern = f"bat-{version}-{arch}-unknown-linux-gnu.tar.gz"

    download_url = next(
        (
            asset["browser_download_url"]
            for asset in latest_json["assets"]
            if asset["name"] == asset_pattern
        ),
        None,
    )

    if not download_url:
        raise Exception(
            f"Could not find suitable release asset for OS={uname_os}, ARCH={arch}"
        )

    asset_path = f"/tmp/{asset_pattern}"
    c.run(f"curl -L {download_url} -o {asset_path}")

    with tarfile.open(asset_path, "r:gz") as tar:
        extracted_dir = tar.getnames()[0].split("/")[0]
        tar.extractall("/tmp")

    bat_path = f"/tmp/{extracted_dir}/bat"
    run_sudo(f"mv {bat_path} /usr/local/bin/bat")
    run_sudo("chmod +x /usr/local/bin/bat")
