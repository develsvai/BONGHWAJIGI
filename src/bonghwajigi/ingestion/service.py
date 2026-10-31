import hashlib
import json

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from bonghwajigi.contracts.analysis import AcceptedJob
from bonghwajigi.db.analysis_models import AnalysisJob, AnalysisOutbox, new_id, now


class IngestionConflict(ValueError):
    pass


def accept_job(session, kind: str, scenario_id: str, external_id: str, body: dict) -> AcceptedJob:
    fingerprint = hashlib.sha256(
        json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
    ).hexdigest()
    job_id = session.execute(
        insert(AnalysisJob)
        .values(
            id=new_id(),
            kind=kind,
            scenario_id=scenario_id,
            external_id=external_id,
            body_hash=fingerprint,
            body=body,
            status="queued",
            attempts=0,
            created_at=now(),
            updated_at=now(),
        )
        .on_conflict_do_nothing(index_elements=["scenario_id", "kind", "external_id"])
        .returning(AnalysisJob.id)
    ).scalar_one_or_none()
    duplicate = job_id is None
    if duplicate:
        job = session.scalar(
            select(AnalysisJob).where(
                AnalysisJob.scenario_id == scenario_id,
                AnalysisJob.kind == kind,
                AnalysisJob.external_id == external_id,
            )
        )
        if job.body_hash != fingerprint:
            raise IngestionConflict("IDEMPOTENCY_CONFLICT")
    else:
        session.add(AnalysisOutbox(job_id=job_id))
        session.flush()
        job = session.get(AnalysisJob, job_id)
    return AcceptedJob(
        job_id=job.id, scenario_id=scenario_id, status=job.status, duplicate=duplicate
    )
