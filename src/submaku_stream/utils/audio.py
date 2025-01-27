import asyncio.subprocess
from subprocess import Popen

import ffmpeg
import loguru
import numpy as np
import soundfile as sf
from anyio import EndOfStream

from ..locales.i18n import gettext as _

logger = loguru.logger


async def process_audio_segments(stream_url, chunk_duration=10, sample_rate=16000, cookie=None):
    """
    Processes a live audio stream in consecutive fixed-length chunks.

    Args:
        stream_url (str): URL of the live audio stream.
        chunk_duration (int): Duration of each chunk in seconds.
        sample_rate (int): Sample rate of the audio (e.g., 16000 Hz).
        cookie (str): Optional authorization cookie.

    Yields:
        np.ndarray: A NumPy array containing raw audio data for each chunk.
    """
    # Calculate the number of samples per chunk
    samples_per_chunk = chunk_duration * sample_rate

    # Prepare FFmpeg input arguments with optional headers
    input_args = {}
    if cookie:
        input_args['headers'] = f"Cookie: {cookie}"

    # Start the FFmpeg process
    process: Popen = (
        ffmpeg.input(stream_url, **input_args).output("pipe:1", format="s16le", acodec="pcm_s16le", ar=sample_rate,
                                                      ac=1)  # 16kHz, mono
        .run_async(pipe_stdout=True, pipe_stderr=True, quiet=True))
    logger.success(_("FFmpeg process has been launched."))

    while True:
        # Read fixed-length audio chunks from the stream
        chunk_size = samples_per_chunk * 2  # 2 bytes per sample (16-bit PCM)
        raw_audio = await asyncio.to_thread(process.stdout.read, chunk_size)

        if not raw_audio:
            raise EndOfStream(_("Stream ended."))
        if len(raw_audio) < chunk_size:
            logger.warning(_("The input raw_audio's size is less than chunk_size."))

        # Convert raw_audio to NumPy array
        audio_array = np.frombuffer(raw_audio, dtype=np.int16).astype(np.float32) / 32768.0  # Normalize
        yield audio_array


def save_audio_to_wav(audio_array, sample_rate, output_file):
    """
    Save a NumPy audio array to a WAV file.

    Args:
        audio_array (np.ndarray): The audio array (normalized to range [-1.0, 1.0]).
        sample_rate (int): The sample rate of the audio (e.g., 16000 for 16kHz).
        output_file (str): The file path to save the WAV file.

    Returns:
        None
    """
    # Ensure the audio array is in the correct range and format
    audio_array = (audio_array * 32768).astype('int16')  # Convert back to 16-bit PCM format
    sf.write(output_file, audio_array, samplerate=sample_rate)
    print(_("Audio saved to {}").format(output_file))
