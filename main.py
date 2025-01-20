import asyncio
import sys
import time

import ffmpeg
import loguru
import numpy as np
from whisper import Whisper

from errors.EndOfStream import EndOfStream
from transcribers import whispers
from utils import network, text
from utils.audio import process_audio_segments
from utils.storage import ConfigStorage, Statics

logger = loguru.logger
config = ConfigStorage.get_instance().config


async def main():
    if Statics.debug:
        logger.warning("Debug mode is enabled.")
        logger.remove()
        logger.add(sys.stdout, level="DEBUG")
    try:
        stream_url = (await network.get_stream_urls())[0]
        logger.info(f"Stream URL: {stream_url}")

        logger.info("Loading model...")
        t0_perf = time.time()
        model = whispers.LocalWhisper("base").model
        delta_t_perf = (time.time() - t0_perf) * 1000
        logger.success(f"Model loaded. {delta_t_perf:.2f}ms")
        while 1:
            try:
                async for audio_chunk in process_audio_segments(stream_url, chunk_duration=config.segment_time_length):
                    asyncio.create_task(danmaku_worker(model, audio_chunk))
            except ffmpeg.Error as e:
                logger.error("Error occurred while processing the audio stream:", e)
                logger.error(e.stderr.decode())
            except EndOfStream:
                logger.warning("Stream ended. Program exits")
                sys.exit(0)
    except asyncio.CancelledError:
        logger.warning("CancelledError is caught, exiting the program.")


async def danmaku_worker(model: Whisper, audio_array: np.ndarray):
    sent_danmaku_amount = 0

    async def _worker():
        nonlocal sent_danmaku_amount
        sent_danmaku_amount += 1
        t0_perf = time.time()
        result = model.transcribe(audio_array, **ConfigStorage.get_instance().config.whisper_params)
        delta_t_perf = (time.time() - t0_perf) * 1000
        logger.debug(result)
        processed_transcription_text = text.remove_repeated_phrases(result["text"])
        formatted_text = config.danmaku_text_format.format(
            transcription_text=processed_transcription_text,
            sent_danmaku_amount=sent_danmaku_amount,
            danmaku_order_num=sent_danmaku_amount % config.max_order_num
        )
        logger.debug(formatted_text)
        logger.info(f'{formatted_text} {delta_t_perf:.2f}ms')
        if not Statics.debug:
            resp = await network.send_danmaku(formatted_text)
            logger.debug(resp)

    await _worker()


if __name__ == '__main__':
    asyncio.run(main())
