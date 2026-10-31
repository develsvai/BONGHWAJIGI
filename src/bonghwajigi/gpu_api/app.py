from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Response
from starlette.concurrency import run_in_threadpool

from bonghwajigi.common.config import Settings
from bonghwajigi.common.health import HealthReport
from bonghwajigi.common.security import service_auth
from bonghwajigi.contracts.models import EmbedRequest, GenerateRequest


def create_app() -> FastAPI:
    settings = Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if settings.gpu_enabled:
            if not settings.service_token or not settings.service_token.get_secret_value():
                raise RuntimeError("GPU 활성화 시 서비스 인증 토큰이 필요합니다.")
            from bonghwajigi.gpu_api.runtime import ModelRuntime

            app.state.runtime = await run_in_threadpool(ModelRuntime, settings)
        try:
            yield
        finally:
            if app.state.runtime:
                await run_in_threadpool(app.state.runtime.close)

    app = FastAPI(title="봉화지기 GPU 서버", version="0.1.0", lifespan=lifespan)
    app.state.settings, app.state.runtime = settings, None
    require_service_token = service_auth(settings)

    @app.get("/health/live")
    def live() -> HealthReport:
        return HealthReport(service="gpu_api", status="alive", checks={"process": "alive"})

    @app.get("/health/ready")
    def ready(response: Response) -> dict:
        if app.state.runtime is None:
            response.status_code = 503
            return {"service": "gpu_api", "status": "not_ready", "stage": "model_runtime"}
        return {
            "service": "gpu_api",
            "status": "ready",
            "stage": "model_runtime",
            "models": {
                "generation": settings.qwen_revision,
                "embedding": settings.embedding_revision,
            },
        }

    def invoke(operation: str, body):
        from bonghwajigi.gpu_api.runtime import ModelBusyError

        runtime = app.state.runtime
        if runtime is None:
            reason = (
                "GENERATION_MODEL_NOT_READY"
                if operation == "generate"
                else "EMBEDDING_MODEL_NOT_READY"
            )
            raise HTTPException(status_code=503, detail=reason)
        try:
            return getattr(runtime, operation)(body)
        except ValueError:
            raise HTTPException(status_code=422, detail="TOKEN_BUDGET_EXCEEDED") from None
        except ModelBusyError:
            raise HTTPException(
                status_code=503, detail="MODEL_BUSY", headers={"Retry-After": "2"}
            ) from None
        except RuntimeError:
            raise HTTPException(status_code=503, detail="MODEL_EXECUTION_FAILED") from None

    @app.post("/internal/v1/generate", dependencies=[Depends(require_service_token)])
    def generate(body: GenerateRequest) -> dict:
        return invoke("generate", body)

    @app.post("/internal/v1/embeddings", dependencies=[Depends(require_service_token)])
    def embed(body: EmbedRequest) -> dict:
        return invoke("embed", body)

    return app
