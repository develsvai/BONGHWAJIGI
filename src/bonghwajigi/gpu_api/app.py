from fastapi import Depends, FastAPI, HTTPException

from bonghwajigi.common.config import Settings
from bonghwajigi.common.health import health_router
from bonghwajigi.common.security import service_auth
from bonghwajigi.contracts.models import EmbedRequest, GenerateRequest


def create_app() -> FastAPI:
    settings = Settings()
    app = FastAPI(title="봉화지기 GPU 서버 · scaffold", version="0.1.0")
    app.state.settings = settings
    app.include_router(health_router("gpu_api", ("generation_model", "embedding_model")))
    require_service_token = service_auth(settings)

    @app.post(
        "/internal/v1/generate", status_code=503, dependencies=[Depends(require_service_token)]
    )
    def generate(body: GenerateRequest) -> None:
        raise HTTPException(status_code=503, detail="GENERATION_MODEL_NOT_READY")

    @app.post(
        "/internal/v1/embeddings", status_code=503, dependencies=[Depends(require_service_token)]
    )
    def embed(body: EmbedRequest) -> None:
        raise HTTPException(status_code=503, detail="EMBEDDING_MODEL_NOT_READY")

    return app
