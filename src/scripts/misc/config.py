import platform
import subprocess
from pydantic import BaseModel, Field, SecretStr
from functools import lru_cache
from .console import print_error
import getpass 

class Config(BaseModel):
    id: str = Field(default="")
    version: str = Field(default="")
    major_version: str = Field(default="")
    name: str = Field(default="")
    os: str = Field(default="")
    password: SecretStr = Field(default=SecretStr(""))

    def get_password(self) -> str:
        if not self.password.get_secret_value():
            self.password = SecretStr(getpass.getpass("Enter sudo password: "))
        return self.password.get_secret_value()

@lru_cache(maxsize=None)
def get_distro_info() -> Config:
    """
    Factory function to create and return a singleton DistroInfo instance.
    """
    os_name = platform.system()
    if os_name != "Linux":
        return Config(os=os_name)

    try:
        result = subprocess.check_output(['lsb_release', '-a'], text=True, stderr=subprocess.DEVNULL)
        info = {key.strip(): value.strip() for key, value in (line.split(':', 1) for line in result.strip().split('\n') if ':' in line)}

        version = info.get('Release', '')
        major_version = version.split('.')[0] if version else ''

        return Config(
            os=os_name,
            id=info.get('Distributor ID', '').lower(),
            version=version,
            name=info.get('Description', '').replace('"', ''),
            major_version=major_version
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        print_error("Warning: `lsb_release` not found. Cannot determine Linux distribution details.")
        return Config(os=os_name)

config = get_distro_info()
