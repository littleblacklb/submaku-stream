"""
OpenAI whisper
"""
from typing import Literal, Union

import numpy as np
import torch
import whisper

from base.transcriber import BaseTranscriber
from utils.storage import ConfigStorage


class LocalWhisper(BaseTranscriber):
    def __init__(self, model_name: Literal["tiny", "base", "small", "medium", "large", "turbo"] = "base"):
        """
        Whisper on local machine
        :param model_name: Model types
        """
        self.model_name = model_name
        self.model = whisper.load_model(model_name)
        self.params = ConfigStorage.get_instance().config.whisper_params

    async def transcribe(self, audio_segment: Union[str, np.ndarray, torch.Tensor], translate=False) -> str:
        """
        Transcribe audio segment
        :param audio_segment: File path or numpy array or torch tensor
        :param translate: Should translate to English?
        :return: Transcribed or translated text
        """
        return self.model.transcribe(audio_segment,
                                     task="translate" if translate else "transcribe",
                                     **self.params)["text"]
