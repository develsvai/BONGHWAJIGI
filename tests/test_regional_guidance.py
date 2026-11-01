import json
from datetime import timedelta
from types import SimpleNamespace

import pytest
from pydantic import ValidationError
from sqlalchemy import select
from test_analysis_database import Embedder, NoWeb
from test_mobile_api import mobile as mobile
from test_mobile_api import response_id
from test_mobile_interaction import Generator
from test_three_stage import AREA, MOMENT, set_environment, source
from test_three_stage import mvp_db as mvp_db

from bonghwajigi.api.interaction import route_data
from bonghwajigi.contracts.analysis import RegionalConditionsInput
from bonghwajigi.contracts.policy import CurrentStateInput, RouteInput
from bonghwajigi.contracts.routes import ReferenceRoute
from bonghwajigi.db.analysis_models import AnalysisJob
from bonghwajigi.db.delivery_models import UserChange
from bonghwajigi.db.policy_models import PolicyEntity
from bonghwajigi.policy.service import evaluate_once, put_entity
from bonghwajigi.retrieval.pipeline import run_job


def conditions(revision=1, **changes):
    return RegionalConditionsInput(
        region_id="test-region",
        revision=revision,
        origin="historical_replay",
        observed_at=MOMENT,
        original_observed_at=MOMENT - timedelta(days=600),
        expires_at=MOMENT + timedelta(minutes=10),
        area=AREA,
        sources=[source()],
        **{"forest_nearby": True, "dry_warning": True, "fog_observed": None, **changes},
    )


def store_conditions(sessions, scenario, value):
    with sessions.begin() as s:
        put_entity(s, scenario, "regional_conditions", value.region_id, value)


def home(mobile, user="a"):
    client, _, _, _, headers = mobile
    response = client.get("/v1/home", headers=headers(user))
    assert response.status_code == 200, response.text
    return response.json()["data"]


def test_regional_evidence_location_expiry_and_no_guessed_fog(mobile):
    _, sessions, scenario, _, _ = mobile
    assert home(mobile)["today_guidance"]["status"] == "unavailable"
    store_conditions(sessions, scenario, conditions())
    data = home(mobile)["today_guidance"]
    assert data["status"] == "available"
    assert [item["id"] for item in data["items"]] == ["mvp-regional-dry"]
    assert data["items"][0]["original_observed_at"].startswith("2025-03-10")
    assert data["location_input_revision"] == 1
    assert data["items"][0]["evidence"][0]["verified"]
    with sessions() as s:
        assert (
            s.scalar(
                select(UserChange).where(
                    UserChange.scenario_id == scenario, UserChange.resource_type == "home"
                )
            )
            is not None
        )
    store_conditions(sessions, scenario, conditions(2, forest_nearby=None, fog_observed=True))
    assert [item["id"] for item in home(mobile)["today_guidance"]["items"]] == ["mvp-regional-fog"]
    store_conditions(sessions, scenario, conditions(3, forest_nearby=None))
    assert home(mobile)["today_guidance"]["status"] == "unavailable"
    # A known dry warning without known nearby forest cannot claim nearby dry forest.
    with sessions.begin() as s:
        location = s.get(PolicyEntity, (scenario, "location", "a"))
        location.body = {**location.body, "expires_at": (MOMENT - timedelta(seconds=1)).isoformat()}
    store_conditions(sessions, scenario, conditions(4, fog_observed=True))
    assert home(mobile)["today_guidance"]["items"] == []


@pytest.mark.parametrize("invalid", ["outside", "expired", "unverified"])
def test_regional_unusable_evidence_is_not_rendered(mobile, invalid):
    _, sessions, scenario, _, _ = mobile
    value = conditions()
    if invalid == "outside":
        value.area.west, value.area.east = 120, 121
    elif invalid == "expired":
        value.observed_at = MOMENT - timedelta(minutes=10)
        value.expires_at = MOMENT - timedelta(seconds=1)
    else:
        value.sources[0].verified = False
    store_conditions(sessions, scenario, value)
    assert home(mobile)["today_guidance"]["items"] == []


def test_regional_recency_compares_instants_not_offset_strings(mobile):
    from datetime import timezone

    _, sessions, scenario, _, _ = mobile
    older = conditions(forest_nearby=None, fog_observed=True)
    older.region_id = "older"
    older.observed_at = (MOMENT - timedelta(minutes=2)).astimezone(timezone(timedelta(hours=9)))
    older.sources[0].published_at = MOMENT - timedelta(days=1)
    newer = conditions()
    newer.region_id = "newer"
    newer.observed_at = MOMENT - timedelta(minutes=1)
    newer.sources[0].published_at = MOMENT - timedelta(days=1)
    store_conditions(sessions, scenario, older)
    store_conditions(sessions, scenario, newer)
    assert [item["id"] for item in home(mobile)["today_guidance"]["items"]] == ["mvp-regional-dry"]


def test_preparation_two_slots_and_potential_child_does_not_set_current_state(mobile):
    client, sessions, scenario, _, headers = mobile
    for user, profile, title in [
        ("a", {"mobility": "independent", "dependents": ["child"]}, "어린이 비상용품 준비"),
        ("b", {"mobility": "walking_aid"}, "이동 보조기구 점검"),
    ]:
        assert (
            client.put(
                "/v1/me/profile",
                headers=headers(user),
                json={
                    "base_revision": 0,
                    "profile": profile,
                },
            ).status_code
            == 200
        )
        cards = home(mobile, user)["preparations"]["items"]
        assert [card["kind"] for card in cards] == ["common", "personal"]
        assert cards[1]["title"] == title
    with sessions() as s:
        a = s.get(PolicyEntity, (scenario, "profile", "a")).body
        b = s.get(PolicyEntity, (scenario, "profile", "b")).body
        assert a["child_registered"] and not a["children_accompanying"]
        assert a["mobility"] == "independent"
        assert b["mobility"] == "needs_time" and b["assistive_device"]
    set_environment(sessions, scenario, "H2")
    snap = client.get(
        "/v1/me/responses/" + response_id(sessions, scenario, "a"), headers=headers()
    ).json()["data"]
    assert snap["content"]["personal_response"]["level"] == "prepare"
    assert snap["user_context"]["data"] is None
    assert snap["content"]["personal_response"]["questions"] == ["지금 아이와 함께 계신가요?"]
    assert not any(a["action_id"] == "mvp-act-child" for a in snap["content"]["actions"])


def test_same_fire_confirms_child_and_solo_mobility_without_profile_inference(mobile):
    client, sessions, scenario, _, headers = mobile
    for user, profile in [
        ("a", {"mobility": "independent", "dependents": ["child"]}),
        ("b", {"mobility": "walking_aid"}),
    ]:
        client.put(
            "/v1/me/profile", headers=headers(user), json={"base_revision": 0, "profile": profile}
        )
        with sessions.begin() as s:
            put_entity(
                s,
                scenario,
                "route",
                "fire/" + user,
                RouteInput(
                    revision=1,
                    status="blocked" if user == "a" else "open",
                    source=source(),
                    reason="Explicit synthetic user route context",
                    observed_at=MOMENT,
                    expires_at=MOMENT + timedelta(minutes=5),
                ),
                user_id=user,
                incident_id="fire",
            )
    set_environment(sessions, scenario, "H3")
    for user, text, changes, expected, question in [
        (
            "a",
            "지금 아이랑 있습니다.",
            [{"field": "state.child_present", "value": True, "quote": "아이랑 있습니다"}],
            "request_assistance",
            "지금 아이와 함께 계신가요?",
        ),
        (
            "b",
            "혼자라 이동할 수 있어요.",
            [
                {"field": "state.alone_now", "value": "yes", "quote": "혼자라"},
                {"field": "state.can_move", "value": True, "quote": "이동할 수 있어요"},
            ],
            "act",
            "보조기구를 사용해 혼자 이동할 수 있나요?",
        ),
    ]:
        path = "/v1/me/responses/" + response_id(sessions, scenario, user)
        before = client.get(path, headers=headers(user)).json()["data"]
        assert before["content"]["personal_response"]["level"] == expected
        assert before["content"]["personal_response"]["questions"] == [question]
        client.app.state.dialogue_generator = Generator(
            {
                "intent": "status_update",
                "action_ids": [],
                "question": "none",
                "changes": changes,
            }
        )
        turn = client.post(
            path + "/text-turns",
            headers=headers(user),
            json={
                "client_turn_id": "confirm-" + user,
                "text": text,
                "base_response_revision": before["revision"],
                "base_context_revision": 0,
            },
        )
        assert turn.status_code == 200, turn.text
        proposal = turn.json()["data"]["proposal"]
        assert proposal is not None
        assert (
            client.get(path, headers=headers(user)).json()["data"]["user_context"]["revision"] == 0
        )
        accepted = client.put(
            path + "/context",
            headers=headers(user),
            json={
                "base_revision": 0,
                "observed_at": MOMENT.isoformat(),
                "confirmation": "user_confirmed",
                "proposal_turn_id": "confirm-" + user,
                "state": proposal["state"],
                "overrides": proposal["overrides"],
            },
        )
        assert accepted.status_code == 202, accepted.text
        evaluate_once(sessions)
        after = client.get(path, headers=headers(user)).json()["data"]
        assert after["content"]["personal_response"]["level"] == expected
        assert after["content"]["personal_response"]["questions"] == []
        state = after["user_context"]["data"]
        if user == "a":
            assert state["child_present"] is True and state["can_move"] is None
            assert "mvp-assist-child" in [a["action_id"] for a in after["content"]["actions"]]
        else:
            assert state["alone_now"] == "yes" and state["can_move"] is True
            assert state["helper_present"] is False and state["mobility_override"] is None
            assert "mvp-act-aid" in [a["action_id"] for a in after["content"]["actions"]]


def reference():
    return ReferenceRoute(
        id="reference-1",
        label="참고 경로",
        geometry={"coordinates": [(129.0, 36.0), (129.001, 36.001)]},
        start={"name": "시작", "longitude": 129.0, "latitude": 36.0},
        destination={"name": "참고 지점", "longitude": 129.001, "latitude": 36.001},
        steps=[
            {
                "sequence": 1,
                "text": "참고 지점",
                "point": {"longitude": 129.001, "latitude": 36.001},
            }
        ],
        bounds={"west": 128.99, "east": 129.01, "south": 35.99, "north": 36.01},
    )


def test_reference_route_is_per_user_bounded_and_never_shows_blocked_route(mobile):
    _, sessions, scenario, settings, _ = mobile
    with sessions() as s:
        incident = s.get(PolicyEntity, (scenario, "incident", "fire"))
        location = s.get(PolicyEntity, (scenario, "location", "a"))
        value = RouteInput(
            revision=1,
            status="open",
            source=source(),
            reason="synthetic reference",
            observed_at=MOMENT,
            expires_at=MOMENT + timedelta(minutes=2),
            reference_route=reference(),
        )
        record = SimpleNamespace(body=value.model_dump(mode="json"), revision=1, entity_id="fire/a")

        def get():
            return route_data(
                settings,
                {"scenario_id": scenario, "sub": "a"},
                SimpleNamespace(incident_id="fire"),
                incident,
                location,
                MOMENT,
                record,
            )

        data = get()
        assert data["status"] == "simulation" and data["route"]["operational_use"] is False
        assert data["route"]["input_versions"]["route:fire/a"] == 1
        record.body = {**record.body, "status": "blocked"}
        assert get()["route"] is None and get()["reason"] == "ROUTE_BLOCKED"
        record.body = {**record.body, "status": "unknown"}
        assert get()["route"] is None
        record.body = {**record.body, "status": "open", "expires_at": MOMENT.isoformat()}
        assert get()["route"] is None
    with pytest.raises(ValidationError):
        ReferenceRoute.model_validate({**reference().model_dump(), "operational_use": True})
    with pytest.raises(ValidationError):
        CurrentStateInput(
            revision=1,
            observed_at=MOMENT,
            expires_at=MOMENT + timedelta(minutes=1),
            alone_now="yes",
            child_present=True,
        )


def test_analysis_queue_registers_region_only_after_success(mobile):
    client, sessions, scenario, settings, _ = mobile
    settings.embedding_revision = "test-revision"
    settings.web_search_enabled = False
    payload = {
        "text": "공식 자료 기반 지역 관측",
        "search_query": "관측",
        "as_of": MOMENT.isoformat(),
        "source": source(),
        "regional_conditions": conditions().model_dump(mode="json"),
    }
    payload = json.loads(json.dumps(payload, default=str))
    result = client.post(
        "/internal/v1/scenario-events",
        headers={"Authorization": "Bearer service-test-token"},
        json={
            "mode": "simulation",
            "scenario_id": scenario,
            "event_id": "regional-input",
            "origin": "historical_replay",
            "queue": "analysis",
            "payload": payload,
        },
    )
    assert result.status_code == 202, result.text
    identifier = result.json()["job_id"]
    assert home(mobile)["today_guidance"]["items"] == []
    assert (
        run_job(identifier, sessions, Embedder(fail=True), NoWeb(), settings)["status"] == "retry"
    )
    assert home(mobile)["today_guidance"]["items"] == []
    assert (
        run_job(identifier, sessions, Embedder(), NoWeb(), settings)["status"] == "ready_for_qwen"
    )
    assert home(mobile)["today_guidance"]["items"][0]["id"] == "mvp-regional-dry"
    with sessions() as s:
        job = s.get(AnalysisJob, identifier)
        assert job.result["qwen_invoked"] is False
        assert s.get(PolicyEntity, (scenario, "regional_conditions", "test-region")).revision == 1
    assert run_job(identifier, sessions, Embedder(), NoWeb(), settings)["duplicate"]
    payload["regional_conditions"]["fog_observed"] = True
    conflict = client.post(
        "/internal/v1/scenario-events",
        headers={"Authorization": "Bearer service-test-token"},
        json={
            "mode": "simulation",
            "scenario_id": scenario,
            "event_id": "regional-conflict",
            "origin": "historical_replay",
            "queue": "analysis",
            "payload": payload,
        },
    )
    assert conflict.status_code == 202
    failed = run_job(conflict.json()["job_id"], sessions, Embedder(), NoWeb(), settings)
    assert failed["status"] == "failed" and failed["attempts"] == 1
    assert failed["error_code"] == "REGIONAL_OBSERVATION_CONFLICT_OR_INVALID"
    assert [item["id"] for item in home(mobile)["today_guidance"]["items"]] == ["mvp-regional-dry"]
