import json
from datetime import timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy import delete, select
from test_mobile_api import mobile as mobile
from test_mobile_api import response_id
from test_three_stage import MOMENT, set_environment
from test_three_stage import mvp_db as mvp_db

from bonghwajigi.api.interaction import route_data
from bonghwajigi.api.user_auth import issue_token
from bonghwajigi.common.config import Settings
from bonghwajigi.contracts.interaction import RouteData
from bonghwajigi.db.analysis_models import now
from bonghwajigi.db.app_models import AppSession, AppTextTurn
from bonghwajigi.db.policy_models import PolicyEntity
from bonghwajigi.policy.service import evaluate_once


class Generator:
    def __init__(self, value=None, callback=None):
        self.calls = 0
        self.prompts = []
        self.callback = callback
        self.value = value or {
            "intent": "status_update",
            "action_ids": [],
            "question": "helper_present",
            "changes": [{"field": "state.can_move", "value": False, "quote": "움직일 수 없어"}],
        }

    def generate(self, prompt):
        self.calls += 1
        self.prompts.append(prompt)
        if self.callback:
            self.callback()
        return {"text": json.dumps(self.value, ensure_ascii=False)}


def setup(mobile, generator=None):
    client, sessions, scenario, _, headers = mobile
    set_environment(sessions, scenario, "H2")
    identifier = response_id(sessions, scenario, "a")
    snapshot = client.get(f"/v1/me/responses/{identifier}", headers=headers()).json()["data"]
    client.app.state.dialogue_generator = generator or Generator()
    body = {
        "client_turn_id": "turn-1",
        "text": "지금 움직일 수 없어",
        "base_response_revision": snapshot["revision"],
        "base_context_revision": snapshot["user_context"]["revision"],
    }
    return identifier, body


@pytest.fixture
def real_sessions(mobile):
    _, sessions, scenario, settings, _ = mobile
    ids = [str(uuid4()), str(uuid4())]
    with sessions.begin() as s:
        for identifier in ids:
            s.add(
                AppSession(
                    id=identifier,
                    scenario_id=scenario,
                    user_id="a",
                    installation_id=identifier,
                    account_version=1,
                    refresh_digest="synthetic-refresh",
                    client_digest="synthetic-client",
                    expires_at=now() + timedelta(hours=1),
                )
            )
    yield (
        [
            {
                "Authorization": "Bearer "
                + issue_token(settings, "a", scenario, session_id=identifier)
            }
            for identifier in ids
        ],
        ids,
    )
    with sessions.begin() as s:
        s.execute(delete(AppSession).where(AppSession.id.in_(ids)))


def test_turn_and_proposal_cannot_cross_real_sessions(mobile, real_sessions):
    client, _, _, _, _ = mobile
    (first, second), _ = real_sessions
    identifier, body = setup(mobile)
    endpoint = f"/v1/me/responses/{identifier}"
    result = client.post(endpoint + "/text-turns", json=body, headers=first)
    assert result.status_code == 200
    proposal = result.json()["data"]["proposal"]
    assert client.get(endpoint + "/text-turns/turn-1", headers=second).status_code == 404
    assert client.post(endpoint + "/text-turns", json=body, headers=second).status_code == 404
    assert (
        client.put(
            endpoint + "/context",
            headers=second,
            json={
                "base_revision": proposal["base_revision"],
                "observed_at": MOMENT.isoformat(),
                "confirmation": "user_confirmed",
                "proposal_turn_id": "turn-1",
                "state": proposal["state"],
                "overrides": proposal["overrides"],
            },
        ).status_code
        == 404
    )


def test_session_revocation_during_generation_discards_turn(mobile, real_sessions):
    client, sessions, scenario, _, _ = mobile
    (first, _), (session_id, _) = real_sessions
    identifier, body = setup(mobile)

    def revoke():
        with sessions.begin() as s:
            s.get(AppSession, session_id).revoked_at = now()

    client.app.state.dialogue_generator = Generator(callback=revoke)
    assert (
        client.post(
            f"/v1/me/responses/{identifier}/text-turns", json=body, headers=first
        ).status_code
        == 401
    )
    with sessions() as s:
        turn = s.scalar(select(AppTextTurn).where(AppTextTurn.scenario_id == scenario))
        assert turn.status == "superseded" and turn.result is None


def test_turn_proposal_is_non_mutating_confirmed_and_policy_grounded(mobile):
    client, sessions, scenario, _, headers = mobile
    identifier, body = setup(mobile)
    endpoint = f"/v1/me/responses/{identifier}"
    result = client.post(endpoint + "/text-turns", json=body, headers=headers())
    assert result.status_code == 200, result.text
    data = result.json()["data"]
    assert data["turn_id"] == "turn-1" and data["status"] == "complete"
    assert data["assistant"]["source"] == "qwen_grounded"
    assert data["proposal"]["state"]["can_move"] is False
    assert data["proposal"]["requires_confirmation"] is True
    with sessions() as s:
        assert s.get(PolicyEntity, (scenario, "state", "fire/a")) is None
    assert client.get(endpoint + "/text-turns/turn-1", headers=headers()).json()["data"] == data
    confirmed = {
        "base_revision": data["proposal"]["base_revision"],
        "observed_at": MOMENT.isoformat(),
        "confirmation": "user_confirmed",
        "proposal_turn_id": "turn-1",
        "state": data["proposal"]["state"],
        "overrides": data["proposal"]["overrides"],
    }
    assert client.put(endpoint + "/context", json=confirmed, headers=headers()).status_code == 202
    evaluate_once(sessions)
    assert client.get(endpoint + "/text-turns/turn-1", headers=headers()).status_code == 409
    with sessions() as s:
        assert s.get(PolicyEntity, (scenario, "state", "fire/a")).body["can_move"] is False


def test_turn_ownership_revision_and_idempotency(mobile):
    client, _, _, _, headers = mobile
    generator = Generator()
    identifier, body = setup(mobile, generator)
    endpoint = f"/v1/me/responses/{identifier}/text-turns"
    assert client.post(endpoint, json=body).status_code == 401
    assert client.post(endpoint, json=body, headers=headers("b")).status_code == 404
    assert (
        client.post(
            endpoint, json={**body, "base_response_revision": 999}, headers=headers()
        ).status_code
        == 409
    )
    first = client.post(endpoint, json=body, headers=headers())
    assert (
        client.post(endpoint, json=body, headers=headers()).json()["data"] == first.json()["data"]
    )
    assert generator.calls == 1
    assert (
        client.post(endpoint, json={**body, "text": "다른 발언"}, headers=headers()).json()[
            "detail"
        ]
        == "IDEMPOTENCY_CONFLICT"
    )
    assert client.get(endpoint + "/turn-1", headers=headers("b")).status_code == 404


@pytest.mark.parametrize(
    "value",
    [
        {
            "intent": "status_update",
            "action_ids": [],
            "question": "",
            "changes": [{"field": "state.can_move", "value": False, "quote": "움직일 수 없어"}],
        },
        {
            "intent": "explain",
            "action_ids": ["invented-safe-route"],
            "question": "none",
            "changes": [],
        },
        {
            "intent": "status_update",
            "action_ids": [],
            "question": "none",
            "changes": [{"field": "state.can_move", "value": False, "quote": "없는 발언"}],
        },
        {
            "intent": "status_update",
            "action_ids": [],
            "question": "none",
            "changes": [{"field": "state.deescalation_confirmed", "value": True, "quote": "지금"}],
        },
        {
            "intent": "status_update",
            "action_ids": [],
            "question": "none",
            "changes": [{"field": "state.can_move", "value": "yes", "quote": "지금"}],
        },
    ],
)
def test_invalid_generation_uses_only_reviewed_policy_fallback(mobile, value):
    client, _, _, _, headers = mobile
    identifier, body = setup(mobile, Generator(value))
    data = client.post(
        f"/v1/me/responses/{identifier}/text-turns", json=body, headers=headers()
    ).json()["data"]
    assert data["assistant"]["source"] == "reviewed_policy_fallback"
    assert data["reason_code"] == "DIALOGUE_MODEL_OUTPUT_INVALID"
    assert data["proposal"] is None
    assert "invented" not in data["assistant"]["text"]


def test_model_may_omit_optional_followup_question(mobile):
    client, _, _, _, headers = mobile
    identifier, body = setup(
        mobile,
        Generator(
            {
                "intent": "status_update",
                "action_ids": [],
                "changes": [{"field": "state.can_move", "value": False, "quote": "움직일 수 없어"}],
            }
        ),
    )
    data = client.post(
        f"/v1/me/responses/{identifier}/text-turns", json=body, headers=headers()
    ).json()["data"]
    assert data["assistant"]["source"] == "qwen_grounded"
    assert data["proposal"]["state"]["can_move"] is False
    assert "곁에서" not in data["assistant"]["text"]


def test_generation_failure_uses_fixed_code_without_exception_contents(mobile):
    from bonghwajigi.integration.service import IntegrationError

    client, _, _, _, headers = mobile

    def fail():
        raise IntegrationError("private-diagnostic-content")

    identifier, body = setup(mobile, Generator(callback=fail))
    data = client.post(
        f"/v1/me/responses/{identifier}/text-turns", json=body, headers=headers()
    ).json()["data"]
    assert data["reason_code"] == "DIALOGUE_GENERATION_FAILED"
    assert data["proposal"] is None
    assert "private-diagnostic-content" not in json.dumps(data)


def test_generation_failure_falls_back_and_pending_other_request_is_bounded(mobile):
    client, _, _, _, headers = mobile
    identifier, body = setup(mobile)
    endpoint = f"/v1/me/responses/{identifier}/text-turns"
    observed = []

    def during_generation():
        status = client.get(endpoint + "/turn-1", headers=headers())
        observed.append(status.json()["data"]["status"])
        observed.append(client.post(endpoint, json=body, headers=headers()).json()["detail"])
        observed.append(
            client.post(
                endpoint, json={**body, "client_turn_id": "turn-2"}, headers=headers()
            ).json()["detail"]
        )
        raise TimeoutError()

    client.app.state.dialogue_generator = Generator(callback=during_generation)
    result = client.post(endpoint, json=body, headers=headers())
    assert result.status_code == 200
    assert result.json()["data"]["assistant"]["source"] == "reviewed_policy_fallback"
    assert observed == ["processing", "TURN_IN_PROGRESS", "CONVERSATION_BUSY"]


def test_proposal_preserves_current_state_and_normalized_mobility(mobile):
    client, sessions, _, _, headers = mobile
    identifier, _ = setup(mobile)
    endpoint = f"/v1/me/responses/{identifier}"
    assert (
        client.put(
            endpoint + "/context",
            headers=headers(),
            json={
                "base_revision": 0,
                "observed_at": MOMENT.isoformat(),
                "confirmation": "user_confirmed",
                "overrides": {"mobility": "needs_time"},
                "state": {"injured": True},
            },
        ).status_code
        == 202
    )
    evaluate_once(sessions)
    snapshot = client.get(endpoint, headers=headers()).json()["data"]
    body = {
        "client_turn_id": "preserved",
        "text": "지금 움직일 수 없어",
        "base_response_revision": snapshot["revision"],
        "base_context_revision": 1,
    }
    proposal = client.post(endpoint + "/text-turns", json=body, headers=headers()).json()["data"][
        "proposal"
    ]
    assert proposal["state"]["injured"] is True
    assert proposal["state"]["can_move"] is False
    assert proposal["overrides"]["mobility"] == "needs_time"
    assert proposal["state"]["deescalation_confirmed"] is False


def test_twenty_turns_limit_prevents_unbounded_storage_and_inference(mobile):
    client, sessions, scenario, _, headers = mobile
    generator = Generator()
    identifier, body = setup(mobile, generator)
    endpoint = f"/v1/me/responses/{identifier}/text-turns"
    for index in range(20):
        result = client.post(
            endpoint, json={**body, "client_turn_id": f"limit-{index}"}, headers=headers()
        )
        assert result.status_code == 200
    assert (
        client.post(
            endpoint, json={**body, "client_turn_id": "overflow"}, headers=headers()
        ).status_code
        == 429
    )
    assert generator.calls == 20
    with sessions() as s:
        assert (
            len(s.scalars(select(AppTextTurn).where(AppTextTurn.scenario_id == scenario)).all())
            == 20
        )


def test_concurrent_input_change_discards_result_and_proposal(mobile):
    client, sessions, scenario, _, headers = mobile
    identifier, body = setup(mobile)

    def changed_input():
        set_environment(sessions, scenario, "H3", revision=2)

    client.app.state.dialogue_generator = Generator(callback=changed_input)
    result = client.post(f"/v1/me/responses/{identifier}/text-turns", json=body, headers=headers())
    assert result.status_code == 409
    with sessions() as s:
        turn = s.scalar(select(AppTextTurn).where(AppTextTurn.scenario_id == scenario))
        assert turn.result is None
        assert turn.status == "superseded"
        assert s.get(PolicyEntity, (scenario, "state", "fire/a")) is None
    snapshot = client.get(f"/v1/me/responses/{identifier}", headers=headers()).json()["data"]
    client.app.state.dialogue_generator = Generator()
    retry = client.post(
        f"/v1/me/responses/{identifier}/text-turns",
        json={
            **body,
            "client_turn_id": "after-conflict",
            "base_response_revision": snapshot["revision"],
        },
        headers=headers(),
    )
    assert retry.status_code == 200


def test_logout_during_generation_cannot_publish(mobile):
    client, _, _, _, headers = mobile
    identifier, body = setup(mobile)
    client.app.state.dialogue_generator = Generator(
        callback=lambda: client.post("/v1/me/logout", headers=headers())
    )
    assert (
        client.post(
            f"/v1/me/responses/{identifier}/text-turns", json=body, headers=headers()
        ).status_code
        == 401
    )


def test_proposal_tamper_and_expiry_are_rejected(mobile):
    client, sessions, scenario, _, headers = mobile
    identifier, body = setup(mobile)
    endpoint = f"/v1/me/responses/{identifier}"
    data = client.post(endpoint + "/text-turns", json=body, headers=headers()).json()["data"]
    proposal = data["proposal"]
    confirm = {
        "base_revision": 0,
        "observed_at": MOMENT.isoformat(),
        "confirmation": "user_confirmed",
        "proposal_turn_id": "turn-1",
        "state": {**proposal["state"], "can_move": True},
        "overrides": proposal["overrides"],
    }
    assert (
        client.put(endpoint + "/context", json=confirm, headers=headers()).json()["detail"]
        == "PROPOSAL_MISMATCH"
    )
    with sessions.begin() as s:
        turn = s.scalar(select(AppTextTurn).where(AppTextTurn.scenario_id == scenario))
        turn.valid_until = MOMENT - timedelta(seconds=1)
    confirm["state"] = proposal["state"]
    assert client.put(endpoint + "/context", json=confirm, headers=headers()).status_code == 410
    assert client.get(endpoint + "/text-turns/turn-1", headers=headers()).status_code == 410


def test_history_has_no_private_profile_and_is_bounded(mobile):
    client, sessions, scenario, _, headers = mobile
    generator = Generator(
        {"intent": "explain", "action_ids": [], "question": "none", "changes": []}
    )
    identifier, body = setup(mobile, generator)
    endpoint = f"/v1/me/responses/{identifier}/text-turns"
    for index in range(5):
        assert (
            client.post(
                endpoint, json={**body, "client_turn_id": f"turn-{index}"}, headers=headers()
            ).status_code
            == 200
        )
    facts = json.loads(
        generator.prompts[-1]
        .split("<untrusted_dialogue_json>\n", 1)[1]
        .split("\n</untrusted_dialogue_json>", 1)[0]
    )
    assert len(facts["previous_turns"]) == 3
    assert "health_notes" not in facts and "display_name" not in facts
    with sessions.begin() as s:
        turns = s.scalars(select(AppTextTurn).where(AppTextTurn.scenario_id == scenario)).all()
        for turn in turns:
            turn.expires_at = now() - timedelta(seconds=1)
    assert (
        client.post(
            endpoint, json={**body, "client_turn_id": "after-expiry"}, headers=headers()
        ).status_code
        == 200
    )
    with sessions() as s:
        assert (
            len(s.scalars(select(AppTextTurn).where(AppTextTurn.scenario_id == scenario)).all())
            == 1
        )


def test_route_is_fixture_only_and_near_current_demo_location():
    settings = Settings(mode="simulation")
    actor = {"scenario_id": "mobile-demo", "sub": "a"}
    row = SimpleNamespace(incident_id="mobile-fire")
    incident = SimpleNamespace(
        revision=1,
        body={
            "origin": "synthetic",
            "observed_at": MOMENT.isoformat(),
            "expires_at": (MOMENT + timedelta(hours=1)).isoformat(),
        },
    )
    location = SimpleNamespace(
        revision=2,
        body={
            "latitude": 36.4,
            "longitude": 129.35,
            "accuracy_m": 10,
            "observed_at": MOMENT.isoformat(),
            "expires_at": (MOMENT + timedelta(minutes=5)).isoformat(),
        },
    )
    result = RouteData.model_validate(route_data(settings, actor, row, incident, location, MOMENT))
    assert result.status == "simulation" and result.route.operational_use is False
    assert result.route.geometry.coordinates[0] == (129.35, 36.4)
    assert result.route.input_versions["location:a"] == 2
    settings.mode = "live"
    assert route_data(settings, actor, row, incident, location, MOMENT)["route"] is None
    settings.mode = "simulation"
    for changed in ({"latitude": 37}, {"accuracy_m": 101}, {"expires_at": MOMENT.isoformat()}):
        other = SimpleNamespace(revision=2, body={**location.body, **changed})
        assert route_data(settings, actor, row, incident, other, MOMENT)["route"] is None
    incident.body["origin"] = "collected_sample"
    assert route_data(settings, actor, row, incident, location, MOMENT)["route"] is None
