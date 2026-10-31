import json
import os
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient

from bonghwajigi.api.app import create_app as create_api
from bonghwajigi.gpu_api.app import create_app as create_gpu


def test_readiness_failure_is_sanitized_and_can_recover():
    from fastapi import FastAPI

    from bonghwajigi.common.health import health_router

    available = False

    def infrastructure():
        if not available:
            raise RuntimeError("postgresql://private-password@private-host")
        return {"database": "connected", "broker": "connected"}

    app = FastAPI()
    app.include_router(health_router("api", (), infrastructure))
    with TestClient(app) as client:
        failed = client.get("/health/ready")
        assert failed.status_code == 503
        assert "private-password" not in failed.text and "private-host" not in failed.text
        assert client.get("/health/live").status_code == 200
        available = True
        assert client.get("/health/ready").status_code == 200
        assert client.get("/health/ready").json()["checks"]["database"] == "connected"


@pytest.mark.parametrize("factory,service", [(create_api, "api"), (create_gpu, "gpu_api")])
def test_process_alive_does_not_mean_service_ready(factory, service):
    with TestClient(factory()) as client:
        live = client.get("/health/live")
        ready = client.get("/health/ready")
    assert live.status_code == 200
    assert live.json()["service"] == service
    assert ready.status_code == 503
    assert ready.json()["status"] == "not_ready"


def test_api_does_not_publish_fixture_endpoints_as_real_implementation():
    with TestClient(create_api()) as client:
        assert client.get("/v1/home").status_code == 404
        assert client.post("/internal/v1/generate", json={"text": "fixture"}).status_code == 404


def test_gpu_without_service_auth_fails_closed():
    with TestClient(create_gpu()) as client:
        response = client.post("/internal/v1/generate", json={"text": "fixture"})
    assert response.status_code == 503
    assert response.json()["detail"] == "SERVICE_AUTH_NOT_CONFIGURED"


def test_enabled_gpu_refuses_startup_without_service_token(monkeypatch):
    monkeypatch.setenv("BONGHWA_GPU_ENABLED", "true")
    with pytest.raises(RuntimeError, match="서비스 인증 토큰"):
        with TestClient(create_gpu()):
            pass


def test_gpu_lease_rejects_overlapping_process_usage(tmp_path):
    from bonghwajigi.common.gpu_lock import GpuLease

    first = GpuLease(tmp_path / "gpu.lock")
    second = GpuLease(tmp_path / "gpu.lock")
    first.acquire()
    try:
        with pytest.raises(RuntimeError, match="사용 중"):
            second.acquire()
    finally:
        first.close()
    second.acquire()
    second.close()


def test_scenario_receiver_cannot_claim_live_ingestion_or_persisted_data(monkeypatch):
    monkeypatch.setenv("BONGHWA_SERVICE_TOKEN", "unit-test-token")
    event = {
        "mode": "simulation",
        "scenario_id": "unit-test",
        "event_id": "unit-test-event",
        "origin": "synthetic",
        "queue": "urgent",
        "payload": {},
    }
    headers = {"Authorization": "Bearer unit-test-token"}
    with TestClient(create_api()) as client:
        response = client.post("/internal/v1/scenario-events", json=event, headers=headers)
        assert response.status_code == 503
        assert response.json()["detail"] == "SCENARIO_INGESTION_NOT_READY"
        event["mode"] = "live"
        assert (
            client.post("/internal/v1/scenario-events", json=event, headers=headers).status_code
            == 422
        )


@pytest.mark.parametrize(
    "path,payload,reason",
    [
        ("generate", {"text": "fixture"}, "GENERATION_MODEL_NOT_READY"),
        ("embeddings", {"texts": ["fixture"]}, "EMBEDDING_MODEL_NOT_READY"),
    ],
)
def test_gpu_auth_never_turns_missing_models_into_success(monkeypatch, path, payload, reason):
    monkeypatch.setenv("BONGHWA_SERVICE_TOKEN", "unit-test-token")
    with TestClient(create_gpu()) as client:
        assert client.post(f"/internal/v1/{path}", json=payload).status_code == 401
        assert (
            client.post(
                f"/internal/v1/{path}",
                json=payload,
                headers={"Authorization": "Bearer wrong-token"},
            ).status_code
            == 401
        )
        response = client.post(
            f"/internal/v1/{path}",
            json=payload,
            headers={"Authorization": "Bearer unit-test-token"},
        )
    assert response.status_code == 503
    assert response.json()["detail"] == reason
    assert "unit-test-token" not in response.text


def test_urgent_worker_starts_without_importing_analysis_or_models():
    probe = """
import json, sys
from bonghwajigi.workers.urgent import app, process
app.loader.import_default_modules()
assert app.conf.task_default_queue == 'urgent'
assert {q.name for q in app.conf.task_queues} == {'urgent'}
assert app.conf.task_create_missing_queues is False
assert app.conf.worker_concurrency == 1
assert not any(name == 'torch' or name == 'transformers'
    or name.startswith('bonghwajigi.gpu_api')
    or name.startswith('bonghwajigi.workers.analysis') for name in sys.modules)
from unittest.mock import MagicMock, patch
sessions = MagicMock()
with patch('bonghwajigi.db.session.session_factory', return_value=sessions), \\
     patch('bonghwajigi.events.urgent.process_urgent', return_value=False) as handler:
    process.run('fixture-event')
    handler.assert_called_once_with(sessions, 'fixture-event')
assert not any(name == 'torch' or name == 'transformers'
    or name.startswith('bonghwajigi.gpu_api')
    or name.startswith('bonghwajigi.workers.analysis') for name in sys.modules)
print(json.dumps({'isolation': 'ok', 'processing': 'independent_urgent_handler'}))
"""
    result = subprocess.run(
        [sys.executable, "-c", probe],
        env={**os.environ, "BONGHWA_BROKER_URL": "redis://127.0.0.1:6379/15"},
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(result.stdout)["isolation"] == "ok"


@pytest.mark.parametrize("component", ["ingestion", "ml"])
def test_unconfigured_command_refuses_to_collect_or_train(component):
    result = subprocess.run(
        [sys.executable, "-m", f"bonghwajigi.{component}"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    checked = subprocess.run(
        [sys.executable, "-m", f"bonghwajigi.{component}", "--check"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(checked.stdout)["status"] == "not_implemented"
