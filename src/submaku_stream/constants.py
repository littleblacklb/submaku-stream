import os
import sys
from pathlib import Path

from loguru import logger

"""
Executable-related constants
"""
# Whether the script is running in a frozen environment (e.g. Compiled from PyInstaller)
IS_FROZEN_ENV = getattr(sys, 'frozen', False)
MEI_PATH = ""
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

# User-defined path
if path := os.getenv("CONFIG_BASE_PATH"):
    CONFIG_BASE_PATH = Path(path)
else:
    # Might be executable file's root path
    CONFIG_BASE_PATH = ROOT_PATH.parent / "configs"
    if not CONFIG_BASE_PATH.exists():
        # Default repo structure path
        CONFIG_BASE_PATH = ROOT_PATH.parent.parent / "configs"
CONFIG_PATH = CONFIG_BASE_PATH / "config.json"
CREDENTIAL_PATH = CONFIG_BASE_PATH / "credential.json"

LOCALE_PATH = ROOT_PATH / "locales" if not IS_FROZEN_ENV else MEI_PATH / "locales"

logger.debug(f"MEI_PATH: {MEI_PATH}")
logger.debug(f"ROOT_PATH: {ROOT_PATH}")
logger.debug(f"CONFIG_BASE_PATH: {CONFIG_BASE_PATH}")
