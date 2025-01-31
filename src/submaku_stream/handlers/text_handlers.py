from __future__ import annotations

import loguru

from submaku_stream.base.handler import Handler
from submaku_stream.utils import text as text_tools
from submaku_stream.utils.storage import ConfigStorage

logger = loguru.logger


class TextHandler(Handler):
    _next_handler: Handler = None

    def set_next(self, handler: TextHandler) -> TextHandler:
        self._next_handler = handler
        return handler

    async def handle(self, text: str) -> str:
        if self._next_handler:
            return await self._next_handler.handle(text)
        return text


class TextPreprocessorHandler(TextHandler):
    async def handle(self, text: str) -> str:
        return await super().handle(text_tools.remove_redundant_repeats(text))


class TextFormatterHandler(TextHandler):
    def __init__(self, total_chunks: int):
        super().__init__()
        self.total_chunks = total_chunks

    async def handle(self, text: str) -> str:
        config = ConfigStorage.get_instance().config
        formatted_text = config.danmaku_text_format.format(
            transcription_text=text,
            sent_danmaku_amount=self.total_chunks,
            danmaku_order_num=self.total_chunks % config.max_order_num
        )
        logger.info(formatted_text)
        return await super().handle(formatted_text)
