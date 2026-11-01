from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from bonghwajigi.common.security import service_auth
from bonghwajigi.contracts.analysis import RegionalConditionsInput
from bonghwajigi.contracts.policy import (
    AlertInput,
    ClockInput,
    CurrentStateInput,
    EnvironmentInput,
    GuidanceInput,
    Identifier,
    IncidentInput,
    LocationInput,
    PredictionInput,
    ProfileInput,
    RouteInput,
    RuleSetInput,
)
from bonghwajigi.db.analysis_models import now
from bonghwajigi.db.policy_models import (
    PolicyEntity,
    PolicyIntegration,
    PolicyProjection,
    PolicySnapshot,
)
from bonghwajigi.ingestion.service import IngestionConflict
from bonghwajigi.policy.service import enqueue, projection_view, put_clock, put_entity, scope_lock


def attach_policy(app, settings):
    if settings.mode != "simulation":
        raise RuntimeError("개인별 정책 루프는 simulation에서만 활성화할 수 있습니다.")
    sessions = app.state.sessions
    router = APIRouter(
        prefix="/internal/v1/policy/scenarios/{scenario_id}",
        dependencies=[Depends(service_auth(settings))],
        tags=["policy-simulation"],
    )

    def mutate(operation):
        try:
            with sessions.begin() as session:
                return {"mode": "simulation", **operation(session)}
        except IngestionConflict:
            raise HTTPException(409, detail="REVISION_CONFLICT") from None
        except ValueError:
            raise HTTPException(422, detail="INVALID_TIME_OR_SCOPE") from None
        except SQLAlchemyError:
            raise HTTPException(503, detail="POLICY_DATABASE_UNAVAILABLE") from None

    @router.put("/clock", status_code=202)
    def clock(scenario_id: Identifier, body: ClockInput):
        return mutate(lambda session: put_clock(session, scenario_id, body))

    @router.put("/users/{user_id}/profile", status_code=202)
    def profile(scenario_id: Identifier, user_id: Identifier, body: ProfileInput):
        return mutate(
            lambda s: put_entity(s, scenario_id, "profile", user_id, body, user_id=user_id)
        )

    @router.put("/users/{user_id}/location", status_code=202)
    def location(scenario_id: Identifier, user_id: Identifier, body: LocationInput):
        return mutate(
            lambda s: put_entity(s, scenario_id, "location", user_id, body, user_id=user_id)
        )

    @router.put("/incidents/{incident_id}", status_code=202)
    def incident(scenario_id: Identifier, incident_id: Identifier, body: IncidentInput):
        return mutate(
            lambda s: put_entity(
                s,
                scenario_id,
                "incident",
                incident_id,
                body,
                incident_id=incident_id,
            )
        )

    @router.put("/incidents/{incident_id}/prediction", status_code=202)
    def prediction(scenario_id: Identifier, incident_id: Identifier, body: PredictionInput):
        return mutate(
            lambda s: put_entity(
                s,
                scenario_id,
                "prediction",
                incident_id,
                body,
                incident_id=incident_id,
            )
        )

    @router.put("/incidents/{incident_id}/alerts/{alert_id}", status_code=202)
    def alert(
        scenario_id: Identifier, incident_id: Identifier, alert_id: Identifier, body: AlertInput
    ):
        return mutate(
            lambda s: put_entity(
                s,
                scenario_id,
                "alert",
                incident_id + "/" + alert_id,
                body,
                incident_id=incident_id,
            )
        )

    @router.get("/incidents/{incident_id}/alerts")
    def alerts(scenario_id: Identifier, incident_id: Identifier):
        with sessions() as session:
            rows = session.scalars(
                select(PolicyEntity).where(
                    PolicyEntity.scenario_id == scenario_id,
                    PolicyEntity.kind == "alert",
                    PolicyEntity.entity_id.startswith(incident_id + "/", autoescape=True),
                )
            ).all()
            return {
                "mode": "simulation",
                "requires_qwen": False,
                "records": [row.body for row in rows],
            }

    @router.put("/guidance/{guidance_id}", status_code=202)
    def guidance(scenario_id: Identifier, guidance_id: Identifier, body: GuidanceInput):
        return mutate(lambda s: put_entity(s, scenario_id, "guidance", guidance_id, body))

    @router.put("/rules", status_code=202)
    def rules(scenario_id: Identifier, body: RuleSetInput):
        return mutate(lambda s: put_entity(s, scenario_id, "rules", "active", body))

    @router.put("/regional-conditions/{region_id}", status_code=202)
    def regional_conditions(
        scenario_id: Identifier, region_id: Identifier, body: RegionalConditionsInput
    ):
        if region_id != body.region_id:
            raise HTTPException(422, detail="REGION_ID_MISMATCH")
        return mutate(lambda s: put_entity(s, scenario_id, "regional_conditions", region_id, body))

    @router.post("/bootstrap-policy", status_code=202)
    def bootstrap_policy(scenario_id: Identifier):
        from bonghwajigi.policy.three_stage import bootstrap

        return mutate(lambda s: bootstrap(s, scenario_id, now()))

    @router.put("/incidents/{incident_id}/environment", status_code=202)
    def environment(scenario_id: Identifier, incident_id: Identifier, body: EnvironmentInput):
        return mutate(
            lambda s: put_entity(
                s, scenario_id, "environment", incident_id, body, incident_id=incident_id
            )
        )

    @router.put("/incidents/{incident_id}/users/{user_id}/state", status_code=202)
    def state(
        scenario_id: Identifier,
        incident_id: Identifier,
        user_id: Identifier,
        body: CurrentStateInput,
    ):
        return mutate(
            lambda s: put_entity(
                s,
                scenario_id,
                "state",
                incident_id + "/" + user_id,
                body,
                user_id=user_id,
                incident_id=incident_id,
            )
        )

    @router.put("/incidents/{incident_id}/users/{user_id}/route", status_code=202)
    def route(
        scenario_id: Identifier, incident_id: Identifier, user_id: Identifier, body: RouteInput
    ):
        return mutate(
            lambda s: put_entity(
                s,
                scenario_id,
                "route",
                incident_id + "/" + user_id,
                body,
                user_id=user_id,
                incident_id=incident_id,
            )
        )

    @router.get("/users/{user_id}/plans/{incident_id}")
    def plan(scenario_id: Identifier, user_id: Identifier, incident_id: Identifier):
        with sessions() as session:
            row = session.scalar(
                select(PolicyProjection).where(
                    PolicyProjection.scenario_id == scenario_id,
                    PolicyProjection.user_id == user_id,
                    PolicyProjection.incident_id == incident_id,
                )
            )
            if row is None:
                raise HTTPException(404, detail="NOT_FOUND")
            return projection_view(session, row)

    @router.get("/users/{user_id}/plans/{incident_id}/history")
    def history(
        scenario_id: Identifier,
        user_id: Identifier,
        incident_id: Identifier,
        after_revision: int = Query(default=0, ge=0),
    ):
        with sessions() as session:
            rows = session.scalars(
                select(PolicySnapshot)
                .join(
                    PolicyProjection,
                    PolicyProjection.id == PolicySnapshot.projection_id,
                )
                .where(
                    PolicyProjection.scenario_id == scenario_id,
                    PolicyProjection.user_id == user_id,
                    PolicyProjection.incident_id == incident_id,
                    PolicySnapshot.revision > after_revision,
                )
                .order_by(PolicySnapshot.revision)
                .limit(100)
            ).all()
            return {
                "mode": "simulation",
                "items": [
                    {
                        "revision": row.revision,
                        "evaluated_at": row.evaluated_at,
                        "content": row.content,
                    }
                    for row in rows
                ],
            }

    @router.get("/integrations/{job_id}")
    def integration(scenario_id: Identifier, job_id: str):
        with sessions() as session:
            row = session.get(PolicyIntegration, job_id)
            if row is None or row.scenario_id != scenario_id:
                raise HTTPException(404, detail="NOT_FOUND")
            return {
                "status": row.status,
                "attempts": row.attempts,
                "error_code": row.error_code,
                "result": row.result,
                "generation": row.raw_generation,
            }

    @router.post("/integrations/{job_id}/retry", status_code=202)
    def retry(scenario_id: Identifier, job_id: str):
        def operation(session):
            scope_lock(session, scenario_id)
            row = session.scalar(
                select(PolicyIntegration)
                .where(
                    PolicyIntegration.scenario_id == scenario_id,
                    PolicyIntegration.job_id == job_id,
                )
                .with_for_update()
            )
            if row is None:
                raise HTTPException(404, detail="NOT_FOUND")
            if row.status != "failed":
                raise HTTPException(409, detail="INTEGRATION_NOT_FAILED")
            row.status, row.attempts, row.error_code = "retry", 0, None
            row.next_attempt_at = now()
            enqueue(session, scenario_id, incident_id=row.incident_id)
            return {"status": row.status}

        return mutate(operation)

    app.include_router(router)
