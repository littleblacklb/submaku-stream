from bilibili_api import Danmaku, DmMode

from storage import Statics


async def send_danmaku(msg: str) -> dict:
    """
    Send a danmaku to bilibili live room.
    :param msg: message to be sent
    :return: API result
    """
    # TODO mode to be customized
    return await Statics.sender.send_danmaku(Danmaku(msg, mode=DmMode.BOTTOM))
