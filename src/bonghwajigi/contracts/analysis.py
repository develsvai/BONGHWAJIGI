from datetime import datetime
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, HttpUrl, model_validator


class Source(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1, max_length=500)
    url: HttpUrl
    published_at: AwareDatetime
    collected_at: AwareDatetime
    verified: bool = False
    publisher: str | None = Field(default=None, max_length=200)
    publisher_url: HttpUrl | None = None

    @model_validator(mode="after")
    def check_collection_time(self):
        if self.published_at > self.collected_at:
            raise ValueError("수집 시각은 발표 시각보다 빠를 수 없습니다.")
        return self


class AnalysisInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    disaster_type: Literal["wildfire"] = "wildfire"
    text: str = Field(min_length=1, max_length=6000)
    search_query: str = Field(min_length=1, max_length=200)
    as_of: AwareDatetime
    source: Source

    @model_validator(mode="after")
    def check_time(self):
        if self.source.published_at > self.as_of:
            raise ValueError("원자료 발표 시각이 시나리오 평가 시각보다 미래입니다.")
        return self


class RetrievalDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mode: Literal["simulation"]
    scenario_id: str = Field(min_length=1, max_length=128)
    document_id: str = Field(min_length=1, max_length=128)
    revision: int = Field(default=1, ge=1)
    disaster_type: Literal["wildfire"] = "wildfire"
    origin: Literal["synthetic", "historical_replay", "collected_sample"]
    source_kind: Literal["stored_document", "news_search"] = "stored_document"
    text: str = Field(min_length=1, max_length=12000)
    source: Source
    valid_from: AwareDatetime
    valid_until: AwareDatetime | None = None

    @model_validator(mode="after")
    def check_validity(self):
        if self.valid_until and self.valid_until <= self.valid_from:
            raise ValueError("유효 기간의 끝은 시작보다 뒤여야 합니다.")
        return self


class AcceptedJob(BaseModel):
    job_id: str
    scenario_id: str
    status: str
    duplicate: bool
    mode: Literal["simulation"] = "simulation"


def utc_iso(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")
