import gettext as gt
from typing import Type, TypeVar

from utils.storage import ConfigStorage

T = TypeVar('T')


class I18n:
    __instance = None

    def __init__(self):
        self.__locale = "zh_CN"
        self.__translation = gt.translation('base', localedir='locales', languages=[self.__locale])

    @classmethod
    def get_instance(cls: Type[T]) -> T:
        if not I18n.__instance:
            I18n.__instance = I18n()
        return I18n.__instance

    def set_locale(self, locale: str):
        self.__locale = locale
        self.__translation = gt.translation('base', localedir='locales', languages=[self.__locale])

    def gettext(self, message: str) -> str:
        return self.__translation.gettext(message)


I18n.get_instance().set_locale(ConfigStorage.get_instance().config.program_display_language)

gettext = I18n.get_instance().gettext
