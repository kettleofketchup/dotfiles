from pathlib import Path    

BASE_DIR = Path(__file__).resolve().parent

SCRIPTS_DIR = BASE_DIR / "scripts"
CONFIGS_DIR = BASE_DIR / "configs"
LINUX_DIR = SCRIPTS_DIR / "linux"
LINUX_LANGUAGES_DIR = LINUX_DIR / "languages"

UNIVERSAL_DIR = SCRIPTS_DIR / "UNIVERSAL"