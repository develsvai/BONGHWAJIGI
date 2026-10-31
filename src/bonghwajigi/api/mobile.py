"""사설망 MVP 앱 API. 0.1 초안과 구분되는 0.2.0-mvp 실행 계약."""

import hashlib
import hmac
import time
from datetime import timedelta

import jwt
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from bonghwajigi.api.user_auth import user_auth
from bonghwajigi.contracts.app import (
    ContextWrite,
    DeviceWrite,
    LocationWrite,
    Preferences,
    PreferencesWrite,
    ProfileWrite,
    ReceiptWrite,
    StoredInput,
)
from bonghwajigi.contracts.policy import CurrentStateInput, Identifier, LocationInput, ProfileInput
from bonghwajigi.db.analysis_models import new_id, now
from bonghwajigi.db.app_models import AppAccount, AppMutation
from bonghwajigi.db.delivery_models import ChangeSequence, Delivery, Device, UserChange
from bonghwajigi.db.policy_models import PolicyEntity, PolicyProjection, PolicySnapshot
from bonghwajigi.integration.service import digest
from bonghwajigi.notifications.service import emit_change
from bonghwajigi.policy.service import (
    at,
    enqueue,
    evaluation_time,
    fresh,
    projection_view,
    put_entity,
    relevance,
    scope_lock,
)
from bonghwajigi.policy.three_stage import POLICY_VERSION


def attach_mobile(app, settings):
    sessions = app.state.sessions
    auth = user_auth(settings, sessions)
    actor_dependency = Depends(auth)
    router = APIRouter(prefix="/v1", tags=["mobile-mvp"])

    @app.exception_handler(SQLAlchemyError)
    async def database_error(request, exc):
        return JSONResponse(status_code=503, content={"detail": "DATABASE_UNAVAILABLE"})

    def envelope(data, status="current"):
        return {
            "meta": {
                "schema_version": "0.2.0-mvp",
                "mode": "simulation",
                "request_id": new_id(),
                "generated_at": now(),
                "data_status": status,
            },
            "data": data,
        }

    def key(actor):
        return actor["scenario_id"], actor["sub"]

    def opaque(actor, kind, identifier):
        content = ":".join((*key(actor), kind, identifier)).encode()
        return hmac.new(
            settings.jwt_secret.get_secret_value().encode(), content, hashlib.sha256
        ).hexdigest()[:32]

    def get_entity(session, actor, kind):
        return session.get(PolicyEntity, (actor["scenario_id"], kind, actor["sub"]))

    def base_check(row, base):
        if (row.revision if row else 0) != base:
            raise HTTPException(409, detail="REVISION_CONFLICT")

    def store(session, actor, kind, data, base):
        row = get_entity(session, actor, kind)
        base_check(row, base)
        put_entity(
            session,
            actor["scenario_id"],
            kind,
            actor["sub"],
            StoredInput(revision=base + 1, data=data),
            user_id=actor["sub"],
        )
        emit_change(session, *key(actor), kind, actor["sub"], base + 1)
        return base + 1

    def mutation(session, actor, resource, identifier, body, operation):
        fingerprint = digest(body)
        previous = (
            session.get(AppMutation, (*key(actor), resource, identifier)) if identifier else None
        )
        if previous:
            if previous.fingerprint != fingerprint:
                raise HTTPException(409, detail="IDEMPOTENCY_CONFLICT")
            return previous.result
        result = operation()
        if identifier:
            session.add(
                AppMutation(
                    scenario_id=actor["scenario_id"],
                    user_id=actor["sub"],
                    resource=resource,
                    key=identifier,
                    fingerprint=fingerprint,
                    result=result,
                )
            )
        return result

    def normalized(profile, revision):
        mobility = {
            "independent": "independent",
            "walking_aid": "needs_time",
            "wheelchair": "needs_time",
            "assistance_required": "requires_help",
            "unknown": "unknown",
        }[profile.mobility]
        if mobility != "requires_help" and (
            profile.stairs in {"difficult", "unable"}
            or "vision" in profile.sensory_supports
            or profile.dependents
        ):
            mobility = "needs_time"
        return ProfileInput(
            revision=revision,
            mobility=mobility,
            mobility_assistance=mobility in {"needs_time", "requires_help"},
            children_accompanying="child" in profile.dependents,
            helper_registered=profile.helper_registered,
            vehicle_access=profile.vehicle_access,
            communication="audio"
            if profile.communication_preference == "voice"
            else profile.communication_preference,
        )

    def owned_response(session, actor, identifier):
        row = session.scalar(
            select(PolicyProjection).where(
                PolicyProjection.id == identifier,
                PolicyProjection.scenario_id == actor["scenario_id"],
                PolicyProjection.user_id == actor["sub"],
            )
        )
        if not row:
            raise HTTPException(404, detail="NOT_FOUND")
        return row

    def public_resource(session, actor, kind, identifier):
        if kind == "alert":
            return opaque(actor, "alert", identifier)
        if kind == "response":
            row = session.scalar(
                select(PolicyProjection).where(
                    PolicyProjection.scenario_id == actor["scenario_id"],
                    PolicyProjection.user_id == actor["sub"],
                    PolicyProjection.incident_id == identifier,
                )
            )
            return row.id if row else None
        return "me"

    def location_data(session, actor, moment):
        row = get_entity(session, actor, "app_location")
        internal = get_entity(session, actor, "location")
        if not row or not internal:
            return {
                "revision": row.revision if row else 0,
                "status": "unavailable",
                "fix": None,
                "valid_until": None,
                "reason_codes": ["LOCATION_NOT_AVAILABLE"],
            }
        valid = fresh(internal.body, moment)
        return {
            "revision": row.revision,
            "status": "available" if valid else "stale",
            "fix": row.body["data"],
            "valid_until": internal.body["expires_at"],
            "reason_codes": [] if valid else ["LOCATION_EXPIRED"],
        }

    def alert_rows(session, actor, identifier=None):
        location = get_entity(session, actor, "location")
        moment = evaluation_time(scope_lock(session, actor["scenario_id"]))
        rows = session.scalars(
            select(PolicyEntity)
            .where(
                PolicyEntity.scenario_id == actor["scenario_id"],
                PolicyEntity.kind == "alert",
            )
            .order_by(PolicyEntity.entity_id)
            .limit(200)
        ).all()
        result = []
        for row in rows:
            relation, reason = relevance(
                location.body if location else None, row.body["area"], moment
            )
            if relation == "outside":
                previous = session.scalar(
                    select(Delivery.id)
                    .where(
                        Delivery.scenario_id == actor["scenario_id"],
                        Delivery.user_id == actor["sub"],
                        Delivery.resource_type == "alert",
                        Delivery.resource_id == row.entity_id,
                    )
                    .limit(1)
                )
                if not previous:
                    continue
            external = opaque(actor, "alert", row.entity_id)
            if identifier and identifier != external:
                continue
            active = (
                row.body["state"] == "issued"
                and row.body["validity_confirmed"]
                and (row.body["source"]["verified"] and fresh(row.body, moment, "issued_at"))
            )
            result.append(
                (
                    row,
                    {
                        "id": external,
                        "revision": row.revision,
                        "response_id": public_resource(
                            session, actor, "response", row.entity_id.split("/", 1)[0]
                        ),
                        "incident_id": row.entity_id.split("/", 1)[0],
                        "original_text": row.body["raw_text"],
                        "official_severity": row.body["severity"],
                        "authority": row.body["authority"],
                        "issued_at": row.body["issued_at"],
                        "valid_until": row.body["expires_at"],
                        "instruction_kind": row.body["instruction_kind"],
                        "source": row.body["source"],
                        "status": "cancelled"
                        if row.body["state"] == "cancelled"
                        else ("active" if active else "unconfirmed_or_expired"),
                        "relevance": {"status": relation, "reason_code": reason},
                        "requires_qwen": False,
                    },
                )
            )
        return result

    @router.get("/app-config")
    def config(actor=actor_dependency):
        return envelope(
            {
                "contract_version": "0.2.0-mvp",
                "disaster_types": ["wildfire"],
                "supported_locales": ["ko-KR"],
                "levels": [
                    {"level": k, "number": n, "label": label}
                    for k, n, label in [
                        ("prepare", 1, "경고"),
                        ("act", 2, "대피"),
                        ("request_assistance", 3, "위급"),
                    ]
                ],
                "features": {
                    "impact_prediction": False,
                    "route_3d": False,
                    "voice_turns": False,
                    "server_audio": False,
                    "support_draft": False,
                    "route_geometry": False,
                    "push_provider": settings.push_provider,
                },
                "policy_status": "reviewed_mvp",
                "location_max_age_seconds": 300,
                "updates_wait_seconds": 25,
                "emergency_phone": "119",
                "automatic_emergency_call": False,
                "draft_owner": "device",
            }
        )

    @router.get("/me/profile")
    def get_profile(actor=actor_dependency):
        with sessions() as s:
            row = get_entity(s, actor, "app_profile")
            return envelope(
                {"revision": row.revision if row else 0, "profile": row.body["data"] if row else {}}
            )

    @router.put("/me/profile")
    def put_profile(
        body: ProfileWrite,
        actor=actor_dependency,
        idempotency_key: str | None = Header(default=None, min_length=1, max_length=128),
    ):
        with sessions.begin() as s:
            scope_lock(s, actor["scenario_id"])

            def apply():
                revision = store(
                    s,
                    actor,
                    "app_profile",
                    body.profile.model_dump(mode="json"),
                    body.base_revision,
                )
                old = get_entity(s, actor, "profile")
                put_entity(
                    s,
                    actor["scenario_id"],
                    "profile",
                    actor["sub"],
                    normalized(body.profile, old.revision + 1 if old else 1),
                    user_id=actor["sub"],
                )
                return {"revision": revision, "profile": body.profile.model_dump(mode="json")}

            return envelope(
                mutation(s, actor, "profile", idempotency_key, body.model_dump(mode="json"), apply)
            )

    @router.delete("/me/profile")
    def delete_profile(actor=actor_dependency):
        with sessions.begin() as s:
            scope_lock(s, actor["scenario_id"])
            current = get_entity(s, actor, "app_profile")
            revision = store(s, actor, "app_profile", {}, current.revision if current else 0)
            old = get_entity(s, actor, "profile")
            put_entity(
                s,
                actor["scenario_id"],
                "profile",
                actor["sub"],
                ProfileInput(revision=old.revision + 1 if old else 1),
                user_id=actor["sub"],
            )
            s.execute(
                delete(AppMutation).where(
                    AppMutation.scenario_id == actor["scenario_id"],
                    AppMutation.user_id == actor["sub"],
                    AppMutation.resource == "profile",
                )
            )
            return envelope({"revision": revision, "profile": {}})

    @router.get("/me/preferences")
    def get_preferences(actor=actor_dependency):
        with sessions() as s:
            row = get_entity(s, actor, "preferences")
            return envelope(
                {
                    "revision": row.revision if row else 0,
                    "preferences": row.body["data"]
                    if row
                    else Preferences().model_dump(mode="json"),
                }
            )

    @router.put("/me/preferences")
    def put_preferences(body: PreferencesWrite, actor=actor_dependency):
        with sessions.begin() as s:
            scope_lock(s, actor["scenario_id"])
            revision = store(
                s,
                actor,
                "preferences",
                body.preferences.model_dump(mode="json"),
                body.base_revision,
            )
            return envelope(
                {"revision": revision, "preferences": body.preferences.model_dump(mode="json")}
            )

    @router.put("/me/devices/{installation_id}")
    def put_device(installation_id: Identifier, body: DeviceWrite, actor=actor_dependency):
        with sessions.begin() as s:
            scope_lock(s, actor["scenario_id"])
            token_hash = (
                hashlib.sha256(body.push_token.encode()).hexdigest() if body.push_token else None
            )
            row = s.scalar(
                select(Device).where(
                    Device.scenario_id == actor["scenario_id"],
                    Device.user_id == actor["sub"],
                    Device.installation_id == installation_id,
                )
            )
            other = (
                s.scalar(select(Device).where(Device.token_hash == token_hash))
                if token_hash
                else None
            )
            if other and (not row or other.id != row.id):
                raise HTTPException(409, detail="DEVICE_TOKEN_ALREADY_REGISTERED")
            if row is None:
                row = Device(
                    scenario_id=actor["scenario_id"],
                    user_id=actor["sub"],
                    installation_id=installation_id,
                    provider="fcm",
                )
                s.add(row)
                row.revision = 1
            else:
                row.revision += 1
            row.enabled = body.notification_permission == "granted" and body.push_token is not None
            row.token, row.token_hash = (
                (body.push_token, token_hash) if row.enabled else (None, None)
            )
            row.updated_at = now()
            try:
                s.flush()
            except IntegrityError:
                raise HTTPException(409, detail="DEVICE_TOKEN_ALREADY_REGISTERED") from None
            return envelope(
                {
                    "installation_id": installation_id,
                    "revision": row.revision,
                    "push_status": "registered" if row.enabled else "disabled",
                    "notification_permission": body.notification_permission,
                    "provider_mode": settings.push_provider,
                }
            )

    @router.delete("/me/devices/{installation_id}")
    def delete_device(installation_id: Identifier, actor=actor_dependency):
        with sessions.begin() as s:
            scope_lock(s, actor["scenario_id"])
            row = s.scalar(
                select(Device).where(
                    Device.scenario_id == actor["scenario_id"],
                    Device.user_id == actor["sub"],
                    Device.installation_id == installation_id,
                )
            )
            if row:
                row.enabled, row.token, row.token_hash = False, None, None
                row.revision += 1
            return envelope({"installation_id": installation_id, "push_status": "disabled"})

    @router.get("/me/location")
    def get_location(actor=actor_dependency):
        with sessions.begin() as s:
            moment = evaluation_time(scope_lock(s, actor["scenario_id"]))
            return envelope(location_data(s, actor, moment))

    @router.put("/me/location")
    def put_location(body: LocationWrite, actor=actor_dependency):
        with sessions.begin() as s:
            scope = scope_lock(s, actor["scenario_id"])
            moment = evaluation_time(scope)
            device = s.scalar(
                select(Device).where(
                    Device.scenario_id == actor["scenario_id"],
                    Device.user_id == actor["sub"],
                    Device.installation_id == body.installation_id,
                )
            )
            if not device:
                raise HTTPException(404, detail="INSTALLATION_NOT_FOUND")
            if body.captured_at > moment or body.captured_at < moment - timedelta(minutes=5):
                raise HTTPException(422, detail="LOCATION_TIME_INVALID")

            def apply():
                old, app_row = (
                    get_entity(s, actor, "location"),
                    get_entity(s, actor, "app_location"),
                )
                if old and at(old.body["observed_at"]) >= body.captured_at:
                    raise HTTPException(409, detail="LOCATION_FIX_SUPERSEDED")
                if (
                    app_row
                    and app_row.body["data"].get("deleted_at")
                    and (body.captured_at <= at(app_row.body["data"]["deleted_at"]))
                ):
                    raise HTTPException(409, detail="LOCATION_FIX_SUPERSEDED")
                store(
                    s,
                    actor,
                    "app_location",
                    body.model_dump(mode="json"),
                    app_row.revision if app_row else 0,
                )
                put_entity(
                    s,
                    actor["scenario_id"],
                    "location",
                    actor["sub"],
                    LocationInput(
                        revision=old.revision + 1 if old else 1,
                        latitude=body.latitude,
                        longitude=body.longitude,
                        accuracy_m=body.accuracy_m,
                        observed_at=body.captured_at,
                        expires_at=body.captured_at + timedelta(minutes=5),
                    ),
                    user_id=actor["sub"],
                )
                return location_data(s, actor, moment)

            result = mutation(
                s, actor, "location", body.fix_id, body.model_dump(mode="json"), apply
            )
            current = get_entity(s, actor, "app_location")
            if current and current.revision != result["revision"]:
                raise HTTPException(409, detail="LOCATION_FIX_SUPERSEDED")
            return envelope(result)

    @router.delete("/me/location")
    def delete_location(actor=actor_dependency):
        with sessions.begin() as s:
            moment = evaluation_time(scope_lock(s, actor["scenario_id"]))
            row = get_entity(s, actor, "app_location")
            store(
                s,
                actor,
                "app_location",
                {"deleted_at": moment.isoformat()},
                row.revision if row else 0,
            )
            current = get_entity(s, actor, "location")
            if current:
                s.delete(current)
                s.flush()
            enqueue(s, actor["scenario_id"], user_id=actor["sub"])
            s.execute(
                delete(AppMutation).where(
                    AppMutation.scenario_id == actor["scenario_id"],
                    AppMutation.user_id == actor["sub"],
                    AppMutation.resource == "location",
                )
            )
            return envelope(location_data(s, actor, moment))

    @router.get("/me/alerts")
    def alerts(actor=actor_dependency):
        with sessions.begin() as s:
            return envelope({"items": [data for _, data in alert_rows(s, actor)]})

    @router.get("/me/alerts/{alert_id}")
    def alert(alert_id: Identifier, actor=actor_dependency):
        with sessions.begin() as s:
            rows = alert_rows(s, actor, alert_id)
            if not rows:
                raise HTTPException(404, detail="NOT_FOUND")
            return envelope(rows[0][1])

    @router.post("/me/alerts/{alert_id}/receipts")
    def receipt(alert_id: Identifier, body: ReceiptWrite, actor=actor_dependency):
        if body.occurred_at > now() + timedelta(seconds=30):
            raise HTTPException(422, detail="RECEIPT_TIME_INVALID")
        with sessions.begin() as s:
            rows = alert_rows(s, actor, alert_id)
            if not rows:
                raise HTTPException(404, detail="NOT_FOUND")
            row = rows[0][0]
            device = s.scalar(
                select(Device).where(
                    Device.scenario_id == actor["scenario_id"],
                    Device.user_id == actor["sub"],
                    Device.installation_id == body.installation_id,
                )
            )
            if not device or body.alert_revision > row.revision:
                raise HTTPException(422, detail="RECEIPT_TARGET_INVALID")
            delivery = s.scalar(
                select(Delivery)
                .where(
                    Delivery.device_id == device.id,
                    Delivery.resource_type == "alert",
                    Delivery.resource_id == row.entity_id,
                    Delivery.revision == body.alert_revision,
                )
                .with_for_update()
            )
            if delivery:
                if delivery.received_at is None:
                    delivery.received_at = body.occurred_at
                if body.event == "opened" and delivery.opened_at is None:
                    delivery.opened_at = body.occurred_at
            receipt_key = ":".join(
                [alert_id, body.installation_id, str(body.alert_revision), body.event]
            )
            return envelope(
                mutation(
                    s,
                    actor,
                    "receipt",
                    receipt_key,
                    {"alert": alert_id, "revision": body.alert_revision, "event": body.event},
                    lambda: {
                        "receipt_id": delivery.id if delivery else new_id(),
                        "recorded_at": now().isoformat(),
                        "meaning": "client_reported_only",
                    },
                )
            )

    @router.get("/me/responses/{response_id}")
    def response(response_id: Identifier, actor=actor_dependency):
        with sessions.begin() as s:
            scope_lock(s, actor["scenario_id"])
            row = owned_response(s, actor, response_id)
            data = projection_view(s, row)
            if data["content"]:
                data["content"]["prediction"] = {
                    "status": "unavailable",
                    "probability": None,
                    "used_for_response_level": False,
                    "reason": "MODEL_CONNECTION_EXCLUDED",
                }
            return envelope(
                {"id": row.id, **data}, "partial" if data["pending_update"] else "current"
            )

    @router.put("/me/responses/{response_id}/context", status_code=202)
    def context(response_id: Identifier, body: ContextWrite, actor=actor_dependency):
        with sessions.begin() as s:
            scope = scope_lock(s, actor["scenario_id"])
            row = owned_response(s, actor, response_id)
            moment = evaluation_time(scope)
            if not moment - timedelta(minutes=5) <= body.observed_at <= moment:
                raise HTTPException(422, detail="CONTEXT_TIME_INVALID")
            identifier = row.incident_id + "/" + actor["sub"]
            current = s.get(PolicyEntity, (actor["scenario_id"], "state", identifier))
            base_check(current, body.base_revision)
            mobility = {
                "walking_aid": "needs_time",
                "wheelchair": "needs_time",
                "assistance_required": "requires_help",
            }.get(body.overrides.mobility, body.overrides.mobility)
            state = body.state.model_dump()
            if body.overrides.alone_now == "yes" and state["helper_present"] is None:
                state["helper_present"] = False
            put_entity(
                s,
                actor["scenario_id"],
                "state",
                identifier,
                CurrentStateInput(
                    revision=body.base_revision + 1,
                    observed_at=body.observed_at,
                    expires_at=body.observed_at + timedelta(minutes=5),
                    mobility_override=mobility,
                    **state,
                ),
                user_id=actor["sub"],
                incident_id=row.incident_id,
            )
            return envelope(
                {
                    "context_revision": body.base_revision + 1,
                    "response_id": response_id,
                    "expires_at": body.observed_at + timedelta(minutes=5),
                    "reevaluation": "pending",
                }
            )

    @router.get("/me/responses/{response_id}/history")
    def history(
        response_id: Identifier,
        after_revision: int = Query(default=0, ge=0),
        actor=actor_dependency,
    ):
        with sessions() as s:
            row = owned_response(s, actor, response_id)
            items = s.scalars(
                select(PolicySnapshot)
                .where(
                    PolicySnapshot.projection_id == row.id, PolicySnapshot.revision > after_revision
                )
                .order_by(PolicySnapshot.revision)
                .limit(100)
            ).all()
            return envelope(
                {
                    "items": [
                        {
                            "revision": i.revision,
                            "evaluated_at": i.evaluated_at,
                            "personal_response": i.content["personal_response"],
                            "actions": i.content["actions"],
                            "historical_record": True,
                        }
                        for i in items
                    ]
                }
            )

    @router.get("/me/updates")
    def updates(
        cursor: str | None = Query(default=None, max_length=2048),
        wait_seconds: int = Query(default=0, ge=0, le=25),
        actor=actor_dependency,
    ):
        sequence = 0
        if cursor:
            try:
                claims = jwt.decode(
                    cursor,
                    settings.jwt_secret.get_secret_value(),
                    algorithms=["HS256"],
                    audience="bonghwajigi-updates",
                    issuer=settings.jwt_issuer,
                    options={"require": ["sub", "scenario_id", "sequence", "exp"]},
                )
                if (
                    key(claims) != key(actor)
                    or type(claims["sequence"]) is not int
                    or claims["sequence"] < 0
                ):
                    raise ValueError
                sequence = claims["sequence"]
            except jwt.ExpiredSignatureError:
                raise HTTPException(410, detail="CURSOR_EXPIRED_RESYNC") from None
            except (jwt.PyJWTError, ValueError, KeyError, TypeError):
                raise HTTPException(400, detail="INVALID_CURSOR") from None
        deadline = time.monotonic() + wait_seconds
        while True:
            with sessions() as s:
                account = s.get(AppAccount, key(actor))
                if (
                    not account
                    or not account.enabled
                    or account.token_version != actor["token_version"]
                ):
                    raise HTTPException(401, detail="UNAUTHENTICATED")
                # 먼저 watermark를 읽고 그 이하만 조회해 조회 중 새 커밋을 건너뛰지 않는다.
                watermark = s.get(ChangeSequence, actor["scenario_id"])
                maximum = watermark.value if watermark else 0
                if sequence > maximum:
                    raise HTTPException(400, detail="INVALID_CURSOR")
                rows = s.scalars(
                    select(UserChange)
                    .where(
                        UserChange.scenario_id == actor["scenario_id"],
                        UserChange.user_id == actor["sub"],
                        UserChange.sequence > sequence,
                        UserChange.sequence <= maximum,
                    )
                    .order_by(UserChange.sequence)
                    .limit(101)
                ).all()
                more = len(rows) > 100
                result = [
                    {
                        "event_id": r.id,
                        "type": r.resource_type + ".updated",
                        "resource_id": public_resource(s, actor, r.resource_type, r.resource_id),
                        "resource_revision": r.revision,
                        "occurred_at": r.created_at,
                    }
                    for r in rows[:100]
                ]
                value = rows[99].sequence if more else maximum
                token = jwt.encode(
                    {
                        "sub": actor["sub"],
                        "scenario_id": actor["scenario_id"],
                        "sequence": value,
                        "iss": settings.jwt_issuer,
                        "aud": "bonghwajigi-updates",
                        "exp": now() + timedelta(days=1),
                    },
                    settings.jwt_secret.get_secret_value(),
                    algorithm="HS256",
                )
            if result or time.monotonic() >= deadline:
                return envelope({"events": result, "next_cursor": token, "has_more": more})
            time.sleep(min(0.25, max(0, deadline - time.monotonic())))

    @router.get("/disasters")
    def disasters(actor=actor_dependency):
        with sessions.begin() as s:
            moment = evaluation_time(scope_lock(s, actor["scenario_id"]))
            location = get_entity(s, actor, "location")
            rows = s.scalars(
                select(PolicyEntity)
                .where(
                    PolicyEntity.scenario_id == actor["scenario_id"],
                    PolicyEntity.kind == "incident",
                )
                .order_by(PolicyEntity.entity_id)
                .limit(200)
            ).all()
            items = []
            for row in rows:
                relation, reason = relevance(
                    location.body if location else None, row.body["area"], moment
                )
                if relation == "outside" or at(row.body["observed_at"]) < moment - timedelta(
                    days=92
                ):
                    continue
                projection = s.scalar(
                    select(PolicyProjection).where(
                        PolicyProjection.scenario_id == actor["scenario_id"],
                        PolicyProjection.user_id == actor["sub"],
                        PolicyProjection.incident_id == row.entity_id,
                    )
                )
                items.append(
                    {
                        "id": row.entity_id,
                        "title": row.body["title"],
                        "origin": row.body["origin"],
                        "observed_at": row.body["observed_at"],
                        "relevance": relation,
                        "reason": reason,
                        "response_id": projection.id if projection else None,
                        "data_status": "current" if fresh(row.body, moment) else "stale",
                    }
                )
            items.sort(key=lambda i: i["observed_at"], reverse=True)
            return envelope({"items": items})

    @router.get("/safety-rules/{disaster_type}")
    def safety_rules(disaster_type: str, actor=actor_dependency):
        if disaster_type != "wildfire":
            raise HTTPException(404, detail="UNSUPPORTED_DISASTER")
        with sessions.begin() as s:
            moment = evaluation_time(scope_lock(s, actor["scenario_id"]))
            ids = [
                "mvp-prepare-follow",
                "mvp-prepare-bag",
                "mvp-act-follow",
                "mvp-information-arrived",
            ]
            items = []
            for identifier in ids:
                row = s.get(PolicyEntity, (actor["scenario_id"], "guidance", identifier))
                if (
                    row
                    and row.body["review_state"] == "approved_mvp"
                    and fresh(row.body, moment, "valid_from")
                ):
                    items.append(
                        {
                            "id": identifier,
                            "text": row.body["text"],
                            "source": row.body["source"],
                            "revision": row.revision,
                        }
                    )
            return envelope(
                {
                    "disaster_type": "wildfire",
                    "status": "available" if items else "unavailable",
                    "policy_version": POLICY_VERSION,
                    "items": items,
                }
            )

    @router.get("/home")
    def home(actor=actor_dependency):
        return envelope(
            {
                "nearby_disasters": disasters(actor)["data"]["items"][:3],
                "basic_rules": safety_rules("wildfire", actor)["data"],
                "location": get_location(actor)["data"],
                "features": config(actor)["data"]["features"],
            }
        )

    @router.get("/me/deliveries")
    def deliveries(actor=actor_dependency):
        with sessions() as s:
            rows = s.scalars(
                select(Delivery)
                .where(
                    Delivery.scenario_id == actor["scenario_id"], Delivery.user_id == actor["sub"]
                )
                .order_by(Delivery.created_at.desc())
                .limit(100)
            ).all()
            return envelope(
                {
                    "items": [
                        {
                            "id": r.id,
                            "resource_type": r.resource_type,
                            "resource_id": public_resource(
                                s, actor, r.resource_type, r.resource_id
                            ),
                            "revision": r.revision,
                            "status": r.status,
                            "attempts": r.attempts,
                            "error_code": r.error_code,
                            "received_at": r.received_at,
                            "opened_at": r.opened_at,
                        }
                        for r in rows
                    ]
                }
            )

    @router.post("/me/logout")
    def logout(actor=actor_dependency):
        with sessions.begin() as s:
            scope_lock(s, actor["scenario_id"])
            account = s.get(AppAccount, key(actor))
            account.token_version += 1
            for device in s.scalars(
                select(Device).where(
                    Device.scenario_id == actor["scenario_id"], Device.user_id == actor["sub"]
                )
            ).all():
                device.enabled, device.token, device.token_hash = False, None, None
                device.revision += 1
        return envelope({"status": "logged_out"})

    @router.get("/me/responses/{response_id}/route")
    def route(response_id: Identifier, actor=actor_dependency):
        with sessions() as s:
            owned_response(s, actor, response_id)
        return envelope(
            {"status": "unavailable", "route": None, "reason": "NO_VERIFIED_ROUTE_GEOMETRY"},
            "unavailable",
        )

    @router.post("/me/responses/{response_id}/support-drafts", status_code=503)
    def support_draft(response_id: Identifier, actor=actor_dependency):
        with sessions() as s:
            owned_response(s, actor, response_id)
        raise HTTPException(503, detail="USE_ON_DEVICE_DRAFT_WITHOUT_WAITING_FOR_SERVER")

    @router.post("/me/responses/{response_id}/voice-turns", status_code=503)
    def voice(response_id: Identifier, actor=actor_dependency):
        raise HTTPException(503, detail="VOICE_DISABLED_SERVER_PROVIDES_TEXT")

    @router.get("/me/responses/{response_id}/voice-turns/{turn_id}", status_code=503)
    def get_voice(response_id: Identifier, turn_id: Identifier, actor=actor_dependency):
        raise HTTPException(503, detail="VOICE_DISABLED_SERVER_PROVIDES_TEXT")

    @router.delete("/me/responses/{response_id}/voice-turns/{turn_id}", status_code=503)
    def delete_voice(response_id: Identifier, turn_id: Identifier, actor=actor_dependency):
        raise HTTPException(503, detail="VOICE_DISABLED_SERVER_PROVIDES_TEXT")

    app.include_router(router)
