from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class HealthReport(BaseModel):
    service: str
    status: str
    stage: str = "scaffold"
    checks: dict[str, str]


def health_router(service: str, pending: tuple[str, ...], ready_check=None) -> APIRouter:
    router = APIRouter(prefix="/health", tags=["health"])

    @router.get("/live", response_model=HealthReport)
    def live() -> HealthReport:
        return HealthReport(service=service, status="alive", checks={"process": "alive"})

    @router.get(
        "/ready",
        response_model=HealthReport,
        status_code=200 if ready_check else 503,
        responses={503: {"model": HealthReport, "description": "기반 서비스 준비 안 됨"}},
    )
    def ready() -> HealthReport:
        if ready_check is not None:
            try:
                checks = ready_check()
                return JSONResponse(
                    status_code=200,
                    content={
                        "service": service,
                        "status": "ready",
                        "stage": "mvp_simulation",
                        "checks": checks,
                    },
                )
            except Exception:
                return JSONResponse(
                    status_code=503,
                    content={
                        "service": service,
                        "status": "not_ready",
                        "stage": "mvp_simulation",
                        "checks": {"infrastructure": "unavailable"},
                    },
                )
        # 설정 유무나 포트 응답만으로 미구현 서비스를 준비 완료로 표시하지 않는다.
        return HealthReport(
            service=service,
            status="not_ready",
            checks=dict.fromkeys(pending, "not_implemented"),
        )

    return router
