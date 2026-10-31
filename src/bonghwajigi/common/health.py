from fastapi import APIRouter
from pydantic import BaseModel


class HealthReport(BaseModel):
    service: str
    status: str
    stage: str = "scaffold"
    checks: dict[str, str]


def health_router(service: str, pending: tuple[str, ...]) -> APIRouter:
    router = APIRouter(prefix="/health", tags=["health"])

    @router.get("/live", response_model=HealthReport)
    def live() -> HealthReport:
        return HealthReport(service=service, status="alive", checks={"process": "alive"})

    @router.get("/ready", response_model=HealthReport, status_code=503)
    def ready() -> HealthReport:
        # 설정 유무나 포트 응답만으로 미구현 서비스를 준비 완료로 표시하지 않는다.
        return HealthReport(
            service=service,
            status="not_ready",
            checks=dict.fromkeys(pending, "not_implemented"),
        )

    return router
