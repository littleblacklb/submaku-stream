import asyncio
import sys
import time

import ffmpeg
import loguru
import numpy as np
from whisper import Whisper

from errors.EndOfStream import EndOfStream
from locales.i18n import gettext as _
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
        logger.warning(_("Debug mode is enabled."))
        logger.remove()
        logger.add(sys.stdout, level="DEBUG")
    stream_url = (await network.get_stream_urls())[0]
    logger.info(_("Stream URL: {}").format(stream_url))

    logger.info(_("Loading model..."))
    t0_perf = time.time()
    model = whispers.LocalWhisper("base").model
    delta_t_perf = (time.time() - t0_perf) * 1000
    logger.success(_("Model loaded. {:.2f}ms").format(delta_t_perf))

    await waiting_for_appending_queue_lock.acquire()
    asyncio.create_task(sending_worker())
    logger.success(_("sending_worker task has been created."))

    while 1:
        try:
            async for audio_chunk in process_audio_segments(stream_url, chunk_duration=config.segment_time_length):
                asyncio.create_task(voice2text_worker(model, audio_chunk))
        except EndOfStream:
            logger.warning(_("Stream ended, program exiting."))
            sys.exit(0)
        except ffmpeg.Error as e:
            logger.error(_("Error occurred while processing the audio stream:"), e)
            logger.error(e.stderr.decode())


async def voice2text_worker(model: Whisper, audio_array: np.ndarray):
    global sent_danmaku_amount
    sent_danmaku_amount += 1
    t0_perf = time.time()
    try:
        result = await asyncio.to_thread(model.transcribe, audio_array,
                                         **ConfigStorage.get_instance().config.whisper_params)
    except RuntimeError as e:
        logger.error(repr(e))
        return

    delta_t_perf = (time.time() - t0_perf) * 1000
    logger.debug(result)
    if not (res_text := result["text"]):
        logger.info(_('<EMPTY> {:.2f}ms').format(delta_t_perf))
        return
    processed_transcription_text = text.remove_redundant_repeats(res_text)
    formatted_text = config.danmaku_text_format.format(
        transcription_text=processed_transcription_text,
        sent_danmaku_amount=sent_danmaku_amount,
        danmaku_order_num=sent_danmaku_amount % config.max_order_num
    )
    logger.info(_('{} {:.2f}ms').format(formatted_text, delta_t_perf))

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
            msg_queue.append(segment)
            i += 1
        formatted_text = formatted_text[end: end + mcpd - 1]
        if formatted_text:
            logger.info(_("Segment{i}: {formatted_text}").format(i=i, formatted_text=formatted_text))

    if formatted_text:
        msg_queue.append(formatted_text)
    if waiting_for_appending_queue_lock.locked():
        # The msg_queue is not empty now.
        waiting_for_appending_queue_lock.release()


async def sending_worker():
    prev_sending_timestamp = 0
    if not config.should_send_danmaku:
        return
    while 1:
        try:
            async with waiting_for_appending_queue_lock:
                dt = time.time() - prev_sending_timestamp
                if dt < config.sending_delay:
                    time_to_sleep = config.sending_delay - dt
                    logger.info(_("Postpone {:.4f} seconds before sending due to sending delay.").format(time_to_sleep))
                    await asyncio.sleep(time_to_sleep)
                msg = msg_queue.pop(0)
                resp = await network.send_danmaku(msg)
                prev_sending_timestamp = time.time()
                logger.success(_("Sent: {}").format(msg))
                logger.debug(resp)
        except RuntimeError:
            # Ignore RuntimeError('Lock is not acquired.')
            # Why it occurs?
            # Cuz when the #send_danmaku is awaiting, the lock might be unlocked by voice2text_worker
            pass
        except Exception as e:
            logger.error(repr(e))
        finally:
            if len(msg_queue) == 0:
                logger.debug(_("Queue is empty"))
                await waiting_for_appending_queue_lock.acquire()


if __name__ == '__main__':
    asyncio.run(main(), debug=config.debug)
