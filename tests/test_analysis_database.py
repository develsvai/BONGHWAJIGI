import os
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import delete, func, select

from bonghwajigi.common.config import Settings
from bonghwajigi.contracts.analysis import RetrievalDocument, Source
from bonghwajigi.db.analysis_models import AnalysisJob, AnalysisOutbox, DocumentChunk
from bonghwajigi.db.session import session_factory
from bonghwajigi.ingestion.service import IngestionConflict, accept_job
from bonghwajigi.retrieval.embedding import EmbeddingError
from bonghwajigi.retrieval.pipeline import run_job
from bonghwajigi.workers.outbox import dispatch_once


@pytest.fixture
def database():
    url = os.environ.get("BONGHWA_TEST_DATABASE_URL")
    if not url:
        pytest.skip("실제 PostgreSQL 검사는 BONGHWA_TEST_DATABASE_URL로 활성화")
    settings = Settings(
        database_url=url,
        embedding_revision="test-revision",
        web_search_enabled=False,
        retrieval_top_k=5,
    )
    sessions = session_factory(settings)
    scenario = "test-" + uuid4().hex
    try:
        yield sessions, settings, scenario
    finally:
        with sessions.begin() as session:
            ids = select(AnalysisJob.id).where(AnalysisJob.scenario_id.like(scenario + "%"))
            session.execute(delete(AnalysisOutbox).where(AnalysisOutbox.job_id.in_(ids)))
            session.execute(delete(AnalysisJob).where(AnalysisJob.scenario_id.like(scenario + "%")))
            session.execute(
                delete(DocumentChunk).where(DocumentChunk.scenario_id.like(scenario + "%"))
            )
        sessions.kw["bind"].dispose()


class Embedder:
    def __init__(self, fail=False):
        self.calls, self.fail = 0, fail

    def encode(self, texts, input_type):
        self.calls += 1
        if self.fail:
            raise EmbeddingError("EMBEDDING_UNAVAILABLE")
        return [[1.0] + [0.0] * 1023 for text in texts]


class NoWeb:
    def search(self, *args):
        raise AssertionError("이 테스트에서는 웹 검색 비활성")


def document(scenario, identifier="doc", valid_until=None):
    moment = datetime(2026, 10, 31, 0, tzinfo=UTC)
    return RetrievalDocument(
        mode="simulation",
        scenario_id=scenario,
        document_id=identifier,
        origin="synthetic",
        text="합성 시연 자료이며 실제 행동 지침이 아닙니다.",
        source=Source(
            title="시연",
            url="https://example.invalid/" + identifier,
            published_at=moment,
            collected_at=moment,
        ),
        valid_from=moment,
        valid_until=valid_until,
    )


def event(scenario, identifier="event"):
    moment = "2026-10-31T01:00:00Z"
    return {
        "mode": "simulation",
        "scenario_id": scenario,
        "event_id": identifier,
        "origin": "synthetic",
        "queue": "analysis",
        "payload": {
            "text": "합성 산불 관측 시연",
            "search_query": "시연",
            "as_of": moment,
            "source": {
                "title": "시연",
                "url": "https://example.invalid/event",
                "published_at": moment,
                "collected_at": moment,
            },
        },
    }


def submit(sessions, scenario, kind, identifier, body):
    with sessions.begin() as session:
        return accept_job(session, kind, scenario, identifier, body)


def test_receiver_atomic_idempotency_and_conflict(database):
    sessions, settings, scenario = database
    body = event(scenario)
    first = submit(sessions, scenario, "analysis", "event", body)
    duplicate = submit(sessions, scenario, "analysis", "event", body)
    assert duplicate.duplicate and first.job_id == duplicate.job_id
    with pytest.raises(IngestionConflict):
        submit(sessions, scenario, "analysis", "event", {**body, "origin": "historical_replay"})
    with sessions() as session:
        assert (
            session.scalar(
                select(func.count())
                .select_from(AnalysisOutbox)
                .where(AnalysisOutbox.job_id == first.job_id)
            )
            == 1
        )


def test_outbox_failed_broker_keeps_durable_work(database):
    sessions, settings, scenario = database
    job = submit(sessions, scenario, "analysis", "event", event(scenario))

    class Broker:
        def send_task(self, *args, **kwargs):
            raise ConnectionError()

    assert dispatch_once(sessions, Broker()) == 0
    with sessions() as session:
        assert session.get(AnalysisJob, job.job_id).status == "queued"
        row = session.scalar(select(AnalysisOutbox).where(AnalysisOutbox.job_id == job.job_id))
        assert row.dispatch_count == 0 and row.error_code == "BROKER_UNAVAILABLE"

    class RecoveredBroker:
        def __init__(self):
            self.sent = []

        def send_task(self, *args, **kwargs):
            self.sent.append((args, kwargs))

    with sessions.begin() as session:
        row = session.scalar(select(AnalysisOutbox).where(AnalysisOutbox.job_id == job.job_id))
        row.next_dispatch_at = datetime.now(UTC) - timedelta(seconds=1)
    recovered = RecoveredBroker()
    assert dispatch_once(sessions, recovered) == 1
    assert recovered.sent[0][1]["args"] == [job.job_id]


def test_database_retrieval_isolates_scenarios_expiry_and_duplicate_delivery(database):
    sessions, settings, scenario = database
    encoder = Embedder()
    for doc in [
        document(scenario),
        document(scenario + "other", "other"),
        document(scenario, "expired", datetime(2026, 10, 31, 0, 30, tzinfo=UTC)),
    ]:
        accepted = submit(
            sessions, doc.scenario_id, "document", doc.document_id, doc.model_dump(mode="json")
        )
        run_job(accepted.job_id, sessions, encoder, NoWeb(), settings)
    accepted = submit(sessions, scenario, "analysis", "event", event(scenario))
    assert (
        run_job(accepted.job_id, sessions, encoder, NoWeb(), settings)["status"] == "ready_for_qwen"
    )
    calls = encoder.calls
    assert run_job(accepted.job_id, sessions, encoder, NoWeb(), settings)["duplicate"]
    assert encoder.calls == calls
    with sessions() as session:
        result = session.get(AnalysisJob, accepted.job_id).result
        assert result["qwen_invoked"] is False
        assert [r["document_id"] for r in result["retrieved_evidence"]] == ["doc"]


def test_embedding_retry_does_not_create_false_handoff(database):
    sessions, settings, scenario = database
    accepted = submit(sessions, scenario, "analysis", "event", event(scenario))
    result = run_job(accepted.job_id, sessions, Embedder(fail=True), NoWeb(), settings)
    assert result["status"] == "retry"
    with sessions() as session:
        assert session.get(AnalysisJob, accepted.job_id).result is None
    assert (
        run_job(accepted.job_id, sessions, Embedder(), NoWeb(), settings)["status"]
        == "ready_for_qwen"
    )
    with sessions() as session:
        result = session.get(AnalysisJob, accepted.job_id).result
        assert result["warnings"] == ["NO_RETRIEVED_EVIDENCE"]


def test_future_and_old_model_documents_are_excluded(database):
    sessions, settings, scenario = database
    old = settings.model_copy(update={"embedding_revision": "old-model"})
    doc = document(scenario, "old-model-document")
    job = submit(sessions, scenario, "document", "old-model", doc.model_dump(mode="json"))
    run_job(job.job_id, sessions, Embedder(), NoWeb(), old)
    future = document(scenario, "future")
    future.valid_from = datetime(2026, 11, 1, tzinfo=UTC)
    job = submit(sessions, scenario, "document", "future", future.model_dump(mode="json"))
    run_job(job.job_id, sessions, Embedder(), NoWeb(), settings)
    job = submit(sessions, scenario, "analysis", "event", event(scenario))
    run_job(job.job_id, sessions, Embedder(), NoWeb(), settings)
    with sessions() as session:
        assert not session.get(AnalysisJob, job.job_id).result["retrieved_evidence"]


def test_unavailable_web_preserves_stored_evidence_as_partial(database):
    sessions, settings, scenario = database
    doc = document(scenario)
    job = submit(sessions, scenario, "document", "doc", doc.model_dump(mode="json"))
    run_job(job.job_id, sessions, Embedder(), NoWeb(), settings)

    class OfflineWeb:
        def search(self, *args):
            return [], {"status": "unavailable", "result_count": 0}

    job = submit(sessions, scenario, "analysis", "event", event(scenario))
    run_job(
        job.job_id,
        sessions,
        Embedder(),
        OfflineWeb(),
        settings.model_copy(update={"web_search_enabled": True}),
    )
    with sessions() as session:
        result = session.get(AnalysisJob, job.job_id).result
        assert result["retrieval_status"] == "partial" and result["retrieved_evidence"]
        assert result["warnings"] == ["WEB_SEARCH_UNAVAILABLE"]


def test_internal_api_accepts_analysis_and_keeps_scope_and_auth(database, monkeypatch):
    from fastapi.testclient import TestClient

    from bonghwajigi.api.app import create_app

    sessions, settings, scenario = database
    monkeypatch.setenv("BONGHWA_DATABASE_URL", settings.database_url.get_secret_value())
    monkeypatch.setenv("BONGHWA_BROKER_URL", "redis://127.0.0.1:16379/0")
    monkeypatch.setenv("BONGHWA_SERVICE_TOKEN", "unit-test-token")
    monkeypatch.setenv("BONGHWA_ANALYSIS_ENABLED", "true")
    headers = {"Authorization": "Bearer unit-test-token"}
    body = event(scenario)
    with TestClient(create_app()) as client:
        assert client.post("/internal/v1/scenario-events", json=body).status_code == 401
        response = client.post("/internal/v1/scenario-events", json=body, headers=headers)
        assert response.status_code == 202
        job_id = response.json()["job_id"]
        assert client.post("/internal/v1/scenario-events", json=body, headers=headers).json()[
            "duplicate"
        ]
        assert (
            client.get(
                f"/internal/v1/scenarios/{scenario}-other/analysis-jobs/{job_id}", headers=headers
            ).status_code
            == 404
        )
        body["payload"]["text"] = "같은 식별자의 다른 본문"
        assert (
            client.post("/internal/v1/scenario-events", json=body, headers=headers).status_code
            == 409
        )
