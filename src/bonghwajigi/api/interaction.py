import json
import math
from datetime import UTC, datetime, timedelta
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy import delete, select

from bonghwajigi.contracts.interaction import RouteData, TextTurnData, TextTurnWrite
from bonghwajigi.contracts.mobile_output import Envelope
from bonghwajigi.contracts.policy import Identifier
from bonghwajigi.db.analysis_models import new_id, now
from bonghwajigi.db.app_models import AppAccount, AppSession, AppTextTurn
from bonghwajigi.db.policy_models import PolicyEntity
from bonghwajigi.integration.service import digest
from bonghwajigi.policy.dialogue import (
    DialogueGenerator,
    fallback_dialogue,
    make_dialogue_prompt,
    render_dialogue,
)
from bonghwajigi.policy.service import at, evaluation_time, fresh, projection_view, scope_lock


def active_actor(session, actor):
    account = session.get(AppAccount, (actor["scenario_id"], actor["sub"]))
    if (
        not account
        or not account.enabled
        or account.token_version != actor["token_version"]
        or datetime.fromtimestamp(actor["exp"], UTC) <= now()
    ):
        raise HTTPException(401, detail="UNAUTHENTICATED")
    if actor.get("session_id"):
        active = session.get(AppSession, actor["session_id"])
        if (
            not active
            or active.revoked_at
            or active.expires_at <= now()
            or active.user_id != actor["sub"]
            or active.scenario_id != actor["scenario_id"]
            or active.account_version != account.token_version
        ):
            raise HTTPException(401, detail="UNAUTHENTICATED")


def current_context(session, actor, row, moment):
    state = session.get(
        PolicyEntity, (actor["scenario_id"], "state", row.incident_id + "/" + actor["sub"])
    )
    return (
        state.revision if state else 0,
        state.body if state and fresh(state.body, moment) else {},
    )


def current_policy(session, row):
    data = projection_view(session, row)
    if data["pending_update"] or not data["content"] or not data["content"]["valid_until"]:
        raise HTTPException(409, detail="RESPONSE_REFRESH_REQUIRED")
    return data["content"]


def own_turn(session, actor, response_id, identifier):
    turn = session.scalar(
        select(AppTextTurn).where(
            AppTextTurn.scenario_id == actor["scenario_id"],
            AppTextTurn.user_id == actor["sub"],
            AppTextTurn.response_id == response_id,
            AppTextTurn.client_turn_id == identifier,
        )
    )
    if not turn or turn.session_id != actor.get("session_id"):
        raise HTTPException(404, detail="NOT_FOUND")
    return turn


def validate_turn(session, actor, row, turn, moment):
    active_actor(session, actor)
    if (
        turn.expires_at <= now()
        or turn.valid_until <= moment
        or turn.status == "superseded"
        or turn.token_version != actor["token_version"]
    ):
        raise HTTPException(410, detail="TURN_EXPIRED")
    content = current_policy(session, row)
    context_revision, _ = current_context(session, actor, row, moment)
    if (
        row.revision != turn.response_revision
        or context_revision != turn.context_revision
        or content["input_versions"] != turn.input_versions
    ):
        raise HTTPException(409, detail="TURN_SUPERSEDED")


def validate_context_proposal(session, actor, row, body, moment):
    if not body.proposal_turn_id:
        return
    turn = own_turn(session, actor, row.id, body.proposal_turn_id)
    validate_turn(session, actor, row, turn, moment)
    proposal = turn.result.get("proposal") if turn.result else None
    if (
        turn.status != "complete"
        or not proposal
        or body.base_revision != proposal["base_revision"]
        or body.state.model_dump(mode="json") != proposal["state"]
        or body.overrides.model_dump(mode="json") != proposal["overrides"]
    ):
        raise HTTPException(409, detail="PROPOSAL_MISMATCH")


def turn_view(turn):
    return {
        "turn_id": turn.client_turn_id,
        "response_id": turn.response_id,
        "status": turn.status,
        "response_revision": turn.response_revision,
        "context_revision": turn.context_revision,
        "valid_until": turn.valid_until,
        "assistant": None,
        "proposal": None,
        "reason_code": None,
        **(turn.result or {}),
    }


def route_data(settings, actor, row, incident, location, moment):
    unavailable = {"status": "unavailable", "route": None, "reason": "NO_VERIFIED_ROUTE_GEOMETRY"}
    if (
        settings.mode != "simulation"
        or actor["scenario_id"] != "mobile-demo"
        or row.incident_id != "mobile-fire"
        or not incident
        or incident.body.get("origin") != "synthetic"
        or not fresh(incident.body, moment)
    ):
        return unavailable
    if not location or not fresh(location.body, moment):
        return {**unavailable, "reason": "SIMULATION_LOCATION_REQUIRED"}
    point = location.body
    distance = (
        6371000
        * 2
        * math.asin(
            min(
                1,
                math.sqrt(
                    math.sin(math.radians(point["latitude"] - 36.4) / 2) ** 2
                    + math.cos(math.radians(36.4))
                    * math.cos(math.radians(point["latitude"]))
                    * math.sin(math.radians(point["longitude"] - 129.35) / 2) ** 2
                ),
            )
        )
    )
    if point["accuracy_m"] > 100 or distance > 200:
        return {**unavailable, "reason": "OUTSIDE_SIMULATION_ROUTE_START"}
    fixture = Path(__file__).parents[1] / "policy/mobile_route.json"
    route = json.loads(fixture.read_text())
    route["valid_until"] = min(at(incident.body["expires_at"]), at(point["expires_at"]))
    route["input_versions"] = {
        "incident:" + row.incident_id: incident.revision,
        "location:" + actor["sub"]: location.revision,
    }
    return {"status": "simulation", "route": route, "reason": "SYNTHETIC_DEMO_ONLY"}


def attach_interaction(app, router, settings, actor_dependency, envelope, owned_response):
    sessions = app.state.sessions
    app.state.dialogue_generator = DialogueGenerator(settings)

    @router.post("/me/responses/{response_id}/text-turns", response_model=Envelope[TextTurnData])
    def text_turn(response_id: Identifier, body: TextTurnWrite, actor=actor_dependency):
        fingerprint = digest({"response_id": response_id, **body.model_dump(mode="json")})
        with sessions.begin() as s:
            moment = evaluation_time(scope_lock(s, actor["scenario_id"]))
            active_actor(s, actor)
            row = owned_response(s, actor, response_id)
            previous = s.scalar(
                select(AppTextTurn).where(
                    AppTextTurn.scenario_id == actor["scenario_id"],
                    AppTextTurn.user_id == actor["sub"],
                    AppTextTurn.client_turn_id == body.client_turn_id,
                )
            )
            if previous:
                if previous.fingerprint != fingerprint:
                    raise HTTPException(409, detail="IDEMPOTENCY_CONFLICT")
                if previous.session_id != actor.get("session_id"):
                    raise HTTPException(404, detail="NOT_FOUND")
                validate_turn(s, actor, row, previous, moment)
                if previous.status == "processing":
                    raise HTTPException(409, detail="TURN_IN_PROGRESS")
                return envelope(turn_view(previous))
            content = current_policy(s, row)
            context_revision, state = current_context(s, actor, row, moment)
            if (
                body.base_response_revision != row.revision
                or body.base_context_revision != context_revision
            ):
                raise HTTPException(409, detail="REVISION_CONFLICT")
            user_filter = (
                AppTextTurn.scenario_id == actor["scenario_id"],
                AppTextTurn.user_id == actor["sub"],
            )
            s.execute(delete(AppTextTurn).where(*user_filter, AppTextTurn.expires_at <= now()))
            recent = s.scalars(
                select(AppTextTurn).where(*user_filter).order_by(AppTextTurn.created_at.desc())
            ).all()
            if len(recent) >= 20:
                raise HTTPException(429, detail="TURN_RATE_LIMIT")
            for item in recent:
                if item.status == "processing":
                    if item.created_at + timedelta(seconds=30) > now():
                        raise HTTPException(409, detail="CONVERSATION_BUSY")
                    item.status = "superseded"
            history = [
                {"user": item.text[:300], "assistant": item.result["assistant"]["text"][:300]}
                for item in recent
                if item.status == "complete"
                and item.result
                and item.response_id == response_id
                and item.session_id == actor.get("session_id")
                and item.response_revision == row.revision
                and item.context_revision == context_revision
                and item.valid_until > moment
            ][:3]
            prompt = make_dialogue_prompt(body.text, content, state, list(reversed(history)))
            turn = AppTextTurn(
                id=new_id(),
                scenario_id=actor["scenario_id"],
                user_id=actor["sub"],
                response_id=response_id,
                client_turn_id=body.client_turn_id,
                session_id=actor.get("session_id"),
                token_version=actor["token_version"],
                fingerprint=fingerprint,
                text=body.text,
                status="processing",
                response_revision=row.revision,
                context_revision=context_revision,
                input_versions=content["input_versions"],
                created_at=now(),
                expires_at=now() + timedelta(minutes=10),
                valid_until=min(at(content["valid_until"]), moment + timedelta(minutes=2)),
            )
            s.add(turn)
        # No DB transaction or scenario lock is held while waiting on the GPU.
        try:
            generated = app.state.dialogue_generator.generate(prompt)
            result = render_dialogue(generated["text"], body.text, content, state, context_revision)
        except Exception:
            result = fallback_dialogue(content)
        final_error = None
        with sessions.begin() as s:
            moment = evaluation_time(scope_lock(s, actor["scenario_id"]))
            row = owned_response(s, actor, response_id)
            turn = own_turn(s, actor, response_id, body.client_turn_id)
            try:
                validate_turn(s, actor, row, turn, moment)
            except HTTPException as exc:
                # Commit the terminal state before returning the conflict. Otherwise rollback
                # would leave an already-finished generation blocking the next turn as busy.
                turn.status, turn.result = "superseded", None
                final_error = exc
            else:
                turn.status, turn.result = "complete", result
                completed = turn_view(turn)
        if final_error:
            raise final_error
        return envelope(completed)

    @router.get(
        "/me/responses/{response_id}/text-turns/{turn_id}", response_model=Envelope[TextTurnData]
    )
    def get_text_turn(response_id: Identifier, turn_id: Identifier, actor=actor_dependency):
        with sessions.begin() as s:
            moment = evaluation_time(scope_lock(s, actor["scenario_id"]))
            row = owned_response(s, actor, response_id)
            turn = own_turn(s, actor, response_id, turn_id)
            validate_turn(s, actor, row, turn, moment)
            if turn.status == "processing" and turn.created_at + timedelta(seconds=30) <= now():
                raise HTTPException(410, detail="TURN_EXPIRED")
            return envelope(
                turn_view(turn), "partial" if turn.status == "processing" else "current"
            )

    @router.get("/me/responses/{response_id}/route", response_model=Envelope[RouteData])
    def route(response_id: Identifier, actor=actor_dependency):
        with sessions.begin() as s:
            moment = evaluation_time(scope_lock(s, actor["scenario_id"]))
            row = owned_response(s, actor, response_id)
            incident = s.get(PolicyEntity, (actor["scenario_id"], "incident", row.incident_id))
            location = s.get(PolicyEntity, (actor["scenario_id"], "location", actor["sub"]))
            data = route_data(settings, actor, row, incident, location, moment)
            return envelope(data, "current" if data["route"] else "unavailable")
