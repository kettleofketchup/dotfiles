
from ...misc.platforms import is_darwin, is_windows, is_linux, is_ubuntu_22, is_ubuntu_24, is_ubuntu
from ...misc.helpers import cmd_exists, download_file
from ...misc.config import  config, Config
from ...misc.console import print_success, print_error, console, print

from scripts.tools.terminal.autoenv import install as install_autoenv
from scripts.tools.terminal.bat import install as install_bat
from scripts.tools.terminal.fzf import install as install_fzf
from scripts.tools.terminal.kitty import install as install_kitty
from scripts.tools.terminal.lsd import install as install_lsd
from scripts.tools.terminal.ohmyposh import install as install_ohmyposh
from scripts.tools.terminal.plugins import install as install_plugins
from scripts.tools.terminal.zoxide import install as install_zoxide
from scripts.tools.terminal.tasks import install_all
