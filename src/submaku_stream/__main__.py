import asyncio
import sys
import time

import ffmpeg
import loguru
import numpy as np
from anyio import EndOfStream
from numpy import ndarray
from whisper import Whisper

from submaku_stream.handlers.text_handlers import TextPreprocessorHandler, TextFormatterHandler
from submaku_stream.workers.danmaku_sender import DanmakuSendingWorker
from .locales.i18n import gettext as _
from .transcribers import whispers
from .utils import network
from .utils.audio import process_audio_segments
from .utils.storage import ConfigStorage

logger = loguru.logger
config = ConfigStorage.get_instance().config


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
    sending_worker = DanmakuSendingWorker()

    asyncio.create_task(sending_worker())
    logger.success(_("sending_worker task has been created."))

    total_chunks = 0
    while 1:
        try:
            async for audio_chunk in process_audio_segments(stream_url, chunk_duration=config.segment_time_length):
                asyncio.create_task(process_worker(model, audio_chunk, sending_worker, total_chunks))
                total_chunks += 1
        except EndOfStream:
            logger.warning(_("Stream ended, program exiting."))
            sys.exit(0)
        except ffmpeg.Error as e:
            logger.error(_("Error occurred while processing the audio stream:"), e)
            logger.error(e.stderr.decode())


async def process_worker(model: Whisper, audio_chunk: ndarray, sending_worker: DanmakuSendingWorker, total_chunks: int):
    def text_segmentation(txt: str) -> list[str]:
        res = []
        if config.max_chars_per_danmaku and len(txt) > config.max_chars_per_danmaku:
            logger.info(_("Text is trimmed due to exceeding char limits."))
            mcpd = config.max_chars_per_danmaku
            mcpas = config.max_chars_per_audio_segment if config.max_chars_per_audio_segment != 0 else len(txt)
            txt = txt[:mcpas]
            i = 0
            end = 0
            for end in range(mcpd, len(txt) + 1, mcpd):
                seg = txt[end - mcpd:end]
                logger.info(_("Segment{i}: {segment}").format(i=i, segment=seg))
                res.append(seg)
                i += 1
            txt = txt[end: end + mcpd - 1]
            if txt:
                logger.info(_("Segment{i}: {formatted_text}").format(i=i, formatted_text=txt))
        if txt:
            res.append(txt)
        return res

    async def transcribe(audio_arr: np.ndarray):
        t0_perf = time.time()
        try:
            res = await asyncio.to_thread(model.transcribe, audio_arr, **config.whisper_params)
        except RuntimeError as e:
            logger.error(repr(e))
            return
        dt = (time.time() - t0_perf) * 1000
        return res["text"], dt

    text, dt_perf = await transcribe(audio_chunk)
    logger.info(_("Transcription costs: {:.2f}ms").format(dt_perf))
    logger.debug(text)
    chains = TextPreprocessorHandler().set_next(TextFormatterHandler(total_chunks))
    product = await chains.handle(text)
    for segment in text_segmentation(product):
        await sending_worker.put_danmaku(segment)


if __name__ == '__main__':
    # TODO add exit handler
    asyncio.run(main(), debug=config.debug)
