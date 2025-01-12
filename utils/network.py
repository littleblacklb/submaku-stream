from bilibili_api import Danmaku, DmMode
from bilibili_api.live import ScreenResolution

from storage import Statics, ConfigStorage


async def send_danmaku(msg: str) -> dict:
    """
    Send a danmaku to bilibili live room.
    :param msg: message to be sent
    :return: API result
    """
    sematic_code = ConfigStorage.get_instance().config.danmaku_display_mode
    return await Statics.live_room.send_danmaku(Danmaku(msg, mode=DmMode[sematic_code].value))


async def get_stream_urls() -> list:
    durls = (await Statics.live_room.get_room_play_url(ScreenResolution.FLUENCY))["durl"]
    res = [url["url"] for url in durls]
    # I don't know somehow the first streaming url is forbidden to access
    res.pop(0)
    return res
