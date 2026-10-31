from datetime import datetime, timedelta

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select
from test_three_stage import MOMENT, set_environment
from test_three_stage import mvp_db as mvp_db

from bonghwajigi.api.user_auth import issue_token
from bonghwajigi.common.config import Settings
from bonghwajigi.db.analysis_models import now
from bonghwajigi.db.app_models import AppAccount, AppMutation
from bonghwajigi.db.delivery_models import Delivery, Device
from bonghwajigi.db.policy_models import PolicyEntity, PolicyProjection
from bonghwajigi.policy.service import evaluate_once


@pytest.fixture
def mobile(mvp_db, monkeypatch):
    sessions, scenario = mvp_db
    settings = Settings(
        database_url=sessions.kw["bind"].url.render_as_string(hide_password=False),
        analysis_enabled=True,
        policy_enabled=True,
        app_enabled=True,
        service_token="service-test-token",
        jwt_secret="mobile-test-signing-key-for-tests-only-1234",
        broker_url="redis://127.0.0.1:16379/0",
        notifications_enabled=True,
        push_provider="simulation",
    )
    with sessions.begin() as s:
        for user in "abc":
            s.add(AppAccount(scenario_id=scenario, user_id=user, token_version=1))
    monkeypatch.setattr("bonghwajigi.api.app.Settings", lambda: settings)
    from bonghwajigi.api.app import create_app

    with TestClient(create_app()) as client:

        def headers(user="a"):
            return {"Authorization": "Bearer " + issue_token(settings, user, scenario)}

        yield client, sessions, scenario, settings, headers
    with sessions.begin() as s:
        s.execute(delete(AppMutation).where(AppMutation.scenario_id == scenario))
        s.execute(delete(AppAccount).where(AppAccount.scenario_id == scenario))


def response_id(sessions, scenario, user):
    with sessions() as s:
        return s.scalar(
            select(PolicyProjection.id).where(
                PolicyProjection.scenario_id == scenario, PolicyProjection.user_id == user
            )
        )


def test_auth_expiry_service_token_and_other_user_ownership(mobile):
    client, sessions, scenario, settings, headers = mobile
    assert client.get("/v1/me/profile").status_code == 401
    assert (
        client.get(
            "/v1/me/profile", headers={"Authorization": "Bearer service-test-token"}
        ).status_code
        == 401
    )
    token = issue_token(settings, "a", scenario)
    claims = jwt.decode(
        token,
        settings.jwt_secret.get_secret_value(),
        algorithms=["HS256"],
        options={"verify_aud": False},
    )
    claims["exp"] = now() - timedelta(seconds=1)
    expired = jwt.encode(claims, settings.jwt_secret.get_secret_value(), algorithm="HS256")
    assert (
        client.get("/v1/me/profile", headers={"Authorization": "Bearer " + expired}).status_code
        == 401
    )
    set_environment(sessions, scenario, "H2")
    identifier = response_id(sessions, scenario, "a")
    assert client.get("/v1/me/responses/" + identifier, headers=headers("b")).status_code == 404
    data = client.get("/v1/me/responses/" + identifier, headers=headers()).json()["data"]
    assert data["content"]["prediction"]["probability"] is None
    assert data["content"]["personal_response"]["label"] == "경고"


def test_profile_revision_idempotency_and_mapping(mobile):
    client, sessions, scenario, _, headers = mobile
    body = {"base_revision": 0, "profile": {"mobility": "wheelchair", "dependents": ["child"]}}
    h = {**headers(), "Idempotency-Key": "profile-once"}
    first = client.put("/v1/me/profile", json=body, headers=h)
    assert first.status_code == 200
    assert client.put("/v1/me/profile", json=body, headers=h).json()["data"] == first.json()["data"]
    assert client.put("/v1/me/profile", json=body, headers=headers()).status_code == 409
    body["profile"]["mobility"] = "independent"
    assert client.put("/v1/me/profile", json=body, headers=h).status_code == 409
    with sessions() as s:
        row = s.get(PolicyEntity, (scenario, "profile", "a"))
        assert row.body["mobility"] == "needs_time"
        assert row.body["children_accompanying"] is False
        assert row.body["child_registered"] is True
        assert row.body["assistive_device"] is True
    assert client.get("/v1/me/profile", headers=headers("b")).json()["data"]["revision"] == 0


def test_location_order_duplicates_deletion_and_stale_actions(mobile):
    client, sessions, scenario, _, headers = mobile
    with sessions.begin() as s:
        s.delete(s.get(PolicyEntity, (scenario, "location", "a")))
    body = {
        "fix_id": "fix-1",
        "installation_id": "phone",
        "latitude": 36,
        "longitude": 129,
        "accuracy_m": 10,
        "captured_at": (MOMENT - timedelta(seconds=20)).isoformat(),
    }
    first = client.put("/v1/me/location", json=body, headers=headers())
    assert first.status_code == 200 and first.json()["data"]["status"] == "available"
    assert client.put("/v1/me/location", json=body, headers=headers()).status_code == 200
    body["fix_id"], body["captured_at"] = "old-fix", (MOMENT - timedelta(seconds=30)).isoformat()
    assert client.put("/v1/me/location", json=body, headers=headers()).status_code == 409
    set_environment(sessions, scenario, "H3")
    identifier = response_id(sessions, scenario, "a")
    assert client.delete("/v1/me/location", headers=headers()).status_code == 200
    pending = client.get("/v1/me/responses/" + identifier, headers=headers()).json()["data"]
    assert pending["pending_update"] and pending["content"]["actions"] == []
    assert pending["content"]["personal_response"]["level"] == "unknown"
    assert client.get("/v1/me/location", headers=headers()).json()["data"]["fix"] is None
    body["fix_id"] = "after-delete-old"
    assert client.put("/v1/me/location", json=body, headers=headers()).status_code == 409


def test_state_is_confirmed_transient_and_cannot_claim_authoritative_route(mobile):
    client, sessions, scenario, _, headers = mobile
    set_environment(sessions, scenario, "H3")
    identifier = response_id(sessions, scenario, "a")
    body = {
        "base_revision": 0,
        "observed_at": MOMENT.isoformat(),
        "confirmation": "user_confirmed",
        "state": {"observed_hazard": "trapped", "can_move": False},
    }
    assert (
        client.put(
            f"/v1/me/responses/{identifier}/context", json=body, headers=headers()
        ).status_code
        == 202
    )
    evaluate_once(sessions)
    data = client.get("/v1/me/responses/" + identifier, headers=headers()).json()["data"]
    assert data["content"]["personal_response"]["label"] == "위급"
    assert data["content"]["personal_response"]["questions"] == []
    with sessions() as s:
        assert s.get(PolicyEntity, (scenario, "profile", "a")).body["mobility"] == "independent"
    body["base_revision"] = 1
    body["state"]["route_status"] = "open"
    assert (
        client.put(
            f"/v1/me/responses/{identifier}/context", json=body, headers=headers()
        ).status_code
        == 422
    )


@pytest.mark.parametrize(
    "offset,accepted", [(-300, True), (-300.001, False), (0.6, True), (30, True), (30.001, False)]
)
def test_location_clock_skew_has_bounded_validity(mobile, offset, accepted):
    client, sessions, scenario, _, headers = mobile
    with sessions.begin() as s:
        s.delete(s.get(PolicyEntity, (scenario, "location", "a")))
    captured = MOMENT + timedelta(seconds=offset)
    body = {
        "fix_id": "skew-fix",
        "installation_id": "phone",
        "latitude": 36,
        "longitude": 129,
        "accuracy_m": 10,
        "captured_at": captured.isoformat(),
    }
    response = client.put("/v1/me/location", json=body, headers=headers())
    if not accepted:
        assert response.status_code == 422
        assert response.json()["detail"] == "LOCATION_TIME_INVALID"
        with sessions() as s:
            assert s.get(PolicyEntity, (scenario, "location", "a")) is None
        return
    assert response.status_code == 200
    effective = min(captured, MOMENT)
    with sessions() as s:
        row = s.get(PolicyEntity, (scenario, "location", "a"))
        assert row.body["observed_at"] == effective.isoformat().replace("+00:00", "Z")
        assert row.body["expires_at"] == (effective + timedelta(minutes=5)).isoformat().replace(
            "+00:00", "Z"
        )
    assert (
        client.put("/v1/me/location", json=body, headers=headers()).json()["data"]
        == response.json()["data"]
    )


def test_clock_skew_location_cannot_replay_or_resurrect_after_deletion(mobile, monkeypatch):
    client, sessions, scenario, _, headers = mobile
    with sessions.begin() as s:
        s.delete(s.get(PolicyEntity, (scenario, "location", "a")))
    body = {
        "fix_id": "ahead-fix",
        "installation_id": "phone",
        "latitude": 36,
        "longitude": 129,
        "accuracy_m": 10,
        "captured_at": (MOMENT + timedelta(seconds=30)).isoformat(),
    }
    assert client.put("/v1/me/location", json=body, headers=headers()).status_code == 200
    monkeypatch.setattr(
        "bonghwajigi.api.mobile.evaluation_time", lambda scope: MOMENT + timedelta(seconds=2)
    )
    assert client.put("/v1/me/location", json=body, headers=headers()).status_code == 200
    body["fix_id"] = "same-capture-new-id"
    assert client.put("/v1/me/location", json=body, headers=headers()).status_code == 409
    assert client.delete("/v1/me/location", headers=headers()).status_code == 200
    assert client.put("/v1/me/location", json=body, headers=headers()).status_code == 409
    assert client.get("/v1/me/location", headers=headers()).json()["data"]["fix"] is None


@pytest.mark.parametrize(
    "offset,accepted", [(-300, True), (-300.001, False), (0.6, True), (30, True), (30.001, False)]
)
def test_context_clock_skew_has_bounded_validity(mobile, offset, accepted):
    client, sessions, scenario, _, headers = mobile
    set_environment(sessions, scenario, "H3")
    identifier = response_id(sessions, scenario, "a")
    observed = MOMENT + timedelta(seconds=offset)
    body = {
        "base_revision": 0,
        "observed_at": observed.isoformat(),
        "confirmation": "user_confirmed",
        "state": {"observed_hazard": "trapped"},
    }
    response = client.put(f"/v1/me/responses/{identifier}/context", json=body, headers=headers())
    if not accepted:
        assert response.status_code == 422
        assert response.json()["detail"] == "CONTEXT_TIME_INVALID"
        with sessions() as s:
            assert s.get(PolicyEntity, (scenario, "state", "fire/a")) is None
        return
    assert response.status_code == 202
    effective = min(observed, MOMENT)
    with sessions() as s:
        row = s.get(PolicyEntity, (scenario, "state", "fire/a"))
        assert row.body["observed_at"] == effective.isoformat().replace("+00:00", "Z")
        assert row.body["expires_at"] == (effective + timedelta(minutes=5)).isoformat().replace(
            "+00:00", "Z"
        )
    assert datetime.fromisoformat(response.json()["data"]["expires_at"]) == effective + timedelta(
        minutes=5
    )


def test_cursor_binding_pagination_expiry_and_response_links(mobile):
    client, sessions, scenario, settings, headers = mobile
    set_environment(sessions, scenario, "H2")
    first = client.get("/v1/me/updates", headers=headers()).json()["data"]
    cursor = first["next_cursor"]
    events = first["events"]
    identifier = response_id(sessions, scenario, "a")
    assert any(e["resource_id"] == identifier for e in events if e["type"] == "response.updated")
    assert (
        client.get("/v1/me/updates", params={"cursor": cursor}, headers=headers()).json()["data"][
            "events"
        ]
        == []
    )
    assert (
        client.get("/v1/me/updates", params={"cursor": cursor}, headers=headers("b")).status_code
        == 400
    )
    assert (
        client.get("/v1/me/profile", headers={"Authorization": "Bearer " + cursor}).status_code
        == 401
    )
    claims = jwt.decode(
        cursor,
        settings.jwt_secret.get_secret_value(),
        algorithms=["HS256"],
        audience="bonghwajigi-updates",
        issuer=settings.jwt_issuer,
    )
    claims["exp"] = now() - timedelta(seconds=1)
    expired = jwt.encode(claims, settings.jwt_secret.get_secret_value(), algorithm="HS256")
    assert (
        client.get("/v1/me/updates", params={"cursor": expired}, headers=headers()).status_code
        == 410
    )


def test_device_token_ownership_revocation_logout_and_feature_limits(mobile):
    client, sessions, scenario, _, headers = mobile
    body = {
        "platform": "android",
        "push_provider": "fcm",
        "push_token": "dummy-test-device-secret",
        "notification_permission": "granted",
        "app_version": "0.1",
    }
    result = client.put("/v1/me/devices/device-a", json=body, headers=headers())
    assert result.status_code == 200 and "dummy-test-device-secret" not in result.text
    assert client.put("/v1/me/devices/device-b", json=body, headers=headers("b")).status_code == 409
    token = headers()
    assert client.post("/v1/me/logout", headers=token).status_code == 200
    assert client.get("/v1/me/profile", headers=token).status_code == 401
    with sessions() as s:
        assert not any(
            d.enabled
            for d in s.scalars(
                select(Device).where(Device.scenario_id == scenario, Device.user_id == "a")
            ).all()
        )
    config = client.get("/v1/app-config", headers=headers("b")).json()["data"]
    assert config["features"]["impact_prediction"] is False
    assert config["features"]["voice_turns"] is False


def test_preferences_disable_push_but_keep_foreground_updates(mobile):
    client, sessions, scenario, _, headers = mobile
    result = client.put(
        "/v1/me/preferences",
        json={"base_revision": 0, "preferences": {"notifications_enabled": False}},
        headers=headers(),
    )
    assert result.status_code == 200
    set_environment(sessions, scenario, "H3")
    with sessions() as s:
        assert (
            s.scalar(
                select(Delivery.id).where(Delivery.scenario_id == scenario, Delivery.user_id == "a")
            )
            is None
        )
    assert client.get("/v1/me/updates", headers=headers()).json()["data"]["events"]


def test_official_alert_ids_are_user_bound_and_receipts_are_persisted(mobile):
    from test_three_stage import AREA, source

    from bonghwajigi.contracts.policy import AlertInput
    from bonghwajigi.policy.service import put_entity

    client, sessions, scenario, _, headers = mobile
    with sessions.begin() as s:
        put_entity(
            s,
            scenario,
            "alert",
            "fire/official",
            AlertInput(
                revision=1,
                state="issued",
                authority="합성 기관",
                severity="합성 등급",
                instruction_kind="evacuate",
                issued_at=MOMENT,
                expires_at=MOMENT + timedelta(minutes=5),
                area=AREA,
                raw_text="합성 공식 원문",
                source=source(),
                validity_confirmed=True,
            ),
            incident_id="fire",
        )
    alerts = client.get("/v1/me/alerts", headers=headers()).json()["data"]["items"]
    identifier = alerts[0]["id"]
    assert alerts[0]["original_text"] == "합성 공식 원문"
    assert alerts[0]["requires_qwen"] is False
    assert client.get("/v1/me/alerts/" + identifier, headers=headers("b")).status_code == 404
    body = {
        "alert_revision": 1,
        "installation_id": "phone",
        "event": "opened",
        "occurred_at": now().isoformat(),
    }
    first = client.post(f"/v1/me/alerts/{identifier}/receipts", json=body, headers=headers())
    repeated = client.post(f"/v1/me/alerts/{identifier}/receipts", json=body, headers=headers())
    assert first.status_code == 200 and first.json()["data"] == repeated.json()["data"]
    assert first.json()["data"]["meaning"] == "client_reported_only"


def test_alert_push_identifier_resolves_to_same_user_api_resource(mobile):
    from test_three_stage import AREA, source

    from bonghwajigi.contracts.policy import AlertInput
    from bonghwajigi.notifications.delivery import send_delivery
    from bonghwajigi.notifications.service import emit_change
    from bonghwajigi.policy.service import put_entity

    client, sessions, scenario, settings, headers = mobile
    with sessions.begin() as s:
        put_entity(
            s,
            scenario,
            "alert",
            "fire/push",
            AlertInput(
                revision=1,
                state="issued",
                authority="합성 기관",
                severity="합성 등급",
                instruction_kind="prepare",
                issued_at=MOMENT,
                expires_at=MOMENT + timedelta(minutes=5),
                area=AREA,
                raw_text="합성 알림 원문",
                source=source(),
                validity_confirmed=True,
            ),
            incident_id="fire",
        )
        for user in ["a", "b"]:
            emit_change(s, scenario, user, "alert", "fire/push", 1, urgency="high")
    with sessions() as s:
        rows = s.scalars(
            select(Delivery).where(
                Delivery.scenario_id == scenario,
                Delivery.resource_type == "alert",
                Delivery.resource_id == "fire/push",
            )
        ).all()
        identifiers = {row.user_id: row.id for row in rows}

    class CaptureSender:
        payload = None

        def send(self, token, payload, urgency):
            self.payload = payload
            return "simulated", None

    public_ids = []
    for user, identifier in identifiers.items():
        sender = CaptureSender()
        assert send_delivery(
            sessions,
            sender,
            identifier,
            resource_id_key=settings.jwt_secret.get_secret_value(),
        )
        payload = sender.payload
        assert payload["resource_type"] == "alert" and payload["revision"] == "1"
        public_id = payload["resource_id"]
        assert public_id != "fire/push" and "합성 알림 원문" not in str(payload)
        response = client.get("/v1/me/alerts/" + public_id, headers=headers(user))
        assert response.status_code == 200
        assert response.json()["data"]["original_text"] == "합성 알림 원문"
        other = "b" if user == "a" else "a"
        assert client.get("/v1/me/alerts/" + public_id, headers=headers(other)).status_code == 404
        with sessions() as s:
            assert s.get(Delivery, identifier).resource_id == "fire/push"
        public_ids.append(public_id)
    assert len(public_ids) == 2 and len(set(public_ids)) == 2
