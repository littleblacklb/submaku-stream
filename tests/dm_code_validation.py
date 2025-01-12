from bilibili_api import DmMode

from storage import ConfigStorage

if __name__ == '__main__':
    semantic_mode = ConfigStorage.get_instance().config.danmaku_display_mode
    mode: int = DmMode[semantic_mode].value
    print(mode)
