from datetime import timedelta

from sqlalchemy import select

from bonghwajigi.db.analysis_models import AnalysisJob, new_id, now
from bonghwajigi.db.policy_models import PolicyEntity, PolicyIntegration
from bonghwajigi.integration.service import (
    GenerationClient,
    IntegrationError,
    make_prompt,
    prepare_evidence,
    validate_model_output,
)
from bonghwajigi.policy.service import enqueue, scope_lock


def integrate_once(sessions, generator):
    token, claimed = new_id(), None
    with sessions.begin() as session:
        rows = session.execute(
            select(PolicyIntegration, AnalysisJob)
            .join(
                AnalysisJob,
                AnalysisJob.id == PolicyIntegration.job_id,
            )
            .where(
                PolicyIntegration.status.in_(["waiting_retrieval", "retry", "processing"]),
                PolicyIntegration.next_attempt_at <= now(),
                AnalysisJob.status.in_(["ready_for_qwen", "failed"]),
            )
            .order_by(PolicyIntegration.next_attempt_at)
            .limit(10)
            .with_for_update(skip_locked=True, of=PolicyIntegration)
        ).all()
        for task, job in rows:
            incident = session.get(PolicyEntity, (task.scenario_id, "incident", task.incident_id))
            if not incident or incident.revision != task.incident_revision:
                task.status = "superseded"
                continue
            if job.status == "failed" or task.attempts >= 3:
                task.status, task.error_code = "failed", "RETRIEVAL_OR_INTEGRATION_FAILED"
                enqueue(session, task.scenario_id, incident_id=task.incident_id)
                continue
            task.status, task.lease_id = "processing", token
            task.attempts += 1
            task.next_attempt_at = now() + timedelta(seconds=180)
            claimed = (task.job_id, job.result, job.body["origin"], incident.body["title"])
            break
    if claimed is None:
        return False
    job_id, handoff, origin, title = claimed
    generation, result, prompt, error = None, None, None, None
    try:
        event = handoff["event"]
        scenario = {
            "scenario_id": handoff["scenario_id"],
            "official_alerts": [],
            "documents": [
                {
                    "scenario_id": handoff["scenario_id"],
                    "document_id": "observation-source",
                    "text": event["text"],
                    "source": event["source"],
                    "origin": origin,
                    "source_kind": "observation",
                }
            ],
        }
        sources, alerts = prepare_evidence(handoff, scenario, require_alerts=False)
        prompt = make_prompt(sources, alerts, title)
        generation = generator.generate(prompt)
        result = {**validate_model_output(generation["text"], sources), "sources": sources}
    except IntegrationError as exc:
        error = str(exc)[:80]
    except Exception:
        error = "INTEGRATION_EXECUTION_FAILED"
    with sessions.begin() as session:
        reference = session.get(PolicyIntegration, job_id)
        scope_lock(session, reference.scenario_id)
        task = session.scalar(
            select(PolicyIntegration)
            .where(
                PolicyIntegration.job_id == job_id,
            )
            .with_for_update()
        )
        if task.lease_id != token:
            return True
        incident = session.get(PolicyEntity, (task.scenario_id, "incident", task.incident_id))
        task.prompt, task.raw_generation = prompt, generation
        if incident.revision != task.incident_revision:
            task.status = "superseded"
        elif result is not None:
            task.status, task.result, task.error_code = "complete", result, None
        else:
            task.error_code = error
            task.status = "failed" if task.attempts >= 3 else "retry"
            task.next_attempt_at = now() + timedelta(seconds=10 * task.attempts)
        enqueue(session, task.scenario_id, incident_id=task.incident_id)
    return True


class ConfiguredGenerator:
    def __init__(self, settings):
        self.settings = settings

    def generate(self, prompt):
        settings = self.settings
        if not settings.qwen_revision or not settings.embedding_service_token:
            raise IntegrationError("GENERATION_NOT_CONFIGURED")
        client = GenerationClient(
            settings.gpu_base_url,
            settings.embedding_service_token,
            settings.qwen_model,
            settings.qwen_revision,
        )
        try:
            return client.generate(prompt)
        finally:
            client.close()
