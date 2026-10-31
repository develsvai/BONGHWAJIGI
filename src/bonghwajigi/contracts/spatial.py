from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator


class Box(BaseModel):
    model_config = ConfigDict(extra="forbid")
    west: float = Field(ge=-180, le=180, allow_inf_nan=False)
    south: float = Field(ge=-85, le=85, allow_inf_nan=False)
    east: float = Field(ge=-180, le=180, allow_inf_nan=False)
    north: float = Field(ge=-85, le=85, allow_inf_nan=False)

    @model_validator(mode="after")
    def check(self):
        if self.west >= self.east or self.south >= self.north:
            raise ValueError("경도 경계를 넘지 않는 유효한 사각 구역이 필요합니다.")
        return self


class PolicyContext(BaseModel):
    model_config = ConfigDict(extra="forbid")
    incident_id: str = Field(min_length=1, max_length=128, pattern=r"^[a-zA-Z0-9_.:-]+$")
    incident_revision: int = Field(ge=1)
    expires_at: AwareDatetime
    area: Box | None = None
