from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from bonghwajigi.common.config import Settings
from bonghwajigi.common.health import health_router
from bonghwajigi.common.security import service_auth
from bonghwajigi.contracts.scenarios import ScenarioEvent


def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(app):
        try:
            yield
        finally:
            if hasattr(app.state, "sessions"):
                app.state.sessions.kw["bind"].dispose()

    app = FastAPI(title="봉화지기 일반 서버", version="0.1.0", lifespan=lifespan)
    app.state.settings = Settings()

    @app.exception_handler(RequestValidationError)
    async def invalid_input(request, exc):
        # FastAPI 기본 오류에 요청 값(선택 의료 메모·토큰)이 포함되지 않게 한다.
        return JSONResponse(
            status_code=422,
            content={
                "detail": [
                    {
                        "loc": list(error["loc"]),
                        "msg": "입력 값을 확인해 주세요.",
                        "type": error["type"],
                    }
                    for error in exc.errors()
                ]
            },
        )

    if app.state.settings.app_cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=app.state.settings.app_cors_origins,
            allow_methods=["GET", "POST", "PUT", "DELETE"],
            allow_headers=["Authorization", "Content-Type", "Idempotency-Key"],
        )

    def ready_check():
        from redis import Redis
        from sqlalchemy import text

        with app.state.sessions() as session:
            session.execute(text("SELECT 1 FROM app_accounts LIMIT 1"))
            session.execute(text("SELECT 1 FROM deliveries LIMIT 1"))
            session.execute(text("SELECT 1 FROM app_text_turns LIMIT 1"))
        with Redis.from_url(
            app.state.settings.broker_url.get_secret_value(),
            socket_connect_timeout=2,
            socket_timeout=2,
        ) as broker:
            broker.ping()
        return {
            "database": "connected",
            "broker": "connected",
            "application": "simulation_ready",
            "prediction": "excluded",
            "gpu": "optional_not_in_readiness",
        }

    app.include_router(
        health_router(
            "api",
            ("database", "broker", "application"),
            ready_check if app.state.settings.app_enabled else None,
        )
    )
    if app.state.settings.analysis_enabled:
        from bonghwajigi.api.analysis import attach_analysis

        attach_analysis(app, app.state.settings)
        if app.state.settings.policy_enabled:
            from bonghwajigi.api.policy import attach_policy

            attach_policy(app, app.state.settings)
        if app.state.settings.app_enabled:
            app.version = "0.2.0-mvp"
            if not app.state.settings.policy_enabled:
                raise RuntimeError("앱 API에는 개인별 정책 루프가 필요합니다.")
            from bonghwajigi.api.mobile import attach_mobile

            attach_mobile(app, app.state.settings)
        return app

    if app.state.settings.policy_enabled:
        raise RuntimeError("정책 루프에는 분석 수신 경로를 활성화해야 합니다.")
    if app.state.settings.app_enabled:
        raise RuntimeError("앱 API에는 분석·정책 루프가 필요합니다.")

    @app.post(
        "/internal/v1/scenario-events",
        status_code=503,
        dependencies=[Depends(service_auth(app.state.settings))],
    )
    def receive_scenario(body: ScenarioEvent) -> None:
        # A3에서 DB 트랜잭션·outbox·분리 큐로 연결한다. 수락을 가장하지 않는다.
        raise HTTPException(status_code=503, detail="SCENARIO_INGESTION_NOT_READY")

    return app
