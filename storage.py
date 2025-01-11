from dataclasses import dataclass
from typing import Type

import bilibili_api

from config_models import Credential, CREDENTIAL_PATH, T


class ConfigStorage:
    _instance = None

    def __init__(self):
        self.credential = Credential.load_from_json(CREDENTIAL_PATH)

    @classmethod
    def get_instance(cls: Type[T]) -> T:
        if not ConfigStorage._instance:
            ConfigStorage._instance = ConfigStorage()
        return ConfigStorage._instance


@dataclass
class Statics:
    credential: Credential = bilibili_api.Credential(ConfigStorage.get_instance().credential.SESSDATA,
                                                     ConfigStorage.get_instance().credential.bili_jct)
