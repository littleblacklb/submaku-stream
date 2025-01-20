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
    platform: str
    room_id: int
    danmaku_display_mode: Literal["FLY", "TOP", "BOTTOM"]
    sending_delay: int
    segment_time_length: int
    whisper_params: dict
    danmaku_text_format: str
    max_order_num: int
    should_send_danmaku: bool
    max_chars_per_danmaku: int
    max_chars_per_audio_segment: int
    debug: bool


class Credential(MyBaseModel):
    SESSDATA: str
    bili_jct: str
