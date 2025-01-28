"""
Base Transcriber
"""
from abc import ABC, abstractmethod


class BaseTranscriber(ABC):
    @abstractmethod
    async def transcribe(self, audio_segments):
        raise NotImplementedError
