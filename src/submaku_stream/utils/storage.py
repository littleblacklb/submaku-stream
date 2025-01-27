from dataclasses import dataclass
from typing import Type, TypeVar

import bilibili_api
from bilibili_api.live import LiveRoom

from ..config_models import Credential, Config
from ..constants import CONFIG_PATH, CREDENTIAL_PATH

T = TypeVar('T')


class ConfigStorage:
    __instance = None

    def __init__(self):
        self.config = Config.load_from_json(CONFIG_PATH)
        self.credential = Credential.load_from_json(CREDENTIAL_PATH)

    @classmethod
    def get_instance(cls: Type[T]) -> T:
        if not ConfigStorage.__instance:
            ConfigStorage.__instance = ConfigStorage()
        return ConfigStorage.__instance


_config = ConfigStorage.get_instance()


@dataclass
class Constants:
    credential: bilibili_api.Credential = bilibili_api.Credential(_config.credential.SESSDATA,
                                                                  _config.credential.bili_jct)
    live_room: LiveRoom = LiveRoom(_config.config.room_id, credential)
