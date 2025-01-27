from bilibili_api import sync

from .utils.audio import process_audio_segments, save_audio_to_wav
from .utils.network import get_stream_urls


async def test():
    stream_url = (await get_stream_urls())[0]
    for i, audio_chunk in enumerate(process_audio_segments(stream_url, chunk_duration=5)):
        print(f"Processing chunk {i + 1} with {len(audio_chunk)} samples.")
        print(audio_chunk)
        save_audio_to_wav(audio_chunk, 16000, f"chunk_{i}.wav")
        if i == 4:
            break


sync(test())
