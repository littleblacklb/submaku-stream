import asyncio
import sys
import time

import ffmpeg
import loguru
from anyio import EndOfStream
from whisper import Whisper

from submaku_stream.workers.danmaku_sender import DanmakuSendingWorker
from submaku_stream.workers.voice2text import voice2text_worker
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
    while 1:
        try:
            async for audio_chunk in process_audio_segments(stream_url, chunk_duration=config.segment_time_length):
                asyncio.create_task(voice2text_worker(model, audio_chunk, sending_worker))
        except EndOfStream:
            logger.warning(_("Stream ended, program exiting."))
            sys.exit(0)
        except ffmpeg.Error as e:
            logger.error(_("Error occurred while processing the audio stream:"), e)
            logger.error(e.stderr.decode())


if __name__ == '__main__':
    asyncio.run(main(), debug=config.debug)
