from datetime import datetime
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    TypeAdapter,
    field_validator,
    model_validator,
)


# 1. Models using strict type checking
class TextMessage(BaseModel):
    model_config = ConfigDict(strict=True)
    msg_type: Literal["text"]
    text: str
    sent_at: datetime


class MediaMessage(BaseModel):
    model_config = ConfigDict(strict=True)
    msg_type: Literal["media"]
    url: str
    size_bytes: int = Field(gt=0)
    sent_at: datetime


# 2. Tagged union for fast O(1) matching
class Conversation(BaseModel):
    model_config = ConfigDict(strict=True)
    message: TextMessage | MediaMessage = Field(discriminator="msg_type")
    sender_id: int

    # Field validator (before internal parsing)
    @field_validator("sender_id", mode="before")
    @classmethod
    def cast_string_id(cls, v: str | int) -> int:
        if isinstance(v, str):
            return int(v)
        return v

    # Model validator (after model assembly)
    @model_validator(mode="after")
    def validate_message_payload(self) -> "Conversation":
        if self.message.msg_type == "text" and not self.message.text:
            raise ValueError("Text message cannot be empty")
        return self


# 3. Instantiate TypeAdapter once for reuse
conversation_list_adapter = TypeAdapter(list[Conversation])


def parse_conversations(json_data: bytes) -> list[Conversation]:
    # Parsing directly from JSON bytes using Rust core
    return conversation_list_adapter.validate_json(json_data)
