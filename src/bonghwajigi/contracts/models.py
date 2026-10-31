from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class GenerateRequest(BaseModel):
    """내부 연결용 초안. 실제 토큰 수 검사는 D3의 tokenizer 연결 시 추가한다."""

    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=1, max_length=16000)
    max_output_tokens: int = Field(default=512, ge=1, le=512)


class EmbedRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    texts: list[Annotated[str, Field(min_length=1, max_length=16000)]] = Field(
        min_length=1, max_length=8
    )
