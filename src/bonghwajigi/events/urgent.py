from datetime import timedelta

from sqlalchemy import select

from bonghwajigi.contracts.policy import UrgentInput
from bonghwajigi.db.analysis_models import AnalysisJob, now
from bonghwajigi.db.delivery_models import Delivery
from bonghwajigi.db.policy_models import PolicyEntity
from bonghwajigi.ingestion.service import IngestionConflict
from bonghwajigi.notifications.service import emit_change
from bonghwajigi.policy.service import evaluation_time, fresh, put_entity, relevance, scope_lock


def process_urgent(sessions, job_id):
    with sessions.begin() as session:
        reference = session.get(AnalysisJob, job_id)
        if reference is None or reference.kind != "urgent":
            return False
        scope = scope_lock(session, reference.scenario_id)
        job = session.scalar(select(AnalysisJob).where(AnalysisJob.id == job_id).with_for_update())
        if job.status == "complete":
            return False
        job.attempts += 1
        try:
            with session.begin_nested():
                payload = UrgentInput.model_validate(job.body["payload"])
                current = session.get(
                    PolicyEntity, (job.scenario_id, "incident", payload.incident_id)
                )
                archived = bool(current and current.body.get("feed_visibility") == "archived")
                if not archived and (
                    current is None or current.revision < payload.incident.revision
                ):
                    put_entity(
                        session,
                        job.scenario_id,
                        "incident",
                        payload.incident_id,
                        payload.incident,
                        incident_id=payload.incident_id,
                    )
                result = put_entity(
                    session,
                    job.scenario_id,
                    "alert",
                    payload.incident_id + "/" + payload.alert_id,
                    payload.alert,
                    incident_id=payload.incident_id,
                )
                moment = evaluation_time(scope)
                matched = 0
                users = session.scalars(
                    select(PolicyEntity).where(
                        PolicyEntity.scenario_id == job.scenario_id,
                        PolicyEntity.kind == "profile",
                    )
                ).all()
                if not result["duplicate"]:
                    for user in users:
                        location = session.get(
                            PolicyEntity, (job.scenario_id, "location", user.entity_id)
                        )
                        notice = payload.alert.model_dump(mode="json")
                        relation, _ = relevance(
                            location.body if location else None, notice["area"], moment
                        )
                        active = (
                            notice["state"] == "issued"
                            and notice["validity_confirmed"]
                            and (
                                notice["source"]["verified"] and fresh(notice, moment, "issued_at")
                            )
                        )
                        # 취소도 별도 변경으로 보존한다. 원문 조회는 정책·모델과 독립적이다.
                        urgency = "high" if active and relation == "inside" else None
                        if notice["state"] == "cancelled" and notice["source"]["verified"]:
                            previously_targeted = session.scalar(
                                select(Delivery.id)
                                .where(
                                    Delivery.scenario_id == job.scenario_id,
                                    Delivery.user_id == user.entity_id,
                                    Delivery.resource_type == "alert",
                                    Delivery.resource_id
                                    == payload.incident_id + "/" + payload.alert_id,
                                )
                                .limit(1)
                            )
                            if previously_targeted or relation == "inside":
                                urgency = "normal"
                        # Preserve new original records without reactivating an archived fixture.
                        if archived or payload.incident.feed_visibility == "archived":
                            urgency = None
                        matched += int(urgency is not None)
                        emit_change(
                            session,
                            job.scenario_id,
                            user.entity_id,
                            "alert",
                            payload.incident_id + "/" + payload.alert_id,
                            payload.alert.revision,
                            urgency=urgency,
                            expires_at=now() + timedelta(minutes=10),
                        )
                job.result = {
                    "requires_qwen": False,
                    "matched_users": matched,
                    "duplicate": result["duplicate"],
                    "revision": payload.alert.revision,
                }
                job.status, job.error_code = "complete", None
        except IngestionConflict:
            job.status, job.error_code = "superseded", "REVISION_CONFLICT"
        except Exception:
            job.status = "failed" if job.attempts >= 5 else "retry"
            job.error_code = "URGENT_PROCESSING_FAILED"
        job.updated_at = now()
    return True
