import copy
import math
from datetime import datetime, timedelta

from sqlalchemy import and_, or_, select
from sqlalchemy.dialects.postgresql import insert

from bonghwajigi.contracts.analysis import AnalysisInput
from bonghwajigi.contracts.policy import IncidentInput
from bonghwajigi.db.analysis_models import now
from bonghwajigi.db.policy_models import (
    PolicyEntity,
    PolicyIntegration,
    PolicyProjection,
    PolicyScope,
    PolicySnapshot,
)
from bonghwajigi.ingestion.service import IngestionConflict
from bonghwajigi.integration.service import digest


def scope_lock(session, scenario):
    session.execute(insert(PolicyScope).values(scenario_id=scenario).on_conflict_do_nothing())
    return session.scalar(
        select(PolicyScope).where(PolicyScope.scenario_id == scenario).with_for_update()
    )


def evaluation_time(scope, wall_time=None):
    return scope.evaluation_at or wall_time or now()


def enqueue(session, scenario, user_id=None, incident_id=None):
    users = session.scalars(
        select(PolicyEntity.entity_id)
        .where(
            PolicyEntity.scenario_id == scenario,
            PolicyEntity.kind == "profile",
            *([PolicyEntity.entity_id == user_id] if user_id else []),
        )
        .order_by(PolicyEntity.entity_id)
    ).all()
    incidents = session.scalars(
        select(PolicyEntity.entity_id)
        .where(
            PolicyEntity.scenario_id == scenario,
            PolicyEntity.kind == "incident",
            *([PolicyEntity.entity_id == incident_id] if incident_id else []),
        )
        .order_by(PolicyEntity.entity_id)
    ).all()
    for user in users:
        for incident in incidents:
            session.execute(
                insert(PolicyProjection)
                .values(
                    scenario_id=scenario,
                    user_id=user,
                    incident_id=incident,
                )
                .on_conflict_do_update(
                    index_elements=["scenario_id", "user_id", "incident_id"],
                    set_={"requested": PolicyProjection.requested + 1, "error_code": None},
                )
            )


def put_entity(session, scenario, kind, key, payload, *, user_id=None, incident_id=None):
    scope = scope_lock(session, scenario)
    body = payload.model_dump(mode="json")
    fingerprint = digest(body)
    current = session.get(PolicyEntity, (scenario, kind, key))
    if current and payload.revision <= current.revision:
        if payload.revision == current.revision and current.body_hash == fingerprint:
            return {"revision": current.revision, "duplicate": True}
        raise IngestionConflict("REVISION_CONFLICT")
    moment = evaluation_time(scope)
    observed = getattr(payload, "observed_at", getattr(payload, "issued_at", None))
    if observed and observed > moment:
        raise ValueError("FUTURE_INPUT")
    if current:
        current.revision, current.body, current.body_hash = payload.revision, body, fingerprint
    else:
        session.add(
            PolicyEntity(
                scenario_id=scenario,
                kind=kind,
                entity_id=key,
                revision=payload.revision,
                body=body,
                body_hash=fingerprint,
            )
        )
    session.flush()
    enqueue(session, scenario, user_id, incident_id)
    return {"revision": payload.revision, "duplicate": False}


def put_clock(session, scenario, payload):
    scope = scope_lock(session, scenario)
    if payload.revision <= scope.clock_revision:
        if (
            payload.revision == scope.clock_revision
            and payload.evaluation_at == scope.evaluation_at
        ):
            return {"revision": scope.clock_revision, "duplicate": True}
        raise IngestionConflict("REVISION_CONFLICT")
    if (
        scope.clock_revision > 0
        and payload.evaluation_at
        and payload.evaluation_at < evaluation_time(scope)
    ):
        raise ValueError("CLOCK_CANNOT_MOVE_BACKWARD")
    scope.clock_revision, scope.evaluation_at = payload.revision, payload.evaluation_at
    enqueue(session, scenario)
    return {"revision": payload.revision, "duplicate": False}


def register_observation(session, job_id, event):
    payload = AnalysisInput.model_validate(event["payload"])
    context = payload.policy_context
    if context is None:
        return
    scope_lock(session, event["scenario_id"])
    existing = session.scalar(
        select(PolicyIntegration).where(
            PolicyIntegration.scenario_id == event["scenario_id"],
            PolicyIntegration.incident_id == context.incident_id,
            PolicyIntegration.incident_revision == context.incident_revision,
        )
    )
    if existing and existing.job_id != job_id:
        raise IngestionConflict("INCIDENT_REVISION_ALREADY_ASSIGNED")
    incident = IncidentInput(
        revision=context.incident_revision,
        origin=event["origin"],
        title=payload.source.title,
        observed_at=payload.as_of,
        expires_at=context.expires_at,
        area=context.area,
        sources=[payload.source],
    )
    put_entity(
        session,
        event["scenario_id"],
        "incident",
        context.incident_id,
        incident,
        incident_id=context.incident_id,
    )
    session.execute(
        insert(PolicyIntegration)
        .values(
            job_id=job_id,
            scenario_id=event["scenario_id"],
            incident_id=context.incident_id,
            incident_revision=context.incident_revision,
        )
        .on_conflict_do_nothing()
    )


def at(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def fresh(body, moment, start="observed_at"):
    return bool(body and at(body[start]) <= moment < at(body["expires_at"]))


def relevance(location, area, moment):
    if not location:
        return "unknown", "LOCATION_MISSING"
    if not fresh(location, moment):
        return "unknown", "LOCATION_EXPIRED_OR_FUTURE"
    if not area:
        return "unknown", "AREA_MISSING"
    # GPS 오차의 보수적 외접 사각형을 사용한다. 경계에 걸리면 확정 판정을 보류한다.
    latitude, longitude = location["latitude"], location["longitude"]
    dy = location["accuracy_m"] / 110000
    dx = dy / max(math.cos(math.radians(min(abs(latitude) + dy, 89.9))), 0.001)
    if longitude - dx < -180 or longitude + dx > 180:
        return "uncertain", "LOCATION_DATELINE_UNSUPPORTED"
    if (
        longitude + dx < area["west"]
        or longitude - dx > area["east"]
        or latitude + dy < area["south"]
        or latitude - dy > area["north"]
    ):
        return "outside", "LOCATION_OUTSIDE_AREA"
    if (
        longitude - dx >= area["west"]
        and longitude + dx <= area["east"]
        and latitude - dy >= area["south"]
        and latitude + dy <= area["north"]
    ):
        return "inside", "LOCATION_INSIDE_AREA"
    return "uncertain", "LOCATION_ACCURACY_OVERLAPS_BOUNDARY"


def evaluate(session, projection, moment):
    entities = session.scalars(
        select(PolicyEntity).where(
            PolicyEntity.scenario_id == projection.scenario_id,
        )
    ).all()
    lookup = {(entity.kind, entity.entity_id): entity for entity in entities}

    def entity(kind, key):
        return lookup.get((kind, key))

    def body(kind, key):
        row = entity(kind, key)
        return row.body if row else None

    user, incident_id = projection.user_id, projection.incident_id
    profile = body("profile", user) or {}
    location, incident = body("location", user), body("incident", incident_id)
    rules, prediction = body("rules", "active"), body("prediction", incident_id)
    relation, relation_reason = relevance(location, incident["area"], moment)
    incident_fresh = fresh(incident, moment)
    reasons = ["RESPONSE_LEVEL_CONFIGURATION_PENDING", relation_reason]
    if not incident_fresh:
        reasons.append("INCIDENT_EXPIRED_OR_FUTURE")
    if not rules or rules["review_state"] == "draft":
        reasons.append("POLICY_REVIEW_PENDING")

    # 공식 기록은 모델의 결과와 독립적으로 보존한다. 만료를 해제나 안전으로 해석하지 않는다.
    alerts = []
    selected = [
        entity("profile", user),
        entity("location", user),
        entity("incident", incident_id),
        entity("rules", "active"),
        entity("prediction", incident_id),
    ]
    for row in entities:
        if row.kind != "alert" or not row.entity_id.startswith(incident_id + "/"):
            continue
        selected.append(row)
        notice = row.body
        alert_relation, _ = relevance(location, notice["area"], moment)
        active = (
            notice["state"] == "issued"
            and notice["validity_confirmed"]
            and fresh(notice, moment, "issued_at")
            and notice["source"]["verified"]
            and at(notice["source"]["published_at"]) <= moment
        )
        alerts.append(
            {
                "alert_id": row.entity_id.split("/", 1)[1],
                **notice,
                "record_status": "active_record"
                if active
                else ("cancelled" if notice["state"] == "cancelled" else "unconfirmed_or_expired"),
                "user_relevance": alert_relation,
                "requires_qwen": False,
            }
        )

    related = relation == "inside" and incident_fresh
    conditions = {
        "related": related,
        "mobility_assistance": related and profile.get("mobility_assistance", False),
        "children_accompanying": related and profile.get("children_accompanying", False),
    }
    actions = []
    if rules and rules["review_state"] == "simulation_only":
        for rule in rules["rules"]:
            guide = entity("guidance", rule["guidance_id"])
            if guide:
                selected.append(guide)
            usable = (
                guide
                and guide.body["review_state"] == "simulation_only"
                and fresh(guide.body, moment, "valid_from")
                and at(guide.body["source"]["published_at"]) <= moment
            )
            if not usable:
                reasons.append("GUIDANCE_MISSING_UNREVIEWED_OR_EXPIRED")
            if usable and conditions[rule["when"]]:
                actions.append(
                    {
                        "action_id": rule["action_id"],
                        "text": guide.body["text"],
                        "priority": rule["priority"],
                        "reason_code": rule["when"],
                        "guidance_id": guide.entity_id,
                        "guidance_revision": guide.revision,
                        "source": guide.body["source"],
                        "approved_policy": False,
                    }
                )
    actions.sort(key=lambda action: (action["priority"], action["action_id"]))
    prediction_state = "unavailable"
    probability = None
    if prediction and fresh(prediction, moment):
        pred_relation, _ = relevance(location, prediction["area"], moment)
        if prediction["status"] == "simulation" and pred_relation == "inside":
            prediction_state, probability = "simulation", prediction["probability"]
    if probability is None:
        reasons.append("PREDICTION_UNAVAILABLE_FOR_USER")

    integration = session.scalar(
        select(PolicyIntegration).where(
            PolicyIntegration.scenario_id == projection.scenario_id,
            PolicyIntegration.incident_id == incident_id,
            PolicyIntegration.incident_revision == incident["revision"],
        )
    )
    context = {
        "status": integration.status if integration else "not_requested",
        "summary": integration.result["summary"] if integration and integration.result else None,
        "facts": integration.result["facts"] if integration and integration.result else [],
        "sources": integration.result["sources"] if integration and integration.result else [],
        "summary_review_status": "not_reviewed",
        "error_code": integration.error_code if integration else None,
        "template_fallback": not (integration and integration.result),
    }
    versions = {f"{row.kind}:{row.entity_id}": row.revision for row in selected if row}
    deadlines = []
    for row in selected:
        if not row:
            continue
        for field in ("expires_at", "valid_from"):
            value = row.body.get(field)
            if value and at(value) > moment:
                deadlines.append(value)
    return {
        "mode": "simulation",
        "operational_use": False,
        "disaster_type": "wildfire",
        "user_id": user,
        "incident_id": incident_id,
        "incident": {
            key: incident[key]
            for key in (
                "title",
                "origin",
                "observed_at",
                "expires_at",
                "area",
                "sources",
            )
        },
        "state": "outside_scope"
        if relation == "outside"
        else (
            "needs_refresh"
            if not incident_fresh or relation in {"unknown", "uncertain"}
            else "simulation_preview"
        ),
        "relevance": {"status": relation, "reason_code": relation_reason},
        "personal_response": {
            "level": "unknown",
            "label": "대응 단계 결정 대기",
            "policy_version": rules["revision"] if rules else None,
            "reason_codes": sorted(set(reasons)),
        },
        "actions": actions,
        "official_alerts": sorted(alerts, key=lambda item: item["alert_id"]),
        "prediction": {
            "status": prediction_state,
            "probability": probability,
            "target": prediction["target"] if prediction else None,
            "model_id": prediction["model_id"] if prediction else None,
            "model_revision": prediction["model_revision"] if prediction else None,
            "operational_use": False,
            "used_for_response_level": False,
        },
        "context": context,
        "input_versions": versions,
        "valid_until": min(deadlines, key=at) if deadlines else None,
        "notification": {"status": "configuration_pending", "dispatched": False},
    }


def evaluate_once(sessions, check_seconds=30, wall_time=None):
    wall_time = wall_time or now()
    changed = 0
    with sessions.begin() as session:
        rows = session.scalars(
            select(PolicyProjection)
            .where(
                or_(
                    and_(
                        PolicyProjection.requested > PolicyProjection.applied,
                        PolicyProjection.error_code.is_(None),
                    ),
                    PolicyProjection.next_check_at <= wall_time,
                )
            )
            .order_by(PolicyProjection.next_check_at)
            .limit(50)
            .with_for_update(skip_locked=True)
        ).all()
        for row in rows:
            moment = evaluation_time(session.get(PolicyScope, row.scenario_id), wall_time)
            try:
                with session.begin_nested():
                    content = evaluate(session, row, moment)
                    fingerprint = digest(content)
                    if fingerprint != row.content_hash:
                        row.revision += 1
                        row.content, row.content_hash = content, fingerprint
                        session.add(
                            PolicySnapshot(
                                projection_id=row.id,
                                revision=row.revision,
                                evaluated_at=moment,
                                content=content,
                            )
                        )
                        changed += 1
                    row.applied, row.evaluated_at, row.error_code = row.requested, moment, None
                    row.next_check_at = wall_time + timedelta(seconds=check_seconds)
            except Exception:
                row.error_code = "POLICY_EVALUATION_FAILED"
                row.next_check_at = wall_time + timedelta(seconds=check_seconds)
    return changed


def projection_view(session, row):
    content = copy.deepcopy(row.content)
    moment = evaluation_time(session.get(PolicyScope, row.scenario_id))
    expired = bool(content and content["valid_until"] and at(content["valid_until"]) <= moment)
    pending = row.requested > row.applied
    if content and (expired or pending or row.error_code):
        content["actions"] = []
        content["state"] = "needs_refresh" if expired else "pending_update"
        content["prediction"]["status"], content["prediction"]["probability"] = "unavailable", None
        for alert in content["official_alerts"]:
            if pending:
                alert["user_relevance"] = "unknown"
            if alert["state"] == "issued" and not fresh(alert, moment, "issued_at"):
                alert["record_status"] = "unconfirmed_or_expired"
    return {
        "scenario_id": row.scenario_id,
        "revision": row.revision,
        "evaluated_at": row.evaluated_at,
        "pending_update": pending or expired or bool(row.error_code),
        "error_code": row.error_code,
        "content": content,
    }
