from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from bonghwajigi.contracts.spatial import Box


class RoutePoint(BaseModel):
    model_config = ConfigDict(extra="forbid")
    latitude: float = Field(ge=-85, le=85, allow_inf_nan=False)
    longitude: float = Field(ge=-180, le=180, allow_inf_nan=False)


class RouteDestination(RoutePoint):
    name: str = Field(min_length=1, max_length=200)


class RouteGeometry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["LineString"] = "LineString"
    coordinates: list[tuple[float, float]] = Field(min_length=2, max_length=100)

    @model_validator(mode="after")
    def valid_points(self):
        for longitude, latitude in self.coordinates:
            RoutePoint(latitude=latitude, longitude=longitude)
        return self


class RouteStep(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sequence: int = Field(ge=1, le=100)
    text: str = Field(min_length=1, max_length=500)
    point: RoutePoint


class ReferenceRoute(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(min_length=1, max_length=128)
    origin: Literal["synthetic", "historical_replay"] = "synthetic"
    operational_use: Literal[False] = False
    label: str = Field(min_length=1, max_length=200)
    geometry: RouteGeometry
    start: RouteDestination
    destination: RouteDestination
    steps: list[RouteStep] = Field(min_length=1, max_length=100)
    bounds: Box

    @model_validator(mode="after")
    def consistent_geometry(self):
        if self.geometry.coordinates[0] != (self.start.longitude, self.start.latitude):
            raise ValueError("참고 경로 시작 좌표가 일치해야 합니다.")
        if self.geometry.coordinates[-1] != (self.destination.longitude, self.destination.latitude):
            raise ValueError("참고 경로 목적지 좌표가 일치해야 합니다.")
        for longitude, latitude in self.geometry.coordinates + [
            (step.point.longitude, step.point.latitude) for step in self.steps
        ]:
            if not (
                self.bounds.west <= longitude <= self.bounds.east
                and self.bounds.south <= latitude <= self.bounds.north
            ):
                raise ValueError("경로 좌표는 표시 범위 안에 있어야 합니다.")
        if [step.sequence for step in self.steps] != list(range(1, len(self.steps) + 1)):
            raise ValueError("경로 단계의 순서가 올바르지 않습니다.")
        return self
