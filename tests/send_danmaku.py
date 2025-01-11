from bilibili_api import sync

import utils


async def test():
    print(await utils.send_danmaku("测试~"))


if __name__ == '__main__':
    sync(test())
