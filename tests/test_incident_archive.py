from datetime import timedelta

import pytest
from pydantic import ValidationError
from sqlalchemy import select
from test_mobile_api import mobile as mobile
from test_mobile_api import response_id
from test_three_stage import AREA, MOMENT, source
from test_three_stage import mvp_db as mvp_db

from bonghwajigi.contracts.policy import AlertInput, IncidentInput, UrgentInput
from bonghwajigi.db.analysis_models import AnalysisJob
from bonghwajigi.db.delivery_models import Delivery
from bonghwajigi.db.policy_models import PolicyEntity
from bonghwajigi.events.urgent import process_urgent
from bonghwajigi.ingestion.service import accept_job
from bonghwajigi.notifications.delivery import send_delivery
from bonghwajigi.policy.service import evaluate_once, put_entity, register_observation


def queue_alert(sessions, scenario, incident, revision):
    payload = UrgentInput(
        incident_id="fire",
        alert_id="notice",
        incident=incident,
        alert=AlertInput(
            revision=revision,
            state="issued",
            authority="합성 기관",
            severity="합성 등급",
            issued_at=MOMENT,
            expires_at=MOMENT + timedelta(minutes=10),
            area=AREA,
            raw_text="보존해야 하는 합성 경보 원문",
            source=source(),
            validity_confirmed=True,
            instruction_kind="evacuate",
        ),
    )
    with sessions.begin() as s:
        job = accept_job(
            s, "urgent", scenario, f"alert-{revision}", {"payload": payload.model_dump(mode="json")}
        )
    assert process_urgent(sessions, job.job_id)
    return job.job_id


def test_archive_hides_feeds_preserves_records_and_blocks_resend(mobile):
    client, sessions, scenario, settings, headers = mobile
    with sessions() as s:
        incident = IncidentInput.model_validate(
            s.get(PolicyEntity, (scenario, "incident", "fire")).body
        )
    queue_alert(sessions, scenario, incident, 1)
    evaluate_once(sessions)
    identifier = response_id(sessions, scenario, "a")
    original = client.get("/v1/home", headers=headers()).json()["data"]
    assert len(original["nearby_disasters"]) == len(original["alerts"]) == 1
    alert_id = original["alerts"][0]["id"]
    before = client.get(f"/v1/me/responses/{identifier}", headers=headers()).json()["data"]
    assert before["content"]["personal_response"]["level"] == "act"
    with sessions.begin() as s:
        stored_alert = s.get(PolicyEntity, (scenario, "alert", "fire/notice")).body.copy()
        deliveries = s.scalars(select(Delivery.id).where(Delivery.scenario_id == scenario)).all()
        put_entity(
            s,
            scenario,
            "incident",
            "fire",
            incident.model_copy(update={"revision": 2, "feed_visibility": "archived"}),
            incident_id="fire",
        )
    # The feed and pending delivery stop immediately, before policy reevaluation.
    assert client.get("/v1/home", headers=headers()).json()["data"]["alerts"] == []
    assert client.get("/v1/disasters", headers=headers()).json()["data"]["items"] == []

    class NeverSend:
        def send(self, *_):
            raise AssertionError("archived incident must not be transmitted")

    for delivery in deliveries:
        assert send_delivery(
            sessions, NeverSend(), delivery, resource_id_key=settings.jwt_secret.get_secret_value()
        )
    with sessions() as s:
        assert all(s.get(Delivery, d).status == "superseded" for d in deliveries)
        assert s.get(PolicyEntity, (scenario, "alert", "fire/notice")).body == stored_alert
    evaluate_once(sessions)
    detail = client.get(f"/v1/me/alerts/{alert_id}", headers=headers()).json()["data"]
    assert detail["original_text"] == stored_alert["raw_text"]
    assert detail["issued_at"] == stored_alert["issued_at"]
    assert detail["status"] == "archived"  # not a fabricated official cancellation
    current = client.get(f"/v1/me/responses/{identifier}", headers=headers()).json()["data"]
    assert current["content"]["state"] == "archived"
    assert current["content"]["personal_response"]["level"] == "unknown"
    assert current["content"]["actions"] == []
    assert current["content"]["assistant_utterance"] is None
    history = client.get(f"/v1/me/responses/{identifier}/history", headers=headers()).json()[
        "data"
    ]["items"]
    assert history[0]["personal_response"]["level"] == "act"
    assert history[-1]["personal_response"]["level"] == "unknown"
    route = client.get(f"/v1/me/responses/{identifier}/route", headers=headers()).json()["data"]
    assert route["route"] is None and route["reason"] == "INCIDENT_ARCHIVED"
    context = client.put(
        f"/v1/me/responses/{identifier}/context",
        headers=headers(),
        json={
            "base_revision": 0,
            "observed_at": MOMENT.isoformat(),
            "confirmation": "user_confirmed",
            "state": {"can_move": True},
        },
    )
    assert context.status_code == 410
    turn = client.post(
        f"/v1/me/responses/{identifier}/text-turns",
        headers=headers(),
        json={
            "client_turn_id": "after-archive",
            "text": "혼자 이동할 수 있어요",
            "base_response_revision": current["revision"],
            "base_context_revision": 0,
        },
    )
    assert turn.status_code == 410

    # Delayed/new queue input can preserve its alert record but cannot unarchive or resend.
    new_job = queue_alert(sessions, scenario, incident.model_copy(update={"revision": 3}), 2)
    with sessions.begin() as s:
        assert s.get(AnalysisJob, new_job).result["matched_users"] == 0
        assert (
            s.get(PolicyEntity, (scenario, "incident", "fire")).body["feed_visibility"]
            == "archived"
        )
        assert s.get(PolicyEntity, (scenario, "alert", "fire/notice")).revision == 2
        register_observation(
            s,
            "late-analysis",
            {
                "scenario_id": scenario,
                "origin": "synthetic",
                "payload": {
                    "text": "늦게 도착한 기록",
                    "search_query": "산불",
                    "as_of": MOMENT,
                    "source": source(),
                    "policy_context": {
                        "incident_id": "fire",
                        "incident_revision": 3,
                        "expires_at": MOMENT + timedelta(minutes=10),
                        "area": AREA,
                    },
                },
            },
        )
        assert s.get(PolicyEntity, (scenario, "incident", "fire")).revision == 2
        assert len(
            s.scalars(select(Delivery.id).where(Delivery.scenario_id == scenario)).all()
        ) == len(deliveries)


@pytest.mark.parametrize("origin", ["historical_replay", "collected_sample"])
def test_archive_cannot_masquerade_as_official_incident_cancellation(origin):
    with pytest.raises(ValidationError, match="합성 사건"):
        IncidentInput(
            revision=1,
            origin=origin,
            feed_visibility="archived",
            title="원본",
            observed_at=MOMENT,
            expires_at=MOMENT + timedelta(minutes=10),
            area=AREA,
            sources=[source()],
        )
