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
from utils.storage import ConfigStorage

logger = loguru.logger
config = ConfigStorage.get_instance().config

sent_danmaku_amount = 0

# Danmaku that awaits to be sent
msg_queue = []
# The lock is locked when the queue is empty
waiting_for_appending_queue_lock = asyncio.Lock()


async def main():
    if config.debug:
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

        await waiting_for_appending_queue_lock.acquire()
        asyncio.create_task(sending_worker())
        logger.success("sending_worker task has been created.")

        while 1:
            try:
                async for audio_chunk in process_audio_segments(stream_url, chunk_duration=config.segment_time_length):
                    asyncio.create_task(voice2text_worker(model, audio_chunk))
            except ffmpeg.Error as e:
                logger.error("Error occurred while processing the audio stream:", e)
                logger.error(e.stderr.decode())
            except EndOfStream:
                logger.warning("Stream ended. Program exits")
                sys.exit(0)
    except asyncio.CancelledError:
        logger.warning("CancelledError is caught, exiting the program.")


async def voice2text_worker(model: Whisper, audio_array: np.ndarray):
    global sent_danmaku_amount
    sent_danmaku_amount += 1
    t0_perf = time.time()
    result = await asyncio.to_thread(model.transcribe, audio_array,
                                     **ConfigStorage.get_instance().config.whisper_params)
    delta_t_perf = (time.time() - t0_perf) * 1000
    logger.debug(result)
    if not (res_text := result["text"]):
        logger.info(f'<EMPTY> {delta_t_perf:.2f}ms')
        return
    processed_transcription_text = text.remove_repeated_phrases(res_text)
    formatted_text = config.danmaku_text_format.format(
        transcription_text=processed_transcription_text,
        sent_danmaku_amount=sent_danmaku_amount,
        danmaku_order_num=sent_danmaku_amount % config.max_order_num
    )
    logger.debug(sent_danmaku_amount)
    logger.info(f'{formatted_text} {delta_t_perf:.2f}ms')
    msg_queue.append(formatted_text)
    if waiting_for_appending_queue_lock.locked():
        # The msg_queue is not empty now.
        waiting_for_appending_queue_lock.release()


async def sending_worker():
    if not config.should_send_danmaku:
        return
    while 1:
        try:
            async with waiting_for_appending_queue_lock:
                msg = msg_queue.pop(0)
                resp = await network.send_danmaku(msg)
                logger.success(f"Sent: {msg}")
                logger.debug(resp)
        except Exception as e:
            logger.error(repr(e))
        finally:
            if len(msg_queue) == 0:
                logger.debug("Queue is empty")
                await waiting_for_appending_queue_lock.acquire()


if __name__ == '__main__':
    asyncio.run(main(), debug=config.debug)
