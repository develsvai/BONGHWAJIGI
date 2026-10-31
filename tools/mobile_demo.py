"""실제 앱 설치 계정용 합성 자료를 준비하고 배포 API를 검증한다. 비밀값은 출력하지 않는다."""

import argparse
import json
import time
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import httpx

from bonghwajigi.common.config import Settings
from bonghwajigi.db.policy_models import PolicyEntity, PolicyScope
from bonghwajigi.db.session import session_factory

AREA = {"west": 129.0, "east": 129.8, "south": 36.0, "north": 37.0}
POSITION = {"latitude": 36.4, "longitude": 129.35, "accuracy_m": 10}


def stamp():
    return datetime.now(UTC).isoformat()


def wait(callback, label):
    deadline = time.monotonic() + 90
    while time.monotonic() < deadline:
        value = callback()
        if value:
            return value
        time.sleep(0.4)
    raise RuntimeError("검증 시간 초과: " + label)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed-only", action="store_true")
    args = parser.parse_args()
    settings = Settings()
    if not (
        settings.mode == "simulation"
        and settings.push_provider == "simulation"
        and settings.app_registration_enabled
        and settings.app_registration_scenario == "mobile-demo"
    ):
        parser.exit(2, "등록이 켜진 mobile-demo simulation 설정에서만 실행합니다.\n")
    scenario = settings.app_registration_scenario
    base = "/internal/v1/policy/scenarios/" + scenario
    sessions = session_factory(settings)
    with sessions() as session:
        scope = session.get(PolicyScope, scenario)
        if scope and scope.evaluation_at is not None:
            parser.exit(
                2,
                "mobile-demo는 실제 시각 평가가 필요합니다. 기존 고정 시각은 변경하지 않습니다.\n",
            )
        revisions = {}
        for kind, identifier in [
            ("incident", "mobile-fire"),
            ("environment", "mobile-fire"),
            ("alert", "mobile-fire/mobile-alert"),
        ]:
            row = session.get(PolicyEntity, (scenario, kind, identifier))
            revisions[kind] = row.revision + 1 if row else 1
    sessions.kw["bind"].dispose()
    expires = (datetime.now(UTC) + timedelta(hours=24)).isoformat()
    source = {
        "title": "[합성 시연] 휴대폰 통합 검증 자료",
        "url": "https://example.invalid/bonghwajigi/mobile-demo",
        "published_at": stamp(),
        "collected_at": stamp(),
        "verified": True,
    }
    incident = {
        "revision": revisions["incident"],
        "origin": "synthetic",
        "title": "[합성 시연] 봉화지기 산불 상황",
        "observed_at": stamp(),
        "expires_at": expires,
        "area": AREA,
        "sources": [source],
    }
    with httpx.Client(base_url="http://127.0.0.1:8000", timeout=30) as client:

        def request(method, path, body=None, token=None, expected=200, params=None):
            headers = {"Authorization": "Bearer " + token} if token else {}
            response = client.request(method, path, json=body, headers=headers, params=params)
            if response.status_code != expected:
                raise RuntimeError(f"{method} {path}: HTTP {response.status_code}, 예상 {expected}")
            return response.json()

        def internal(method, path, body=None):
            return request(method, path, body, settings.service_token.get_secret_value(), 202)

        internal("POST", base + "/bootstrap-policy")
        internal("PUT", base + "/incidents/mobile-fire", incident)
        internal(
            "PUT",
            base + "/incidents/mobile-fire/environment",
            {
                "revision": revisions["environment"],
                "observed_at": stamp(),
                "expires_at": expires,
                "hazard_band": "H2",
                "source": source,
                "reason": "[합성 시연] 접근 상황. 실제 산불 확산 또는 예측 결과가 아닙니다.",
            },
        )
        job = internal(
            "POST",
            "/internal/v1/scenario-events",
            {
                "mode": "simulation",
                "scenario_id": scenario,
                "event_id": "mobile-" + uuid4().hex,
                "origin": "synthetic",
                "queue": "urgent",
                "payload": {
                    "incident_id": "mobile-fire",
                    "alert_id": "mobile-alert",
                    "incident": incident,
                    "alert": {
                        "revision": revisions["alert"],
                        "state": "issued",
                        "authority": "합성 시연 발령기관",
                        "severity": "시연",
                        "instruction_kind": "prepare",
                        "issued_at": stamp(),
                        "expires_at": expires,
                        "area": AREA,
                        "source": source,
                        "validity_confirmed": True,
                        "raw_text": (
                            "[합성 시연] 산불 상황을 확인하고 대피에 필요한 물품을 준비하세요. "
                            "실제 경보가 아닙니다."
                        ),
                    },
                },
            },
        )
        wait(
            lambda: (
                request(
                    "GET",
                    f"/internal/v1/scenarios/{scenario}/analysis-jobs/{job['job_id']}",
                    token=settings.service_token.get_secret_value(),
                )["status"]
                == "complete"
            ),
            "긴급 큐 완료",
        )
        report = {
            "scenario_id": scenario,
            "mode": "simulation",
            "origin": "synthetic",
            "incident_id": "mobile-fire",
            "test_position": POSITION,
            "expires_at": expires,
            "urgent_queue_complete": True,
            "actual_prediction_connected": False,
            "real_push": False,
            "verified_at": stamp(),
        }
        if args.seed_only:
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return

        def register():
            identifier = "qa-" + uuid4().hex
            tokens = request(
                "POST",
                "/v1/auth/installations",
                {
                    "installation_id": identifier,
                    "consent": {
                        "version": "internal-demo-v1",
                        "service": True,
                        "privacy": True,
                        "location": True,
                    },
                },
                expected=201,
            )["data"]
            return identifier, tokens

        installation, tokens = register()
        _, second = register()

        def app(method, path, body=None, expected=200, params=None):
            return request(method, "/v1/" + path, body, tokens["access_token"], expected, params)[
                "data"
            ]

        app(
            "PUT",
            "me/profile",
            {
                "base_revision": 1,
                "profile": {
                    "display_name": "합성 단말 검증",
                    "mobility": "independent",
                    "dependents": ["other"],
                },
            },
        )
        app(
            "PUT",
            "me/location",
            {
                "fix_id": uuid4().hex,
                "installation_id": installation,
                **POSITION,
                "captured_at": stamp(),
            },
        )

        def current():
            items = app("GET", "disasters")["items"]
            item = next((i for i in items if i["id"] == "mobile-fire"), None)
            return (
                app("GET", "me/responses/" + item["response_id"])
                if item and item["response_id"]
                else None
            )

        def level(expected):
            return wait(
                lambda: (
                    v
                    if (v := current())
                    and not v["pending_update"]
                    and v["content"]["personal_response"]["level"] == expected
                    else None
                ),
                expected,
            )

        first = level("prepare")
        assert first["content"]["prediction"]["probability"] is None
        alert = wait(
            lambda: next(
                (a for a in app("GET", "me/alerts")["items"] if a["incident_id"] == "mobile-fire"),
                None,
            ),
            "공식 원문",
        )
        assert alert["requires_qwen"] is False and "[합성 시연]" in alert["raw_text"]
        cursor = app("GET", "me/updates")["next_cursor"]
        path = "me/responses/" + first["id"]
        app(
            "PUT",
            path + "/context",
            {
                "base_revision": 0,
                "observed_at": stamp(),
                "confirmation": "user_confirmed",
                "overrides": {"stairs": "difficult"},
            },
            202,
        )
        second_level = level("act")
        app(
            "PUT",
            path + "/context",
            {
                "base_revision": second_level["user_context"]["revision"],
                "observed_at": stamp(),
                "confirmation": "user_confirmed",
                "state": {"observed_hazard": "trapped", "can_move": False},
            },
            202,
        )
        final = level("request_assistance")
        assert final["content"]["assistant_utterance"]["text"]
        assert app("GET", "me/updates", params={"cursor": cursor})["events"]
        request("GET", "/v1/" + path, token=second["access_token"], expected=404)
        request("GET", "/v1/me/alerts/" + alert["id"], token=second["access_token"], expected=404)
        refreshed = request("POST", "/v1/auth/refresh", {"refresh_token": tokens["refresh_token"]})[
            "data"
        ]
        assert refreshed["refresh_token"] != tokens["refresh_token"]
        tokens = refreshed
        app("GET", "me/profile")
        app("POST", "me/logout")
        request("GET", "/v1/me/profile", token=tokens["access_token"], expected=401)
        request(
            "POST", "/v1/auth/refresh", {"refresh_token": tokens["refresh_token"]}, expected=401
        )
        request("POST", "/v1/me/logout", token=second["access_token"])
        report.update(
            {
                "checks": [
                    "등록",
                    "프로필 기타 보호 대상",
                    "위치",
                    "긴급 큐 원문",
                    "경고→대피→위급",
                    "정책 텍스트",
                    "cursor 갱신",
                    "사용자 격리",
                    "refresh 회전",
                    "로그아웃 폐기",
                ],
                "labels": [
                    first["content"]["personal_response"]["label"],
                    second_level["content"]["personal_response"]["label"],
                    final["content"]["personal_response"]["label"],
                ],
            }
        )
        print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
