import json
import os
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from bonghwajigi.common.config import Settings
from bonghwajigi.contracts.analysis import AnalysisInput, Source
from bonghwajigi.contracts.policy import (
    AlertInput,
    ClockInput,
    GuidanceInput,
    IncidentInput,
    LocationInput,
    PredictionInput,
    ProfileInput,
    RuleSetInput,
)
from bonghwajigi.db.analysis_models import AnalysisJob, AnalysisOutbox, now
from bonghwajigi.db.policy_models import (
    PolicyEntity,
    PolicyIntegration,
    PolicyProjection,
    PolicyScope,
    PolicySnapshot,
)
from bonghwajigi.db.session import session_factory
from bonghwajigi.ingestion.service import IngestionConflict, accept_job
from bonghwajigi.integration.service import IntegrationError
from bonghwajigi.policy.integration import integrate_once
from bonghwajigi.policy.service import (
    evaluate_once,
    projection_view,
    put_clock,
    put_entity,
    register_observation,
)

MOMENT = datetime(2026, 10, 31, 10, tzinfo=UTC)
AREA = {"west": 128.0, "east": 130.0, "south": 35.0, "north": 37.0}


def source():
    return Source(
        title="합성 시연",
        url="https://example.invalid/policy",
        published_at=MOMENT - timedelta(days=1),
        collected_at=MOMENT,
        verified=False,
    )


@pytest.fixture
def policy_db(monkeypatch):
    url = os.environ.get("BONGHWA_TEST_DATABASE_URL")
    if not url:
        pytest.skip("정책 루프 검사는 실제 PostgreSQL 설정이 필요합니다.")
    settings = Settings(
        database_url=url,
        service_token="policy-test-only",
        analysis_enabled=True,
        policy_enabled=True,
        broker_url="redis://127.0.0.1:16379/0",
    )
    sessions = session_factory(settings)
    scenario = "policy-test-" + uuid4().hex
    with sessions.begin() as session:
        put_clock(session, scenario, ClockInput(revision=1, evaluation_at=MOMENT))
    monkeypatch.setattr("bonghwajigi.api.app.Settings", lambda: settings)
    from bonghwajigi.api.app import create_app

    with TestClient(create_app()) as client:
        client.headers["Authorization"] = "Bearer policy-test-only"
        yield sessions, scenario, client
    with sessions.begin() as session:
        projections = select(PolicyProjection.id).where(PolicyProjection.scenario_id == scenario)
        session.execute(delete(PolicySnapshot).where(PolicySnapshot.projection_id.in_(projections)))
        session.execute(delete(PolicyProjection).where(PolicyProjection.scenario_id == scenario))
        session.execute(delete(PolicyIntegration).where(PolicyIntegration.scenario_id == scenario))
        session.execute(delete(PolicyEntity).where(PolicyEntity.scenario_id == scenario))
        session.execute(delete(PolicyScope).where(PolicyScope.scenario_id == scenario))
        jobs = select(AnalysisJob.id).where(AnalysisJob.scenario_id == scenario)
        session.execute(delete(AnalysisOutbox).where(AnalysisOutbox.job_id.in_(jobs)))
        session.execute(delete(AnalysisJob).where(AnalysisJob.scenario_id == scenario))
    sessions.kw["bind"].dispose()


def seed(db):
    sessions, scenario, _ = db
    with sessions.begin() as session:
        for user, profile in {
            "a": {},
            "b": {"mobility_assistance": True},
            "c": {"children_accompanying": True},
        }.items():
            put_entity(
                session,
                scenario,
                "profile",
                user,
                ProfileInput(revision=1, **profile),
                user_id=user,
            )
            put_entity(
                session,
                scenario,
                "location",
                user,
                LocationInput(
                    revision=1,
                    latitude=36,
                    longitude=129,
                    accuracy_m=10,
                    observed_at=MOMENT,
                    expires_at=MOMENT + timedelta(minutes=10),
                ),
                user_id=user,
            )
        put_entity(
            session,
            scenario,
            "incident",
            "fire",
            IncidentInput(
                revision=1,
                origin="synthetic",
                title="합성 산불",
                area=AREA,
                observed_at=MOMENT,
                expires_at=MOMENT + timedelta(hours=1),
                sources=[source()],
            ),
            incident_id="fire",
        )
        rules = []
        for index, condition in enumerate(
            ["related", "mobility_assistance", "children_accompanying"]
        ):
            put_entity(
                session,
                scenario,
                "guidance",
                condition,
                GuidanceInput(
                    revision=1,
                    review_state="simulation_only",
                    text="[시연] " + condition,
                    source=source(),
                    valid_from=MOMENT - timedelta(days=1),
                    expires_at=MOMENT + timedelta(hours=1),
                ),
            )
            rules.append(
                {
                    "action_id": condition,
                    "when": condition,
                    "guidance_id": condition,
                    "priority": index + 1,
                }
            )
        put_entity(
            session,
            scenario,
            "rules",
            "active",
            RuleSetInput(
                revision=1,
                review_state="simulation_only",
                rules=rules,
            ),
        )
    evaluate_once(sessions)


def view(db, user="a"):
    sessions, scenario, _ = db
    with sessions() as session:
        row = session.scalar(
            select(PolicyProjection).where(
                PolicyProjection.scenario_id == scenario,
                PolicyProjection.user_id == user,
            )
        )
        return projection_view(session, row)


def action_ids(result):
    return {item["action_id"] for item in result["content"]["actions"]}


def test_three_users_personalized_and_no_change_sweep_does_not_append_history(policy_db):
    seed(policy_db)
    sessions, _, _ = policy_db
    assert action_ids(view(policy_db, "a")) == {"related"}
    assert action_ids(view(policy_db, "b")) == {"related", "mobility_assistance"}
    assert action_ids(view(policy_db, "c")) == {"related", "children_accompanying"}
    before = view(policy_db)
    evaluate_once(sessions, wall_time=now() + timedelta(seconds=40))
    assert view(policy_db)["revision"] == before["revision"]
    assert before["content"]["personal_response"]["level"] == "unknown"
    assert before["content"]["notification"]["dispatched"] is False


def test_profile_update_targets_one_user_and_same_level_can_change_actions(policy_db):
    seed(policy_db)
    sessions, scenario, _ = policy_db
    before = {user: view(policy_db, user)["revision"] for user in "abc"}
    with sessions.begin() as session:
        put_entity(
            session,
            scenario,
            "profile",
            "b",
            ProfileInput(
                revision=2,
                mobility_assistance=True,
                children_accompanying=True,
            ),
            user_id="b",
        )
    evaluate_once(sessions)
    assert view(policy_db, "a")["revision"] == before["a"]
    assert view(policy_db, "c")["revision"] == before["c"]
    assert view(policy_db, "b")["revision"] == before["b"] + 1
    assert len(action_ids(view(policy_db, "b"))) == 3


def test_location_outside_and_expiration_do_not_claim_safe(policy_db):
    seed(policy_db)
    sessions, scenario, _ = policy_db
    with sessions.begin() as session:
        put_entity(
            session,
            scenario,
            "location",
            "a",
            LocationInput(
                revision=2,
                latitude=34,
                longitude=127,
                accuracy_m=10,
                observed_at=MOMENT,
                expires_at=MOMENT + timedelta(minutes=10),
            ),
            user_id="a",
        )
    assert view(policy_db)["pending_update"]
    assert not action_ids(view(policy_db))
    evaluate_once(sessions)
    assert view(policy_db)["content"]["state"] == "outside_scope"
    assert not action_ids(view(policy_db))
    with sessions.begin() as session:
        put_clock(
            session, scenario, ClockInput(revision=2, evaluation_at=MOMENT + timedelta(minutes=11))
        )
    # 재평가 전 조회도 이미 만료된 행동을 내보내지 않는다.
    assert view(policy_db, "b")["pending_update"]
    assert not action_ids(view(policy_db, "b"))
    evaluate_once(sessions)
    assert view(policy_db, "b")["content"]["state"] == "needs_refresh"
    assert view(policy_db, "b")["content"]["personal_response"]["level"] == "unknown"


def test_periodic_wall_clock_expiration_without_new_input(policy_db):
    seed(policy_db)
    sessions, scenario, _ = policy_db
    with sessions.begin() as session:
        put_clock(session, scenario, ClockInput(revision=2, evaluation_at=None))
    evaluate_once(sessions, wall_time=MOMENT)
    revision = view(policy_db)["revision"]
    evaluate_once(sessions, wall_time=MOMENT + timedelta(minutes=11))
    assert view(policy_db)["revision"] == revision + 1
    assert view(policy_db)["content"]["relevance"]["status"] == "unknown"


def test_uncertain_location_and_draft_guidance_never_get_actions(policy_db):
    seed(policy_db)
    sessions, scenario, _ = policy_db
    with sessions.begin() as session:
        put_entity(
            session,
            scenario,
            "location",
            "a",
            LocationInput(
                revision=2,
                latitude=36,
                longitude=128,
                accuracy_m=100,
                observed_at=MOMENT,
                expires_at=MOMENT + timedelta(minutes=10),
            ),
            user_id="a",
        )
        guide = GuidanceInput.model_validate(
            session.get(
                PolicyEntity,
                (
                    scenario,
                    "guidance",
                    "related",
                ),
            ).body
        ).model_copy(update={"revision": 2, "review_state": "draft"})
        put_entity(session, scenario, "guidance", "related", guide)
    evaluate_once(sessions)
    assert view(policy_db)["content"]["relevance"]["status"] == "uncertain"
    assert not action_ids(view(policy_db))
    assert "related" not in action_ids(view(policy_db, "b"))


def test_low_or_unavailable_prediction_preserves_alert_original_and_level_pending(policy_db):
    seed(policy_db)
    sessions, scenario, _ = policy_db
    with sessions.begin() as session:
        put_entity(
            session,
            scenario,
            "alert",
            "fire/notice",
            AlertInput(
                revision=1,
                state="issued",
                authority="합성 기관",
                severity="심각",
                area=AREA,
                raw_text="[합성 시연] 공식 원문 보존 검사",
                source=source(),
                issued_at=MOMENT,
                expires_at=MOMENT + timedelta(hours=1),
            ),
            incident_id="fire",
        )
        put_entity(
            session,
            scenario,
            "prediction",
            "fire",
            PredictionInput(
                revision=1,
                status="simulation",
                probability=0.01,
                model_id="synthetic",
                model_revision="test",
                target="simulation-only",
                area=AREA,
                observed_at=MOMENT,
                expires_at=MOMENT + timedelta(minutes=5),
            ),
            incident_id="fire",
        )
    evaluate_once(sessions)
    content = view(policy_db)["content"]
    assert content["official_alerts"][0]["severity"] == "심각"
    assert content["prediction"]["probability"] == 0.01
    assert not content["prediction"]["used_for_response_level"]
    assert content["personal_response"]["level"] == "unknown"
    with sessions.begin() as session:
        put_entity(
            session,
            scenario,
            "prediction",
            "fire",
            PredictionInput(
                revision=2,
                status="unavailable",
                model_id="synthetic",
                model_revision="test",
                target="simulation-only",
                area=AREA,
                observed_at=MOMENT,
                expires_at=MOMENT + timedelta(minutes=5),
            ),
            incident_id="fire",
        )
    evaluate_once(sessions)
    assert view(policy_db)["content"]["prediction"]["probability"] is None
    assert (
        view(policy_db)["content"]["official_alerts"][0]["raw_text"]
        == content["official_alerts"][0]["raw_text"]
    )


def test_api_auth_scope_idempotency_reverse_revision_and_meeting_fields(policy_db):
    seed(policy_db)
    _, scenario, client = policy_db
    path = f"/internal/v1/policy/scenarios/{scenario}"
    response = client.put(path + "/users/a/profile", json={"revision": 1})
    assert response.status_code == 202 and response.json()["duplicate"]
    assert (
        client.put(
            path + "/users/a/profile", json={"revision": 1, "mobility_assistance": True}
        ).status_code
        == 409
    )
    assert client.put(path + "/users/a/profile", json={"revision": 2}).status_code == 202
    assert client.put(path + "/users/a/profile", json={"revision": 1}).status_code == 409
    assert client.get(path + "other/users/a/plans/fire").status_code == 404
    assert (
        client.put(
            path + "/rules", json={"revision": 2, "review_state": "approved", "rules": []}
        ).status_code
        == 422
    )
    assert (
        client.put(
            path + "/rules",
            json={"revision": 2, "review_state": "simulation_only", "rules": [], "level": 4},
        ).status_code
        == 422
    )
    assert client.get(path + "/users/a/plans/fire/history").json()["items"]
    client.headers.pop("Authorization")
    assert client.get(path + "/users/a/plans/fire").status_code == 401


def prepare_job(db, event_id="observation", incident_revision=2):
    sessions, scenario, _ = db
    payload = AnalysisInput(
        text="합성 산불 관측 자료로 출처와 발표 시각을 확인합니다.",
        search_query="합성 시연",
        as_of=MOMENT,
        source=source(),
        policy_context={
            "incident_id": "fire",
            "incident_revision": incident_revision,
            "expires_at": MOMENT + timedelta(hours=1),
            "area": AREA,
        },
    ).model_dump(mode="json")
    event = {
        "mode": "simulation",
        "scenario_id": scenario,
        "event_id": event_id,
        "origin": "synthetic",
        "queue": "analysis",
        "payload": payload,
    }
    with sessions.begin() as session:
        accepted = accept_job(session, "analysis", scenario, event_id, event)
        register_observation(session, accepted.job_id, event)
        job = session.get(AnalysisJob, accepted.job_id)
        job.status = "ready_for_qwen"
        job.result = {
            "mode": "simulation",
            "stage": "ready_for_qwen",
            "qwen_invoked": False,
            "scenario_id": scenario,
            "event": payload,
            "retrieved_evidence": [],
        }
    return accepted.job_id


class Generator:
    def __init__(self, callback=None, fail=False):
        self.calls, self.callback, self.fail = 0, callback, fail

    def generate(self, prompt):
        self.calls += 1
        if self.callback:
            self.callback()
        if self.fail:
            raise IntegrationError("GENERATION_HTTP_503")
        assert "mobility_assistance" not in prompt
        return {
            "text": json.dumps(
                {
                    "summary": "당시 합성 산불 관측 자료가 입력됐다.",
                    "facts": [
                        {
                            "evidence_id": "observation-source",
                            "quote": "합성 산불 관측 자료로 출처와 발표 시각을 확인합니다.",
                        }
                    ],
                }
            )
        }


def test_qwen_integration_is_durable_idempotent_and_rejoins_plan(policy_db):
    seed(policy_db)
    sessions, _, _ = policy_db
    job_id = prepare_job(policy_db)
    generator = Generator()
    assert integrate_once(sessions, generator)
    assert not integrate_once(sessions, generator) and generator.calls == 1
    evaluate_once(sessions)
    assert view(policy_db)["content"]["context"]["status"] == "complete"
    assert not view(policy_db)["content"]["context"]["template_fallback"]
    with sessions() as session:
        assert session.get(PolicyIntegration, job_id).prompt


def test_qwen_failure_does_not_block_profile_plan_and_recovery(policy_db):
    seed(policy_db)
    sessions, scenario, _ = policy_db
    job_id = prepare_job(policy_db)

    def concurrent_update():
        with sessions.begin() as session:
            put_entity(
                session,
                scenario,
                "profile",
                "a",
                ProfileInput(
                    revision=2,
                    mobility_assistance=True,
                ),
                user_id="a",
            )
        evaluate_once(sessions)
        assert "mobility_assistance" in action_ids(view(policy_db))

    integrate_once(sessions, Generator(callback=concurrent_update, fail=True))
    evaluate_once(sessions)
    assert view(policy_db)["content"]["context"]["template_fallback"]
    assert action_ids(view(policy_db))
    with sessions.begin() as session:
        task = session.get(PolicyIntegration, job_id)
        assert task.status == "retry"
        task.next_attempt_at = now() - timedelta(seconds=1)
    integrate_once(sessions, Generator())
    evaluate_once(sessions)
    assert view(policy_db)["content"]["context"]["status"] == "complete"


def test_late_qwen_completion_cannot_overwrite_new_observation(policy_db):
    seed(policy_db)
    sessions, _, _ = policy_db
    old = prepare_job(policy_db)
    integrate_once(
        sessions,
        Generator(
            callback=lambda: prepare_job(
                policy_db,
                event_id="new-observation",
                incident_revision=3,
            )
        ),
    )
    with sessions() as session:
        assert session.get(PolicyIntegration, old).status == "superseded"
    evaluate_once(sessions)
    assert view(policy_db)["content"]["input_versions"]["incident:fire"] == 3
    assert view(policy_db)["content"]["context"]["summary"] is None


def test_reverse_clock_and_duplicate_observation_revision_rejected(policy_db):
    seed(policy_db)
    sessions, scenario, _ = policy_db
    prepare_job(policy_db)
    with pytest.raises(IngestionConflict):
        prepare_job(policy_db, event_id="different-same-revision")
    with sessions.begin() as session, pytest.raises(ValueError):
        put_clock(
            session, scenario, ClockInput(revision=2, evaluation_at=MOMENT - timedelta(seconds=1))
        )


def test_guidance_update_and_expiry_reapply_without_deciding_level(policy_db):
    seed(policy_db)
    sessions, scenario, _ = policy_db
    before = view(policy_db)
    with sessions.begin() as session:
        current = session.get(PolicyEntity, (scenario, "guidance", "related"))
        payload = GuidanceInput.model_validate(current.body).model_copy(
            update={
                "revision": 2,
                "text": "[시연] 수정된 기본 참고 지침",
                "expires_at": MOMENT + timedelta(seconds=30),
            }
        )
        put_entity(session, scenario, "guidance", "related", payload)
    evaluate_once(sessions)
    updated = view(policy_db)
    assert updated["revision"] == before["revision"] + 1
    assert updated["content"]["actions"][0]["text"] == "[시연] 수정된 기본 참고 지침"
    assert updated["content"]["personal_response"]["level"] == "unknown"
    with sessions.begin() as session:
        put_clock(
            session, scenario, ClockInput(revision=2, evaluation_at=MOMENT + timedelta(seconds=31))
        )
    evaluate_once(sessions)
    assert "related" not in action_ids(view(policy_db))


def test_integration_retry_limit_and_expired_lease_recovery(policy_db):
    seed(policy_db)
    sessions, scenario, client = policy_db
    job_id = prepare_job(policy_db)
    with sessions.begin() as session:
        task = session.get(PolicyIntegration, job_id)
        task.status, task.lease_id = "processing", "expired-lease"
        task.next_attempt_at = now() - timedelta(seconds=1)
    for attempt in range(3):
        assert integrate_once(sessions, Generator(fail=True))
        with sessions.begin() as session:
            task = session.get(PolicyIntegration, job_id)
            assert task.attempts == attempt + 1
            task.next_attempt_at = now() - timedelta(seconds=1)
    with sessions() as session:
        assert session.get(PolicyIntegration, job_id).status == "failed"
    path = f"/internal/v1/policy/scenarios/{scenario}/integrations/{job_id}/retry"
    assert client.post(path).status_code == 202
    assert integrate_once(sessions, Generator())
    assert client.post(path).status_code == 409
    evaluate_once(sessions)
    assert view(policy_db)["content"]["context"]["status"] == "complete"


def test_failed_user_evaluation_does_not_block_others_and_periodic_retry(policy_db, monkeypatch):
    seed(policy_db)
    sessions, scenario, _ = policy_db
    from bonghwajigi.policy import service

    original = service.evaluate
    with sessions.begin() as session:
        for user in "ab":
            put_entity(
                session,
                scenario,
                "profile",
                user,
                ProfileInput(
                    revision=2,
                    children_accompanying=True,
                ),
                user_id=user,
            )

    def fail_one(session, row, moment):
        if row.user_id == "a":
            raise ValueError("simulated")
        return original(session, row, moment)

    monkeypatch.setattr(service, "evaluate", fail_one)
    evaluate_once(sessions)
    assert view(policy_db)["error_code"] == "POLICY_EVALUATION_FAILED"
    assert "children_accompanying" in action_ids(view(policy_db, "b"))
    monkeypatch.setattr(service, "evaluate", original)
    evaluate_once(sessions, wall_time=now() + timedelta(seconds=31))
    assert view(policy_db)["error_code"] is None
    assert "children_accompanying" in action_ids(view(policy_db))


def test_alert_lookup_escapes_wildcards_and_cancelled_record_is_retained(policy_db):
    seed(policy_db)
    _, scenario, client = policy_db
    base = f"/internal/v1/policy/scenarios/{scenario}"
    notice = AlertInput(
        revision=1,
        state="issued",
        authority="합성 기관",
        severity="시연 등급",
        issued_at=MOMENT,
        expires_at=MOMENT + timedelta(minutes=20),
        raw_text="[시연] 발령 기록",
        source=source(),
    ).model_dump(mode="json")
    assert client.put(base + "/incidents/fireX/alerts/a", json=notice).status_code == 202
    assert client.get(base + "/incidents/fire_/alerts").json()["records"] == []
    assert client.put(base + "/incidents/fire/alerts/a", json=notice).status_code == 202
    assert (
        client.put(
            base + "/incidents/fire/alerts/a",
            json={
                **notice,
                "revision": 2,
                "state": "cancelled",
            },
        ).status_code
        == 202
    )
    evaluate_once(policy_db[0])
    content = view(policy_db)["content"]
    assert content["official_alerts"][0]["record_status"] == "cancelled"
    assert content["official_alerts"][0]["raw_text"] == notice["raw_text"]
    assert content["personal_response"]["level"] == "unknown"
