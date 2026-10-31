from datetime import timedelta
from uuid import uuid4

import pytest
from sqlalchemy import delete, select
from test_mobile_api import mobile as mobile
from test_mobile_api import response_id
from test_three_stage import MOMENT, set_environment
from test_three_stage import mvp_db as mvp_db

from bonghwajigi.db.analysis_models import now
from bonghwajigi.db.app_models import AppMutation, AppSession
from bonghwajigi.db.policy_models import PolicyEntity
from bonghwajigi.policy.service import evaluate_once


def registration():
    return {
        "installation_id": str(uuid4()),
        "consent": {
            "version": "internal-demo-v1",
            "service": True,
            "privacy": True,
            "location": True,
        },
    }


@pytest.fixture
def installation(mobile):
    client, sessions, scenario, settings, _ = mobile
    settings.app_registration_enabled = True
    settings.app_registration_scenario = scenario
    response = client.post("/v1/auth/installations", json=registration())
    assert response.status_code == 201
    tokens = response.json()["data"]
    yield client, sessions, scenario, settings, tokens
    with sessions.begin() as s:
        s.execute(delete(AppSession).where(AppSession.scenario_id == scenario))


def auth(tokens):
    return {"Authorization": "Bearer " + tokens["access_token"]}


def test_registration_is_opt_in_simulation_and_requires_explicit_consents(mobile):
    client, _, _, settings, _ = mobile
    assert client.get("/v1/auth/config").json()["data"]["registration_enabled"] is False
    assert client.post("/v1/auth/installations", json=registration()).status_code == 404
    settings.app_registration_enabled = True
    settings.mode = "live"
    assert client.post("/v1/auth/installations", json=registration()).status_code == 404
    settings.mode = "simulation"
    body = registration()
    body["consent"]["privacy"] = False
    assert client.post("/v1/auth/installations", json=body).status_code == 422


def test_refresh_rotates_and_reuse_commits_revocation(installation):
    client, sessions, _, _, initial = installation
    assert client.get("/v1/me/profile", headers=auth(initial)).status_code == 200
    renewed = client.post("/v1/auth/refresh", json={"refresh_token": initial["refresh_token"]})
    assert renewed.status_code == 200
    current = renewed.json()["data"]
    assert current["refresh_token"] != initial["refresh_token"]
    assert client.get("/v1/me/profile", headers=auth(current)).status_code == 200
    assert (
        client.post(
            "/v1/auth/refresh", json={"refresh_token": initial["refresh_token"]}
        ).status_code
        == 401
    )
    assert client.get("/v1/me/profile", headers=auth(current)).status_code == 401
    assert (
        client.post(
            "/v1/auth/refresh", json={"refresh_token": current["refresh_token"]}
        ).status_code
        == 401
    )
    with sessions() as s:
        row = s.get(AppSession, current["session_id"])
        assert row.revoked_at is not None
        assert current["refresh_token"].split(".", 1)[1] != row.refresh_digest


def test_expired_session_and_logout_deny_access_and_refresh(installation):
    client, sessions, _, _, tokens = installation
    with sessions.begin() as s:
        s.get(AppSession, tokens["session_id"]).expires_at = now() - timedelta(seconds=1)
    assert client.get("/v1/me/profile", headers=auth(tokens)).status_code == 401
    assert (
        client.post("/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}).status_code
        == 401
    )


def test_logout_invalidates_refresh_and_old_access(installation):
    client, _, _, _, tokens = installation
    assert client.post("/v1/me/logout", headers=auth(tokens)).status_code == 200
    assert client.get("/v1/me/profile", headers=auth(tokens)).status_code == 401
    assert (
        client.post("/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}).status_code
        == 401
    )


def test_registration_rate_limit_does_not_leak_existing_accounts(installation):
    client, _, _, settings, _ = installation
    settings.app_registration_hourly_limit = 1
    result = client.post("/v1/auth/installations", json=registration())
    assert result.status_code == 429 and result.headers["Retry-After"] == "3600"
    assert "access_token" not in result.text


def test_profile_preparations_and_sensitive_consent_withdrawal(installation):
    client, sessions, scenario, _, tokens = installation
    headers = {**auth(tokens), "Idempotency-Key": "profile-with-consent"}
    body = {
        "base_revision": 1,
        "profile": {
            "display_name": "통합시연",
            "age_band": "60_plus",
            "mobility": "walking_aid",
            "emergency_contact": "합성 연락처",
            "usual_place": "합성 장소",
            "building_floor": "2층",
            "health_consent": True,
            "health_notes": "합성 의료 메모",
        },
    }
    saved = client.put("/v1/me/profile", headers=headers, json=body)
    assert saved.status_code == 200
    assert saved.json()["data"]["profile"]["display_name"] == "통합시연"
    cards = client.get("/v1/me/preparations", headers=auth(tokens)).json()["data"]
    assert cards["profile_revision"] == 2
    assert len(cards["items"]) == 2
    assert cards["items"][1]["reason_code"] == "MOBILITY_PREPARATION"
    assert all(item["source"]["verified"] for item in cards["items"])
    assert "합성 의료 메모" not in str(cards)
    with sessions() as s:
        assert "합성 의료 메모" not in str(
            s.get(PolicyEntity, (scenario, "profile", tokens["user_id"])).body
        )
    body["base_revision"] = 2
    body["profile"].update(health_consent=False, health_notes="")
    assert client.put("/v1/me/profile", headers=auth(tokens), json=body).status_code == 200
    with sessions() as s:
        prior = s.scalars(
            select(AppMutation).where(
                AppMutation.scenario_id == scenario,
                AppMutation.user_id == tokens["user_id"],
            )
        ).all()
        assert all("합성 의료 메모" not in str(r.result) for r in prior)
    assert client.delete("/v1/me/profile", headers=auth(tokens)).status_code == 200
    assert client.get("/v1/me/profile", headers=auth(tokens)).json()["data"]["profile"] == {}


def test_invalid_health_input_is_rejected_without_echoing_sensitive_text(installation):
    client, _, _, _, tokens = installation
    result = client.put(
        "/v1/me/profile",
        headers=auth(tokens),
        json={
            "base_revision": 1,
            "profile": {"health_consent": False, "health_notes": "비공개 합성 문장"},
        },
    )
    assert result.status_code == 422
    assert "비공개 합성 문장" not in result.text
    assert "input" not in result.json()["detail"][0]


def test_home_has_independent_preparations_and_avoid_guidance(installation):
    client, _, _, _, tokens = installation
    home = client.get("/v1/home", headers=auth(tokens))
    assert home.status_code == 200
    data = home.json()["data"]
    assert data["preparations"]["status"] == "available"
    assert len(data["preparations"]["items"]) == 2
    assert len(data["basic_rules"]["avoid"]) == 2
    assert isinstance(data["alerts"], list)


def test_confirmed_stairs_change_updates_level_and_server_authored_text(mobile):
    client, sessions, scenario, _, headers = mobile
    set_environment(sessions, scenario, "H2")
    identifier = response_id(sessions, scenario, "a")
    path = "/v1/me/responses/" + identifier
    before = client.get(path, headers=headers()).json()["data"]
    assert before["content"]["personal_response"]["label"] == "경고"
    result = client.put(
        path + "/context",
        headers=headers(),
        json={
            "base_revision": 0,
            "observed_at": MOMENT.isoformat(),
            "confirmation": "user_confirmed",
            "overrides": {"stairs": "difficult"},
        },
    )
    assert result.status_code == 202
    pending = client.get(path, headers=headers()).json()["data"]
    assert pending["content"]["assistant_utterance"] is None
    evaluate_once(sessions)
    after = client.get(path, headers=headers()).json()["data"]
    assert after["user_context"]["revision"] == 1
    assert after["content"]["personal_response"]["label"] == "대피"
    assert after["content"]["assistant_utterance"]["source"] == "reviewed_policy_text"
    assert after["content"]["prediction"]["probability"] is None
