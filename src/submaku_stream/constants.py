import os
import sys
from pathlib import Path

from loguru import logger

"""
Executable-related constants
"""

# https://pyinstaller.org/en/stable/runtime-information.html
# Whether the script is running in a frozen environment (e.g. Compiled from PyInstaller)
IS_FROZEN_ENV: bool = getattr(sys, 'frozen', False)
# Resource folder exists while the program is running in a Pyinstaller bundle
MEI_PATH: Path = Path()
if hasattr(sys, '_MEIPASS'):
    # noinspection PyProtectedMember
    MEI_PATH = Path(sys._MEIPASS)

"""
Path
"""

'''
DEFAULT ROOT_PATH:
Case1 Executable file: "exe file's parent directory" -> "configs"
Case2 Original structure: "repo's parent directory" -> "configs"
Case3 User-defined: "user-defined path"
'''

ROOT_PATH = Path(sys.executable).parent if IS_FROZEN_ENV else Path(__file__).parent

# Case3: User-defined path
if path := os.getenv("CONFIG_BASE_PATH"):
    CONFIG_BASE_PATH = Path(path)
else:
    # Case1: Might be an executable file's root path
    CONFIG_BASE_PATH = ROOT_PATH.parent / "configs"
    if not CONFIG_BASE_PATH.exists():
        # Case2: Default repo structure path
        CONFIG_BASE_PATH = ROOT_PATH.parent.parent / "configs"

CONFIG_PATH = CONFIG_BASE_PATH / "config.json"
CREDENTIAL_PATH = CONFIG_BASE_PATH / "credential.json"

LOCALE_PATH = ROOT_PATH / "locales" if not IS_FROZEN_ENV else MEI_PATH / "locales"

logger.debug(f"MEI_PATH: {MEI_PATH}")
logger.debug(f"ROOT_PATH: {ROOT_PATH}")
logger.debug(f"CONFIG_BASE_PATH: {CONFIG_BASE_PATH}")
