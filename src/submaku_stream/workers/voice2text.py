import asyncio
import time

import loguru
import numpy as np
from whisper import Whisper

from submaku_stream.locales.i18n import gettext as _
from submaku_stream.utils import text
from submaku_stream.utils.storage import ConfigStorage
from submaku_stream.workers.danmaku_sender import DanmakuSendingWorker

logger = loguru.logger
config = ConfigStorage.get_instance().config

async def voice2text_worker(model: Whisper, audio_array: np.ndarray, dm: DanmakuSendingWorker):
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
