from bilibili_api import sync

from utils.network import send_danmaku


async def test():
    print(await send_danmaku("测试~"))


if __name__ == '__main__':
    sync(test())
