from bilibili_api.live import ScreenResolution

from ..utils.storage import Constants


async def get_stream_urls() -> list:
    durls = (await Constants.live_room.get_room_play_url(ScreenResolution.FLUENCY))["durl"]
    res = [url["url"] for url in durls]
    # I don't know somehow the first streaming url is forbidden to access
    res.pop(0)
    return res
