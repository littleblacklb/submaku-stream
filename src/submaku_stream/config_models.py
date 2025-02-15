from pathlib import Path
from typing import TypeVar, Type, Literal

from pydantic import BaseModel

T = TypeVar('T')


class MyBaseModel(BaseModel):
    @classmethod
    def load_from_json(cls: Type[T], path: Path) -> T:
        with open(path) as f:
            json_data = f.read()
            return cls.model_validate_json(json_data)


class Config(MyBaseModel):
    program_display_language: Literal["zh_CN", "en"]
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    platform: str
    room_id: int
    danmaku_display_mode: Literal["FLY", "TOP", "BOTTOM"]
    sending_delay: int
    segment_time_length: int
    model_name: Literal["tiny", "base", "small", "medium", "large", "turbo"]
    whisper_params: dict
    danmaku_text_format: str
    max_order_num: int
    should_send_danmaku: bool
    max_retry_times: int
    max_chars_per_danmaku: int
    max_chars_per_audio_segment: int
    debug: bool


class Credential(MyBaseModel):
    SESSDATA: str
    bili_jct: str
