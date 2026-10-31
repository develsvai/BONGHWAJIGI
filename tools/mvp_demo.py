"""일반 서버의 실제 큐·API·정책·모의 전달을 합성 시나리오로 점검한다."""

import argparse
import json
import os
import time
from collections import Counter
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import httpx

from bonghwajigi.api.user_auth import issue_token
from bonghwajigi.common.config import Settings
from bonghwajigi.db.app_models import AppAccount
from bonghwajigi.db.session import session_factory

AREA = {"west": 129.0, "east": 129.8, "south": 36.0, "north": 37.0}
USERS = {"independent": "independent", "slow": "walking_aid", "assistance": "assistance_required"}


def timestamp():
    return datetime.now(UTC).isoformat()


def private_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def wait(callback, description, seconds=90):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        value = callback()
        if value:
            return value
        time.sleep(0.4)
    raise RuntimeError("시연 확인 시간 초과: " + description)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--output-dir", type=Path, default=Path("/accounts"))
    args = parser.parse_args()
    settings = Settings()
    if settings.mode != "simulation" or settings.push_provider != "simulation":
        parser.exit(2, "simulation 모드와 모의 전송 설정에서만 실행할 수 있습니다.\n")
    scenario = "mvp-demo-" + uuid4().hex[:16]
    base = "/internal/v1/policy/scenarios/" + scenario
    tokens, steps = {}, []
    sessions = session_factory(settings)
    with sessions.begin() as session:
        for user in USERS:
            session.add(AppAccount(scenario_id=scenario, user_id=user, token_version=1))
            tokens[user] = issue_token(settings, user, scenario)
    sessions.kw["bind"].dispose()
    for user, token in tokens.items():
        private_json(
            args.output_dir / f"{scenario}-{user}.json",
            {
                "scenario_id": scenario,
                "user_id": user,
                "access_token": token,
                "token_type": "Bearer",
                "expires_in": settings.jwt_lifetime_seconds,
            },
        )
    with httpx.Client(base_url=args.base_url, timeout=30) as client:

        def request(method, path, body=None, user=None, code=200, params=None):
            token = tokens[user] if user else settings.service_token.get_secret_value()
            response = client.request(
                method,
                path,
                json=body,
                params=params,
                headers={"Authorization": "Bearer " + token},
            )
            if response.status_code != code:
                # 자격정보/입력 본문/응답 본문을 오류 출력에 포함하지 않는다.
                raise RuntimeError(f"{method} {path}: HTTP {response.status_code}, 예상 {code}")
            return response.json() if code != 404 else None

        def app(path, user="independent"):
            return request("GET", "/v1/" + path, user=user)["data"]

        def put(path, body):
            return request("PUT", base + path, body, code=202)

        def timed(revision=1):
            return {
                "revision": revision,
                "observed_at": timestamp(),
                "expires_at": (datetime.now(UTC) + timedelta(minutes=20)).isoformat(),
            }

        source = {
            "title": "실제 재난이 아닌 MVP 합성 시연 자료",
            "url": "https://example.invalid/bonghwajigi/synthetic-replay",
            "published_at": timestamp(),
            "collected_at": timestamp(),
            "verified": True,
        }
        incident = {
            **timed(),
            "origin": "synthetic",
            "title": "[합성 시연] 산불 상황",
            "area": AREA,
            "sources": [source],
        }
        request("POST", base + "/bootstrap-policy", code=202)
        for user, mobility in USERS.items():
            request(
                "PUT",
                "/v1/me/profile",
                {
                    "base_revision": 0,
                    "profile": {"mobility": mobility},
                },
                user=user,
            )
            request(
                "PUT",
                "/v1/me/devices/demo-phone",
                {
                    "platform": "android",
                    "push_provider": "fcm",
                    "push_token": "synthetic-device-" + scenario + "-" + user,
                    "notification_permission": "granted",
                    "app_version": "mvp-synthetic",
                },
                user=user,
            )
            request(
                "PUT",
                "/v1/me/location",
                {
                    "fix_id": "initial",
                    "installation_id": "demo-phone",
                    "latitude": 36.4,
                    "longitude": 129.35,
                    "accuracy_m": 10,
                    "captured_at": timestamp(),
                },
                user=user,
            )
        put("/incidents/fire", incident)
        put(
            "/incidents/fire/environment",
            {
                **timed(),
                "hazard_band": "H2",
                "source": source,
                "reason": "합성 접근 상황",
            },
        )

        def plan(user):
            items = app("disasters", user)["items"]
            identifier = next((i["response_id"] for i in items if i["id"] == "fire"), None)
            return app("me/responses/" + identifier, user) if identifier else None

        def capture(name, expected):
            def ready():
                values = {u: plan(u) for u in expected}
                return (
                    values
                    if all(
                        v
                        and not v["pending_update"]
                        and v["content"]
                        and v["content"]["personal_response"]["level"] == expected[u]
                        for u, v in values.items()
                    )
                    else None
                )

            values = wait(ready, name)
            snapshot = {}
            for user, value in values.items():
                content = value["content"]
                assert content["prediction"]["status"] == "unavailable"
                assert content["prediction"]["probability"] is None
                snapshot[user] = {
                    "response_id": value["id"],
                    "revision": value["revision"],
                    "level": content["personal_response"]["level"],
                    "label": content["personal_response"]["label"],
                    "actions": [a["text"] for a in content["actions"]],
                    "prediction": content["prediction"],
                }
            steps.append({"step": name, "users": snapshot})
            print("검증 완료:", name, flush=True)
            return values

        capture(
            "H2에서 이동 여건별 경고와 조기 대피",
            {
                "independent": "prepare",
                "slow": "act",
                "assistance": "act",
            },
        )
        cursor = app("me/updates")["next_cursor"]
        alert = {
            "revision": 1,
            "state": "issued",
            "authority": "합성 시연 기관",
            "severity": "시연",
            "instruction_kind": "evacuate",
            "issued_at": timestamp(),
            "expires_at": (datetime.now(UTC) + timedelta(minutes=20)).isoformat(),
            "area": AREA,
            "raw_text": "[합성 시연] 지정된 장소로 대피하세요.",
            "source": source,
            "validity_confirmed": True,
        }

        def urgent(revision, state="issued"):
            body = {
                "mode": "simulation",
                "scenario_id": scenario,
                "event_id": "official-" + str(revision),
                "origin": "synthetic",
                "queue": "urgent",
                "payload": {
                    "incident_id": "fire",
                    "alert_id": "demo-alert",
                    "incident": incident,
                    "alert": {
                        **alert,
                        "revision": revision,
                        "state": state,
                        "raw_text": f"[합성 시연] 대피 안내 {revision}판, {state}",
                    },
                },
            }
            result = request("POST", "/internal/v1/scenario-events", body, code=202)
            duplicate = request("POST", "/internal/v1/scenario-events", body, code=202)
            assert duplicate["duplicate"] and duplicate["job_id"] == result["job_id"]
            return result["job_id"]

        job_id = urgent(1)
        alerts = wait(lambda: app("me/alerts")["items"], "긴급 큐 공식 원문")
        assert alerts[0]["requires_qwen"] is False
        values = capture(
            "긴급 큐 대피 경보: 독립·느린 이동은 대피, 조력자 없는 사용자는 위급",
            {
                "independent": "act",
                "slow": "act",
                "assistance": "request_assistance",
            },
        )
        job = request("GET", f"/internal/v1/scenarios/{scenario}/analysis-jobs/{job_id}")
        assert job["status"] == "complete"
        updates = request("GET", "/v1/me/updates", user="independent", params={"cursor": cursor})
        assert any(e["type"] == "alert.updated" for e in updates["data"]["events"])
        request("GET", "/v1/me/responses/" + values["independent"]["id"], user="slow", code=404)
        request("GET", "/v1/me/alerts/" + alerts[0]["id"], user="slow", code=404)
        receipt = request(
            "POST",
            "/v1/me/alerts/" + alerts[0]["id"] + "/receipts",
            {
                "alert_revision": 1,
                "installation_id": "demo-phone",
                "event": "displayed",
                "occurred_at": timestamp(),
            },
            user="independent",
            code=202,
        )
        assert receipt["data"]["meaning"] == "client_reported_only"
        put(
            "/incidents/fire/users/assistance/route",
            {
                **timed(),
                "status": "open",
                "source": source,
                "reason": "합성 대피 경로 확인",
            },
        )
        request(
            "PUT",
            "/v1/me/responses/" + values["assistance"]["id"] + "/context",
            {
                "base_revision": 0,
                "observed_at": timestamp(),
                "confirmation": "user_confirmed",
                "state": {"helper_present": True, "can_move": True},
            },
            user="assistance",
            code=202,
        )
        capture("조력자 현장 도착과 이용 가능한 경로 확인 후 대피", {"assistance": "act"})
        put(
            "/incidents/fire/users/slow/route",
            {
                **timed(),
                "status": "blocked",
                "source": source,
                "reason": "합성: 대체 경로도 없음",
            },
        )
        capture("이용 가능한 모든 대피 경로 차단 시 위급", {"slow": "request_assistance"})
        urgent(2)
        wait(
            lambda: next((a for a in app("me/alerts")["items"] if a["revision"] == 2), None),
            "경보 정정",
        )
        urgent(3, "cancelled")
        wait(
            lambda: next((a for a in app("me/alerts")["items"] if a["revision"] == 3), None),
            "경보 해제",
        )
        # 해제만으로 기존 위험 단계를 자동 하향하지 않는다.
        capture("경보 해제 후에도 확인 없는 자동 하향 방지", {"independent": "act"})
        put(
            "/incidents/fire/environment",
            {
                **timed(2),
                "hazard_band": "H1",
                "source": source,
                "reason": "합성 위험 감소 확인",
            },
        )
        request(
            "PUT",
            "/v1/me/responses/" + values["independent"]["id"] + "/context",
            {
                "base_revision": 0,
                "observed_at": timestamp(),
                "confirmation": "user_confirmed",
                "state": {"can_move": True, "deescalation_confirmed": True},
            },
            user="independent",
            code=202,
        )
        final = capture("새 위험 감소 자료와 사용자 확인 후 경고", {"independent": "prepare"})
        request("DELETE", "/v1/me/location", user="independent")
        wait(
            lambda: (
                (v := plan("independent"))
                and not v["pending_update"]
                and v["content"]["personal_response"]["level"] == "unknown"
            ),
            "위치 삭제 시 확인 중",
        )
        request(
            "PUT",
            "/v1/me/location",
            {
                "fix_id": "restored",
                "installation_id": "demo-phone",
                "latitude": 36.4,
                "longitude": 129.35,
                "accuracy_m": 10,
                "captured_at": timestamp(),
            },
            user="independent",
        )
        final = capture("새 위치 입력 후 정책 재계산", {"independent": "prepare"})
        wait(
            lambda: any(d["status"] == "simulated" for d in app("me/deliveries")["items"]),
            "전달 큐 모의 전송",
        )
        deliveries = {
            u: dict(Counter(d["status"] for d in app("me/deliveries", u)["items"])) for u in USERS
        }
        assert all(v.get("simulated", 0) for v in deliveries.values())
        report = {
            "scenario_id": scenario,
            "mode": "simulation",
            "verified_at": timestamp(),
            "origin": "합성 시연이며 실제 재난·공식 발령·실제 단말 수신 결과가 아님",
            "steps": steps,
            "deliveries": deliveries,
            "checks": {
                "urgent_without_qwen": True,
                "idempotent_event_acceptance": True,
                "official_correction_and_cancel": True,
                "user_owned_resources": True,
                "cursor_updates": True,
                "location_delete_and_restore": True,
                "client_reported_receipt": True,
                "real_push": False,
                "actual_prediction_connected": False,
            },
            "restart_probe": {
                "user": "independent",
                "response_id": final["independent"]["id"],
                "revision": final["independent"]["revision"],
            },
        }
        output = args.output_dir / (scenario + "-report.json")
        private_json(output, report)
        print("비밀값 없는 검증 보고서:", output)


if __name__ == "__main__":
    main()
