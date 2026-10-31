from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

from bonghwajigi.contracts.analysis import Source
from bonghwajigi.contracts.spatial import Box

Identifier = Annotated[str, Field(min_length=1, max_length=128, pattern=r"^[a-zA-Z0-9_.:-]+$")]


class Versioned(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mode: Literal["simulation"] = "simulation"
    revision: int = Field(ge=1)


class ClockInput(Versioned):
    evaluation_at: AwareDatetime | None = None


class ProfileInput(Versioned):
    mobility_assistance: bool = False
    children_accompanying: bool = False


class LocationInput(Versioned):
    latitude: float = Field(ge=-85, le=85, allow_inf_nan=False)
    longitude: float = Field(ge=-180, le=180, allow_inf_nan=False)
    accuracy_m: float = Field(ge=0, le=100000, allow_inf_nan=False)
    observed_at: AwareDatetime
    expires_at: AwareDatetime

    @model_validator(mode="after")
    def check(self):
        if self.expires_at <= self.observed_at:
            raise ValueError("위치 유효 종료 시각이 관측 시각보다 뒤여야 합니다.")
        return self


class IncidentInput(Versioned):
    origin: Literal["synthetic", "historical_replay", "collected_sample"]
    disaster_type: Literal["wildfire"] = "wildfire"
    title: str = Field(min_length=1, max_length=500)
    observed_at: AwareDatetime
    expires_at: AwareDatetime
    area: Box | None = None
    sources: list[Source] = Field(min_length=1, max_length=10)

    @model_validator(mode="after")
    def check(self):
        if self.expires_at <= self.observed_at:
            raise ValueError("사건 자료의 유효 기간이 잘못됐습니다.")
        if any(source.published_at > self.observed_at for source in self.sources):
            raise ValueError("평가 시각 이후의 출처를 입력에 사용할 수 없습니다.")
        return self


class AlertInput(Versioned):
    state: Literal["issued", "cancelled"]
    authority: str = Field(min_length=1, max_length=200)
    severity: str = Field(min_length=1, max_length=100)
    issued_at: AwareDatetime
    expires_at: AwareDatetime
    area: Box | None = None
    raw_text: str = Field(min_length=1, max_length=4000)
    source: Source
    validity_confirmed: bool = False

    @model_validator(mode="after")
    def check(self):
        if self.expires_at <= self.issued_at:
            raise ValueError("경보 유효 기간이 잘못됐습니다.")
        return self


class PredictionInput(Versioned):
    status: Literal["simulation", "unavailable"]
    probability: float | None = Field(default=None, ge=0, le=1, allow_inf_nan=False)
    model_id: str = Field(min_length=1, max_length=128)
    model_revision: str = Field(min_length=1, max_length=128)
    target: str = Field(min_length=1, max_length=300)
    observed_at: AwareDatetime
    expires_at: AwareDatetime
    area: Box | None = None
    operational_use: Literal[False] = False

    @model_validator(mode="after")
    def check(self):
        if self.expires_at <= self.observed_at:
            raise ValueError("예측 유효 기간이 잘못됐습니다.")
        if (self.status == "simulation") != (self.probability is not None):
            raise ValueError("모의 예측에만 확률이 필요하며 예측 불가이면 null이어야 합니다.")
        return self


class GuidanceInput(Versioned):
    review_state: Literal["draft", "simulation_only"]
    text: str = Field(min_length=1, max_length=1000)
    source: Source
    valid_from: AwareDatetime
    expires_at: AwareDatetime

    @model_validator(mode="after")
    def check(self):
        if self.expires_at <= self.valid_from:
            raise ValueError("참고 지침 유효 기간이 잘못됐습니다.")
        return self


class Rule(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action_id: Identifier
    when: Literal["related", "mobility_assistance", "children_accompanying"]
    guidance_id: Identifier
    priority: int = Field(ge=1, le=100)


class RuleSetInput(Versioned):
    review_state: Literal["draft", "simulation_only"]
    rules: list[Rule] = Field(max_length=30)

    @model_validator(mode="after")
    def check(self):
        if len({rule.action_id for rule in self.rules}) != len(self.rules):
            raise ValueError("행동 ID는 중복될 수 없습니다.")
        return self
