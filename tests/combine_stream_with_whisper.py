import time

import whisper
from bilibili_api import sync

from utils.audio import process_audio_segments
from utils.network import get_stream_urls
from utils.storage import ConfigStorage


async def main():
    model = whisper.load_model("base")
    stream_url = (await get_stream_urls())[0]
    for i, audio_chunk in enumerate(process_audio_segments(stream_url, chunk_duration=5)):
        # print(f"Processing chunk {i + 1} with {len(audio_chunk)} samples.")
        # print(audio_chunk)
        t0 = time.time()
        result = model.transcribe(audio=audio_chunk, **ConfigStorage.get_instance().config.whisper_params)
        delta_t = (time.time() - t0) * 1000
        print(result["text"], f"({delta_t:.2f}ms)")
        # if i == 4:
        #     break


sync(main())
