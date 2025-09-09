import platform
import subprocess
from pydantic import BaseModel
from .config import config
from .console import print
from functools import lru_cache


@lru_cache(maxsize=None)
def get_platform() -> str:
    return config


@lru_cache(maxsize=None)
def is_ubuntu() -> bool:
    """Returns True if the OS is any version of Ubuntu, else returns False."""
    if not is_linux():
        return False
    return config.id == "ubuntu"

@lru_cache(maxsize=None)
def is_ubuntu_22() -> bool:
    """Returns True if the OS is Ubuntu 22.xx, else returns False."""
    if not is_linux():
        return False
    if not is_ubuntu():
        return False
    global config
    return config.major_version == "22"

@lru_cache(maxsize=None)
def is_ubuntu_24() -> bool:
    """Returns True if the OS is Ubuntu 24.xx, else returns False."""
    if not is_linux():
        return False
    if not is_ubuntu():
        return False
    global config
    return config.major_version == "24"

@lru_cache(maxsize=None)
def is_linux() -> bool:
    """Returns True if the OS is Linux, else returns False."""
    get_platform()
    return config.os == "Linux"

@lru_cache(maxsize=None)
def is_darwin() -> bool:
    """Returns True if the OS is Darwin (macOS), else returns False."""
    get_platform()
    return config.os == "Darwin"

@lru_cache(maxsize=None)
def is_windows() -> bool:
    """Returns True if the OS is Windows, else returns False."""
    get_platform()
    return config.os == "Windows"