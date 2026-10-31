from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException

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
    app.include_router(health_router("api", ("database", "broker", "application")))
    if app.state.settings.analysis_enabled:
        from bonghwajigi.api.analysis import attach_analysis

        attach_analysis(app, app.state.settings)
        return app

    @app.post(
        "/internal/v1/scenario-events",
        status_code=503,
        dependencies=[Depends(service_auth(app.state.settings))],
    )
    def receive_scenario(body: ScenarioEvent) -> None:
        # A3에서 DB 트랜잭션·outbox·분리 큐로 연결한다. 수락을 가장하지 않는다.
        raise HTTPException(status_code=503, detail="SCENARIO_INGESTION_NOT_READY")

    return app
