"""실행 중인 0.2 앱 응답. 초기 0.1 화면 계약과 구분한다."""

from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict

from bonghwajigi.contracts.analysis import Source
from bonghwajigi.contracts.app import AppProfile, LocationWrite
from bonghwajigi.contracts.policy import CurrentStateInput


class Meta(BaseModel):
    schema_version: Literal["0.2.0-mvp"]
    mode: Literal["simulation"]
    request_id: str
    generated_at: AwareDatetime
    data_status: Literal["current", "partial", "stale", "unavailable"]


class Envelope[T](BaseModel):
    meta: Meta
    data: T


class ProfileData(BaseModel):
    revision: int
    input_revision: int
    profile: AppProfile


class LocationData(BaseModel):
    revision: int
    input_revision: int
    status: Literal["available", "stale", "unavailable"]
    fix: LocationWrite | None
    valid_until: AwareDatetime | None
    reason_codes: list[str]


class GuidanceItem(BaseModel):
    id: str
    text: str
    source: Source
    revision: int


class PreparedItem(GuidanceItem):
    valid_until: AwareDatetime
    reason_code: str


class AvoidItem(GuidanceItem):
    valid_until: AwareDatetime


class PreparationsData(BaseModel):
    status: Literal["available", "unavailable"]
    policy_version: str
    profile_revision: int
    generated_at: AwareDatetime
    items: list[PreparedItem]


class RulesData(BaseModel):
    disaster_type: Literal["wildfire"]
    status: Literal["available", "unavailable"]
    policy_version: str
    items: list[GuidanceItem]
    avoid: list[AvoidItem]


class Relevance(BaseModel):
    status: str
    reason_code: str


class AlertData(BaseModel):
    id: str
    revision: int
    response_id: str | None
    incident_id: str
    original_text: str
    official_severity: str
    authority: str
    issued_at: AwareDatetime
    valid_until: AwareDatetime
    instruction_kind: str
    source: Source
    status: Literal["active", "cancelled", "unconfirmed_or_expired"]
    relevance: Relevance
    requires_qwen: Literal[False]


class DisasterData(BaseModel):
    id: str
    title: str
    origin: str
    observed_at: AwareDatetime
    relevance: str
    reason: str
    response_id: str | None
    data_status: Literal["current", "stale"]


class HomeData(BaseModel):
    nearby_disasters: list[DisasterData]
    basic_rules: RulesData
    location: LocationData
    features: dict[str, bool | str]
    preparations: PreparationsData
    alerts: list[AlertData]


class PersonalResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    level: Literal["prepare", "act", "request_assistance", "information", "unknown"]
    number: int | None
    label: str
    reason_codes: list[str]


class PolicyAction(BaseModel):
    model_config = ConfigDict(extra="allow")
    action_id: str
    text: str
    priority: int
    source: Source


class PolicyUtterance(BaseModel):
    id: str
    text: str
    source: Literal["reviewed_policy_text"]
    valid_until: AwareDatetime | None


class UserContextData(BaseModel):
    revision: int
    status: Literal["available", "stale", "unavailable"]
    data: CurrentStateInput | None


class PolicyContent(BaseModel):
    model_config = ConfigDict(extra="allow")
    mode: Literal["simulation"]
    operational_use: Literal[False]
    disaster_type: Literal["wildfire"]
    incident_id: str
    incident: dict
    state: str
    relevance: Relevance
    personal_response: PersonalResponse
    actions: list[PolicyAction]
    official_alerts: list[dict]
    prediction: dict
    context: dict
    input_versions: dict[str, int]
    valid_until: AwareDatetime | None
    assistant_utterance: PolicyUtterance | None


class SnapshotData(BaseModel):
    id: str
    scenario_id: str
    revision: int
    evaluated_at: AwareDatetime | None
    pending_update: bool
    error_code: str | None
    content: PolicyContent | None
    user_context: UserContextData
