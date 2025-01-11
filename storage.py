from dataclasses import dataclass
from pathlib import Path
from typing import Type, TypeVar

import bilibili_api
from bilibili_api.live import LiveRoom

from config_models import Credential, Config

T = TypeVar('T')

CONFIG_BASE_PATH = Path(__file__).parent / "configs"
CONFIG_PATH = CONFIG_BASE_PATH / "config.json"
CREDENTIAL_PATH = CONFIG_BASE_PATH / "credential.json"


class ConfigStorage:
    _instance = None

    def __init__(self):
        self.config = Config.load_from_json(CONFIG_PATH)
        self.credential = Credential.load_from_json(CREDENTIAL_PATH)

    @classmethod
    def get_instance(cls: Type[T]) -> T:
        if not ConfigStorage._instance:
            ConfigStorage._instance = ConfigStorage()
        return ConfigStorage._instance


_config = ConfigStorage.get_instance()


@dataclass
class Statics:
    credential: Credential = bilibili_api.Credential(_config.credential.SESSDATA, _config.credential.bili_jct)
    sender: LiveRoom = LiveRoom(_config.config.room_id, credential)
