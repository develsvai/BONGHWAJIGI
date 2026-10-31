import os
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import delete, select

from bonghwajigi.common.config import Settings
from bonghwajigi.contracts.policy import (
    AlertInput,
    ClockInput,
    CurrentStateInput,
    EnvironmentInput,
    IncidentInput,
    LocationInput,
    ProfileInput,
    RouteInput,
    UrgentInput,
)
from bonghwajigi.db.analysis_models import AnalysisJob, AnalysisOutbox, now
from bonghwajigi.db.delivery_models import ChangeSequence, Delivery, Device, UserChange
from bonghwajigi.db.policy_models import (
    PolicyEntity,
    PolicyIntegration,
    PolicyProjection,
    PolicyScope,
    PolicySnapshot,
)
from bonghwajigi.db.session import session_factory
from bonghwajigi.events.urgent import process_urgent
from bonghwajigi.ingestion.service import accept_job
from bonghwajigi.notifications.delivery import send_delivery
from bonghwajigi.notifications.providers import PushError, SimulationSender
from bonghwajigi.policy.service import evaluate_once, put_clock, put_entity
from bonghwajigi.policy.three_stage import bootstrap, decide

MOMENT = datetime(2026, 10, 31, 12, tzinfo=UTC)
AREA = {"west": 128.0, "east": 130.0, "south": 35.0, "north": 37.0}


def source():
    return {
        "title": "합성 시연 출처",
        "url": "https://example.invalid/mvp",
        "published_at": MOMENT,
        "collected_at": MOMENT,
        "verified": True,
    }


@pytest.mark.parametrize(
    ("band", "mobility", "helper", "expected"),
    [
        ("H1", "independent", False, "prepare"),
        ("H2", "independent", False, "prepare"),
        ("H2", "needs_time", False, "act"),
        ("H3", "independent", False, "act"),
        ("H3", "requires_help", False, "request_assistance"),
        ("H3", "requires_help", True, "act"),
    ],
)
def test_user_specific_levels(band, mobility, helper, expected):
    response, _ = decide(
        {"mobility": mobility},
        {"helper_present": helper},
        {"hazard_band": band},
        {},
        [],
        None,
        True,
    )
    assert response["level"] == expected
    assert response["label"] in {"경고", "대피", "위급"}


def test_urgent_does_not_require_a_question_and_fear_does_not_mean_trapped():
    response, _ = decide({}, {"observed_hazard": "trapped"}, {}, {}, [], None, False)
    assert response["level"] == "request_assistance" and response["questions"] == []
    response, _ = decide({}, {"observed_hazard": "fear"}, {}, {}, [], None, True)
    assert response["level"] == "act"
    assert response["automatic_emergency_call"] is False


def test_unknown_is_not_blocked_and_deescalation_requires_confirmation():
    previous = {"personal_response": {"level": "act"}}
    response, _ = decide(
        {"mobility": "independent"},
        {},
        {"hazard_band": "H1"},
        {"status": "unknown"},
        [],
        previous,
        True,
    )
    assert response["level"] == "act"
    response, _ = decide(
        {}, {"deescalation_confirmed": True}, {"hazard_band": "H1"}, {}, [], previous, True
    )
    assert response["level"] == "prepare"


@pytest.fixture
def mvp_db():
    url = os.environ.get("BONGHWA_TEST_DATABASE_URL")
    if not url:
        pytest.skip("실제 PostgreSQL 설정 필요")
    sessions = session_factory(Settings(database_url=url))
    scenario = "three-stage-" + uuid4().hex
    with sessions.begin() as s:
        put_clock(s, scenario, ClockInput(revision=1, evaluation_at=MOMENT))
        bootstrap(s, scenario, MOMENT)
        put_entity(
            s,
            scenario,
            "incident",
            "fire",
            IncidentInput(
                revision=1,
                origin="synthetic",
                title="합성 산불",
                observed_at=MOMENT,
                expires_at=MOMENT + timedelta(hours=1),
                area=AREA,
                sources=[source()],
            ),
            incident_id="fire",
        )
        for user, mobility in [("a", "independent"), ("b", "needs_time"), ("c", "requires_help")]:
            put_entity(
                s,
                scenario,
                "profile",
                user,
                ProfileInput(revision=1, mobility=mobility),
                user_id=user,
            )
            put_entity(
                s,
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
            s.add(
                Device(
                    scenario_id=scenario,
                    user_id=user,
                    installation_id="phone",
                    provider="fcm",
                    token="simulation-device-" + user,
                    enabled=True,
                )
            )
    yield sessions, scenario
    with sessions.begin() as s:
        for model in (Delivery, Device, UserChange, ChangeSequence):
            s.execute(delete(model).where(model.scenario_id == scenario))
        pids = select(PolicyProjection.id).where(PolicyProjection.scenario_id == scenario)
        s.execute(delete(PolicySnapshot).where(PolicySnapshot.projection_id.in_(pids)))
        for model in (PolicyProjection, PolicyIntegration, PolicyEntity, PolicyScope):
            s.execute(delete(model).where(model.scenario_id == scenario))
        ids = select(AnalysisJob.id).where(AnalysisJob.scenario_id == scenario)
        s.execute(delete(AnalysisOutbox).where(AnalysisOutbox.job_id.in_(ids)))
        s.execute(delete(AnalysisJob).where(AnalysisJob.scenario_id == scenario))
    sessions.kw["bind"].dispose()


def set_environment(sessions, scenario, band, revision=1):
    with sessions.begin() as s:
        put_entity(
            s,
            scenario,
            "environment",
            "fire",
            EnvironmentInput(
                revision=revision,
                observed_at=MOMENT,
                expires_at=MOMENT + timedelta(minutes=10),
                hazard_band=band,
                source=source(),
                reason="합성 시연 구간",
            ),
            incident_id="fire",
        )
    evaluate_once(sessions)


def plans(sessions, scenario):
    with sessions() as s:
        return {
            p.user_id: p.content
            for p in s.scalars(
                select(PolicyProjection).where(PolicyProjection.scenario_id == scenario)
            ).all()
        }


def test_database_three_users_guides_and_targeted_state(mvp_db):
    sessions, scenario = mvp_db
    set_environment(sessions, scenario, "H2")
    result = plans(sessions, scenario)
    assert [result[u]["personal_response"]["level"] for u in "abc"] == ["prepare", "act", "act"]
    assert all(a["approved_policy"] for p in result.values() for a in p["actions"])
    set_environment(sessions, scenario, "H3", 2)
    assert plans(sessions, scenario)["c"]["personal_response"]["level"] == "request_assistance"
    with sessions.begin() as s:
        put_entity(
            s,
            scenario,
            "state",
            "fire/c",
            CurrentStateInput(
                revision=1,
                helper_present=True,
                can_move=True,
                observed_at=MOMENT,
                expires_at=MOMENT + timedelta(minutes=10),
            ),
            user_id="c",
            incident_id="fire",
        )
        put_entity(
            s,
            scenario,
            "route",
            "fire/c",
            RouteInput(
                revision=1,
                status="open",
                source=source(),
                reason="합성 통제 정보",
                observed_at=MOMENT,
                expires_at=MOMENT + timedelta(minutes=5),
            ),
            user_id="c",
            incident_id="fire",
        )
    evaluate_once(sessions)
    assert plans(sessions, scenario)["c"]["personal_response"]["level"] == "act"


def test_official_intake_independent_of_models_duplicate_and_cancel(mvp_db):
    sessions, scenario = mvp_db
    with sessions.begin() as s:
        incident = IncidentInput.model_validate(
            s.get(PolicyEntity, (scenario, "incident", "fire")).body
        )
        alert = AlertInput(
            revision=1,
            state="issued",
            authority="합성 기관",
            severity="합성 등급",
            issued_at=MOMENT,
            expires_at=MOMENT + timedelta(minutes=10),
            area=AREA,
            raw_text="합성 대피 안내",
            source=source(),
            validity_confirmed=True,
            instruction_kind="evacuate",
        )
        payload = UrgentInput(incident_id="fire", alert_id="notice", incident=incident, alert=alert)
        accepted = accept_job(
            s, "urgent", scenario, "warning", {"payload": payload.model_dump(mode="json")}
        )
    assert process_urgent(sessions, accepted.job_id)
    assert not process_urgent(sessions, accepted.job_id)
    evaluate_once(sessions)
    assert plans(sessions, scenario)["a"]["personal_response"]["level"] == "act"
    with sessions() as s:
        assert s.get(AnalysisJob, accepted.job_id).result["requires_qwen"] is False
        deliveries = s.scalars(
            select(Delivery).where(
                Delivery.scenario_id == scenario, Delivery.resource_type == "alert"
            )
        ).all()
        assert len(deliveries) == 3
        identifier = deliveries[0].id
    assert send_delivery(sessions, SimulationSender(), identifier)
    assert not send_delivery(sessions, SimulationSender(), identifier)
    with sessions() as s:
        assert s.get(Delivery, identifier).status == "simulated"
    with sessions.begin() as s:
        payload.alert = alert.model_copy(update={"revision": 2, "state": "cancelled"})
        cancelled = accept_job(
            s,
            "urgent",
            scenario,
            "warning-cancel",
            {
                "payload": payload.model_dump(mode="json"),
            },
        )
    process_urgent(sessions, cancelled.job_id)
    evaluate_once(sessions)
    with sessions() as s:
        notice = s.get(PolicyEntity, (scenario, "alert", "fire/notice"))
        assert notice.body["state"] == "cancelled"
        assert notice.body["raw_text"] == "합성 대피 안내"
        updates = s.scalars(
            select(Delivery).where(
                Delivery.scenario_id == scenario,
                Delivery.resource_type == "alert",
                Delivery.revision == 2,
            )
        ).all()
        assert len(updates) == 3 and all(d.urgency == "normal" for d in updates)


def test_delivery_retry_revocation_and_lease(mvp_db):
    sessions, scenario = mvp_db
    set_environment(sessions, scenario, "H3")
    with sessions() as s:
        row = s.scalar(select(Delivery).where(Delivery.scenario_id == scenario))
        identifier, device_id = row.id, row.device_id

    class Failing:
        def send(self, *args):
            raise PushError("NETWORK_UNCERTAIN", retryable=True)

    assert send_delivery(sessions, Failing(), identifier)
    with sessions.begin() as s:
        row = s.get(Delivery, identifier)
        assert row.status == "retry" and row.attempts == 1
        row.next_attempt_at = now() - timedelta(seconds=1)
        s.get(Device, device_id).enabled = False
    assert send_delivery(sessions, SimulationSender(), identifier)
    with sessions() as s:
        assert s.get(Delivery, identifier).status == "device_revoked"
