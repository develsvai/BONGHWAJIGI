from fastapi import APIRouter, Depends, HTTPException
from pydantic import ValidationError
from redis import Redis
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError

from bonghwajigi.common.security import service_auth
from bonghwajigi.contracts.analysis import AcceptedJob, AnalysisInput, RetrievalDocument
from bonghwajigi.contracts.scenarios import ScenarioEvent
from bonghwajigi.db.analysis_models import AnalysisJob, AnalysisOutbox, now
from bonghwajigi.db.session import session_factory
from bonghwajigi.ingestion.service import IngestionConflict, accept_job


def attach_analysis(app, settings):
    if not settings.service_token or not settings.broker_url:
        raise RuntimeError("분석 흐름에는 내부 인증·DB·브로커 설정이 필요합니다.")
    sessions = session_factory(settings)
    app.state.sessions = sessions
    router = APIRouter(dependencies=[Depends(service_auth(settings))], tags=["analysis"])

    def accept(kind, scenario_id, external_id, body):
        try:
            with sessions.begin() as session:
                accepted = accept_job(session, kind, scenario_id, external_id, body)
                if kind == "analysis" and settings.policy_enabled and not accepted.duplicate:
                    from bonghwajigi.policy.service import register_observation

                    register_observation(session, accepted.job_id, body)
                return accepted
        except IngestionConflict:
            raise HTTPException(409, detail="IDEMPOTENCY_CONFLICT") from None
        except ValueError:
            raise HTTPException(422, detail="INVALID_POLICY_OBSERVATION") from None
        except SQLAlchemyError:
            raise HTTPException(503, detail="DATABASE_UNAVAILABLE") from None

    @router.post("/internal/v1/scenario-events", status_code=202, response_model=AcceptedJob)
    def receive_event(body: ScenarioEvent):
        if body.queue != "analysis":
            raise HTTPException(503, detail="URGENT_INGESTION_NOT_IMPLEMENTED")
        try:
            payload = AnalysisInput.model_validate(body.payload)
        except ValidationError:
            raise HTTPException(422, detail="INVALID_ANALYSIS_PAYLOAD") from None
        normalized = body.model_dump(mode="json")
        normalized["payload"] = payload.model_dump(mode="json")
        return accept("analysis", body.scenario_id, body.event_id, normalized)

    @router.post("/internal/v1/retrieval-documents", status_code=202, response_model=AcceptedJob)
    def receive_document(body: RetrievalDocument):
        return accept(
            "document",
            body.scenario_id,
            f"{body.document_id}:{body.revision}:{settings.embedding_revision}",
            body.model_dump(mode="json"),
        )

    @router.get("/internal/v1/scenarios/{scenario_id}/analysis-jobs/{job_id}")
    def get_job(scenario_id: str, job_id: str):
        with sessions() as session:
            job = session.scalar(
                select(AnalysisJob).where(
                    AnalysisJob.id == job_id,
                    AnalysisJob.scenario_id == scenario_id,
                )
            )
            if job is None:
                raise HTTPException(404, detail="NOT_FOUND")
            return {
                "job_id": job.id,
                "scenario_id": job.scenario_id,
                "mode": "simulation",
                "kind": job.kind,
                "status": job.status,
                "attempts": job.attempts,
                "error_code": job.error_code,
                "result": job.result,
            }

    @router.post("/internal/v1/scenarios/{scenario_id}/analysis-jobs/{job_id}/retry")
    def retry_job(scenario_id: str, job_id: str):
        with sessions.begin() as session:
            job = session.scalar(
                select(AnalysisJob)
                .where(
                    AnalysisJob.id == job_id,
                    AnalysisJob.scenario_id == scenario_id,
                )
                .with_for_update()
            )
            if job is None:
                raise HTTPException(404, detail="NOT_FOUND")
            if job.status != "failed":
                raise HTTPException(409, detail="JOB_NOT_FAILED")
            job.status, job.attempts, job.error_code = "queued", 0, None
            row = session.scalar(select(AnalysisOutbox).where(AnalysisOutbox.job_id == job.id))
            row.next_dispatch_at = now()
            return {"job_id": job.id, "status": "queued"}

    @router.get("/internal/v1/analysis-health")
    def health():
        try:
            with sessions() as session:
                session.execute(text("SELECT 1 FROM analysis_jobs LIMIT 1"))
            with Redis.from_url(
                settings.broker_url.get_secret_value(), socket_connect_timeout=3, socket_timeout=3
            ) as redis:
                redis.ping()
        except Exception:
            raise HTTPException(503, detail="ANALYSIS_INFRASTRUCTURE_UNAVAILABLE") from None
        return {
            "status": "ready",
            "database": "connected",
            "broker": "connected",
            "scope": "analysis_ingestion_only",
        }

    app.include_router(router)
