"""
Base Transcription
"""
from abc import ABC


class BaseTranscriber(ABC):
    async def transcribe(self, audio_segments):
        raise NotImplementedError
