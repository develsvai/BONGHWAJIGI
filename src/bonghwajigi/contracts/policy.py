from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

from bonghwajigi.contracts.analysis import Source
from bonghwajigi.contracts.routes import ReferenceRoute
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
    child_registered: bool = False
    assistive_device: bool = False
    # Legacy simulation rules only. The approved policy uses confirmed CurrentStateInput.
    children_accompanying: bool = False
    mobility: Literal["unknown", "independent", "needs_time", "requires_help"] = "unknown"
    helper_registered: bool | None = None
    vehicle_access: bool | None = None
    communication: Literal["text", "audio", "both"] = "text"


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
    instruction_kind: Literal["evacuate", "prepare", "information", "unknown"] = "unknown"

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
    review_state: Literal["draft", "simulation_only", "approved_mvp"]
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
    review_state: Literal["draft", "simulation_only", "approved_mvp"]
    policy_version: Literal["wildfire-three-stage-v1"] | None = None
    rules: list[Rule] = Field(max_length=30)

    @model_validator(mode="after")
    def check(self):
        if self.review_state == "approved_mvp" and (
            self.policy_version != "wildfire-three-stage-v1" or self.rules
        ):
            raise ValueError("확정 MVP 정책은 고정된 3단계 실행기를 사용합니다.")
        if len({rule.action_id for rule in self.rules}) != len(self.rules):
            raise ValueError("행동 ID는 중복될 수 없습니다.")
        return self


class TimedInput(Versioned):
    observed_at: AwareDatetime
    expires_at: AwareDatetime

    @model_validator(mode="after")
    def check_time(self):
        if self.expires_at <= self.observed_at:
            raise ValueError("유효 종료 시각은 관측 시각 이후여야 합니다.")
        return self


class EnvironmentInput(TimedInput):
    hazard_band: Literal["H1", "H2", "H3", "unknown"]
    source: Source
    reason: str = Field(min_length=1, max_length=500)


class CurrentStateInput(TimedInput):
    child_present: bool | None = None
    alone_now: Literal["yes", "no", "unknown"] = "unknown"
    mobility_override: Literal["unknown", "independent", "needs_time", "requires_help"] | None = (
        None
    )
    helper_present: bool | None = None
    can_move: bool | None = None
    injured: bool | None = None
    observed_hazard: Literal["unknown", "none", "smoke", "flames", "fear", "trapped"] = "unknown"
    location_type: Literal["unknown", "house", "outside", "vehicle"] = "unknown"
    evacuation_status: Literal["unknown", "not_started", "moving", "arrived"] = "unknown"
    deescalation_confirmed: bool = False

    @model_validator(mode="after")
    def consistent_companions(self):
        if self.alone_now == "yes" and (self.child_present is True or self.helper_present is True):
            raise ValueError("혼자 있음과 현재 동행 상태를 함께 확인할 수 없습니다.")
        return self


class RouteInput(TimedInput):
    status: Literal["open", "blocked", "unknown"]
    source: Source
    reason: str = Field(min_length=1, max_length=500)
    # open은 현재 이용 가능한 대피 경로, blocked는 이용 가능한 대체 경로도 없다는 뜻이다.
    destination: str | None = Field(default=None, max_length=300)
    reference_route: ReferenceRoute | None = None


class UrgentInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    incident_id: Identifier
    alert_id: Identifier
    incident: IncidentInput
    alert: AlertInput
