import asyncio
import time
from asyncio import Queue
from typing import Union

import loguru
from bilibili_api import ResponseCodeException, Danmaku, DmMode
from httpx import NetworkError

from submaku_stream.locales.i18n import gettext as _
from submaku_stream.utils.storage import ConfigStorage, Constants

logger = loguru.logger
config = ConfigStorage.get_instance().config


class DanmakuMessage:
    def __init__(self, danmaku: Danmaku, msg_position: int):
        self.danmaku = danmaku
        self.msg_position = msg_position

    def __str__(self):
        return self.danmaku.text

    def __repr__(self):
        return f"DanmakuMessage(danmaku={self.danmaku}, msg_position={self.msg_position})"


class DanmakuSendingWorker:
    """
    A worker class that manages danmaku sending process.
    """

    def __init__(self):
        # A queue storing danmaku that await to be sent
        # TODO priority queue
        self._msg_queue: Queue[DanmakuMessage] = asyncio.Queue()
        self._sent_danmaku_amount = 0
        self._prev_sending_timestamp = 0
        self._cur_danmaku_position = 0

    async def _send_danmaku(self, msg: DanmakuMessage):
        dt = time.time() - self._prev_sending_timestamp
        if dt < config.sending_delay:
            time_to_sleep = config.sending_delay - dt
            logger.info(_("Postpone {:.4f} seconds before sending due to sending delay.").format(time_to_sleep))
            await asyncio.sleep(time_to_sleep)
        resp = await Constants.live_room.send_danmaku(msg.danmaku)
        # Generate a random sleep time to simulate the sending process
        self._prev_sending_timestamp = time.time()
        logger.success(_("Sent: {}").format(msg))
        logger.debug(resp)

    async def __call__(self):
        if not config.should_send_danmaku:
            return
        while True:
            # Include the normal sending process
            for t in range(0, config.max_retry_times + 1):
                if t > 0:
                    logger.info(_("Retry times: {}").format(t))
                try:
                    await self._send_danmaku(await self._msg_queue.get())
                    break
                except ResponseCodeException as e:
                    logger.error(str(e))
                    # 超出限制长度
                    if e.code == 1003212:
                        return
                except NetworkError as e:
                    logger.error(str(e))
                    logger.warning(_("Network error occurred, retrying..."))
                except Exception as e:
                    logger.error(repr(e))
            else:  # If the loop is not broken
                logger.warning(_("Retry times exceed max_retry_times, so current task is given up."))
                return
            self._sent_danmaku_amount += 1

    async def put_danmaku(self, msg: Union[DanmakuMessage, str]):
        """
        Put a danmaku message into the queue, and the message will be sent later.
        :param msg: A DanmakuMessage object or a string.
        """
        if isinstance(msg, str):
            sematic_code = ConfigStorage.get_instance().config.danmaku_display_mode
            msg = DanmakuMessage(Danmaku(text=msg, mode=DmMode[sematic_code].value), self._cur_danmaku_position)
            self._cur_danmaku_position += 1
        await self._msg_queue.put(msg)

    @property
    def sent_danmaku_amount(self):
        return self._sent_danmaku_amount
