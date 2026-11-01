from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue


class ScenarioEvent(BaseModel):
    """MVP 시나리오 입력 초안. 실제 수집 표준 계약은 B2에서 별도로 확정한다."""

    model_config = ConfigDict(extra="forbid")
    mode: Literal["simulation"]
    scenario_id: str = Field(min_length=1, max_length=128)
    event_id: str = Field(min_length=1, max_length=128)
    origin: Literal["synthetic", "historical_replay", "collected_sample"]
    queue: Literal["urgent", "analysis"]
    payload: dict[str, JsonValue]
