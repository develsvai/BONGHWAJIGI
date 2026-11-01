from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

from bonghwajigi.contracts.policy import Identifier


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AppProfile(Strict):
    display_name: str = Field(default="", max_length=40)
    age_band: Literal["under_20", "20_39", "40_59", "60_plus", "unknown"] = "unknown"
    emergency_contact: str = Field(default="", max_length=120)
    usual_place: str = Field(default="", max_length=200)
    building_floor: str = Field(default="", max_length=40)
    health_consent: bool = False
    health_notes: str = Field(default="", max_length=500)
    mobility: Literal[
        "independent", "walking_aid", "wheelchair", "assistance_required", "unknown"
    ] = "unknown"
    stairs: Literal["able", "difficult", "unable", "unknown"] = "unknown"
    communication_preference: Literal["text", "voice", "both"] = "text"
    sensory_supports: list[Literal["vision", "hearing"]] = Field(default_factory=list, max_length=2)
    dependents: list[Literal["child", "care_recipient", "pet", "other"]] = Field(
        default_factory=list, max_length=4
    )
    helper_registered: bool | None = None
    vehicle_access: bool | None = None

    @model_validator(mode="after")
    def check_health_consent(self):
        if self.health_notes.strip() and not self.health_consent:
            raise ValueError("건강·의료 메모는 별도 동의가 필요합니다.")
        return self


class ProfileWrite(Strict):
    base_revision: int = Field(ge=0)
    profile: AppProfile


class Preferences(Strict):
    locale: Literal["ko-KR", "en-US"] = "ko-KR"
    notifications_enabled: bool = True
    nearby_radius_m: int = Field(default=10000, ge=1000, le=50000)
    home_area_code: str | None = Field(default=None, max_length=32)


class PreferencesWrite(Strict):
    base_revision: int = Field(ge=0)
    preferences: Preferences


class LocationWrite(Strict):
    fix_id: Identifier
    installation_id: Identifier
    latitude: float = Field(ge=-85, le=85, allow_inf_nan=False)
    longitude: float = Field(ge=-180, le=180, allow_inf_nan=False)
    accuracy_m: float = Field(ge=0, le=100000, allow_inf_nan=False)
    captured_at: AwareDatetime


class DeviceWrite(Strict):
    platform: Literal["android", "ios", "web"]
    push_provider: Literal["fcm"]
    push_token: str | None = Field(default=None, min_length=1, max_length=4096)
    notification_permission: Literal["granted", "denied", "not_determined"]
    app_version: str = Field(min_length=1, max_length=64)


class StatePatch(Strict):
    child_present: bool | None = None
    alone_now: Literal["yes", "no", "unknown"] = "unknown"
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


class ContextOverrides(Strict):
    mobility: (
        Literal[
            "independent",
            "walking_aid",
            "wheelchair",
            "assistance_required",
            "unknown",
            "needs_time",
            "requires_help",
        ]
        | None
    ) = None
    stairs: Literal["able", "difficult", "unable", "unknown"] | None = None
    alone_now: Literal["yes", "no", "unknown"] = "unknown"


class ContextWrite(Strict):
    base_revision: int = Field(ge=0)
    observed_at: AwareDatetime
    confirmation: Literal["user_confirmed"]
    proposal_turn_id: Identifier | None = None
    overrides: ContextOverrides = Field(default_factory=ContextOverrides)
    state: StatePatch = Field(default_factory=StatePatch)


class ReceiptWrite(Strict):
    alert_revision: int = Field(ge=1)
    installation_id: Identifier
    event: Literal["received", "displayed", "opened"]
    occurred_at: AwareDatetime


class StoredInput(Strict):
    revision: int = Field(ge=1)
    data: dict
