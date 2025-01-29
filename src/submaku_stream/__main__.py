import asyncio
import sys
import time

import ffmpeg
import loguru
import numpy as np
from anyio import EndOfStream
from bilibili_api import ResponseCodeException
from httpx import NetworkError
from whisper import Whisper

from .locales.i18n import gettext as _
from .transcribers import whispers
from .utils import network, text
from .utils.audio import process_audio_segments
from .utils.storage import ConfigStorage

logger = loguru.logger
config = ConfigStorage.get_instance().config


class DanmakuManager:
    def __init__(self):
        # A queue storing danmaku that await to be sent
        self._msg_queue = asyncio.Queue()
        self._sent_danmaku_amount = 0
        self._prev_sending_timestamp = 0

    async def _send_danmaku(self, msg):
        dt = time.time() - self._prev_sending_timestamp
        if dt < config.sending_delay:
            time_to_sleep = config.sending_delay - dt
            logger.info(_("Postpone {:.4f} seconds before sending due to sending delay.").format(time_to_sleep))
            await asyncio.sleep(time_to_sleep)
        resp = await network.send_danmaku(msg)
        self._prev_sending_timestamp = time.time()
        logger.success(_("Sent: {}").format(msg))
        logger.debug(resp)

    async def sending_worker(self):
        if not config.should_send_danmaku:
            return
        while True:
            # Include the normal sending process
            for t in range(0, config.retry_times + 1):
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
                logger.warning(_("Retry times exceeded, so current task is given up."))
                return
            self._sent_danmaku_amount += 1

    async def put_danmaku(self, msg):
        await self._msg_queue.put(msg)

    @property
    def sent_danmaku_amount(self):
        return self._sent_danmaku_amount


async def main():
    def logger_level_setup():
        logger.remove()
        if config.debug:
            logger.warning(_("Debug mode is enabled."))
            logger.add(sys.stderr, level="DEBUG")
        else:
            logger.add(sys.stderr, level=config.log_level)

    def model_setup() -> Whisper:
        logger.info(_("Loading model..."))
        t0_perf = time.time()
        m = whispers.LocalWhisper("base").model
        delta_t_perf = (time.time() - t0_perf) * 1000
        logger.success(_("Model loaded. {:.2f}ms").format(delta_t_perf))
        return m

    logger_level_setup()

    stream_url = (await network.get_stream_urls())[0]
    logger.info(_("Stream URL: {}").format(stream_url))

    model = model_setup()
    dm = DanmakuManager()

    asyncio.create_task(dm.sending_worker())
    logger.success(_("sending_worker task has been created."))
    while 1:
        try:
            async for audio_chunk in process_audio_segments(stream_url, chunk_duration=config.segment_time_length):
                asyncio.create_task(voice2text_worker(model, audio_chunk, dm))
        except EndOfStream:
            logger.warning(_("Stream ended, program exiting."))
            sys.exit(0)
        except ffmpeg.Error as e:
            logger.error(_("Error occurred while processing the audio stream:"), e)
            logger.error(e.stderr.decode())


async def voice2text_worker(model: Whisper, audio_array: np.ndarray, dm: DanmakuManager):
    async def transcribe(audio_arr: np.ndarray):
        t0_perf = time.time()
        try:
            res = await asyncio.to_thread(model.transcribe, audio_arr, **config.whisper_params)
        except RuntimeError as e:
            logger.error(repr(e))
            return
        dt = (time.time() - t0_perf) * 1000
        return res, dt

    result, dt_perf = await transcribe(audio_array)
    logger.debug(result)

    # Detect empty transcription
    if not (res_text := result["text"]):
        logger.info(_('<EMPTY> {:.2f}ms').format(dt_perf))
        return

    # Process transcription text
    processed_transcription_text = text.remove_redundant_repeats(res_text)
    formatted_text = config.danmaku_text_format.format(
        transcription_text=processed_transcription_text,
        sent_danmaku_amount=dm.sent_danmaku_amount,
        danmaku_order_num=dm.sent_danmaku_amount % config.max_order_num
    )
    logger.info(_('{} {:.2f}ms').format(formatted_text, dt_perf))

    # Text segmentation
    if config.max_chars_per_danmaku and len(formatted_text) > config.max_chars_per_danmaku:
        logger.info(_("Text is trimmed due to exceeding char limits."))
        mcpd = config.max_chars_per_danmaku
        mcpas = config.max_chars_per_audio_segment if config.max_chars_per_audio_segment != 0 else len(formatted_text)
        formatted_text = formatted_text[:mcpas]
        i = 0
        end = 0
        for end in range(mcpd, len(formatted_text) + 1, mcpd):
            segment = formatted_text[end - mcpd:end]
            logger.info(_("Segment{i}: {segment}").format(i=i, segment=segment))
            await dm.put_danmaku(segment)
            i += 1
        formatted_text = formatted_text[end: end + mcpd - 1]
        if formatted_text:
            logger.info(_("Segment{i}: {formatted_text}").format(i=i, formatted_text=formatted_text))

    if formatted_text:
        await dm.put_danmaku(formatted_text)


if __name__ == '__main__':
    asyncio.run(main(), debug=config.debug)
