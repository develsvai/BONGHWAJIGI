"""실제 분석·Qwen·정책 루프에서 개인화, 새 관측, 프로필/위치 변경과 주기 만료를 재생한다."""

import argparse
import json
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import httpx

from bonghwajigi.common.config import Settings

AREA = {"west": 129.0, "east": 129.8, "south": 36.0, "north": 37.0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:18000")
    parser.add_argument("--report", type=Path, default=Path("data/artifacts/policy-loop-demo.json"))
    args = parser.parse_args()
    settings = Settings()
    if not settings.service_token:
        parser.exit(2, "분석 API 토큰 설정이 필요합니다.\n")
    template = json.loads(Path("data/scenarios/yeongdeok-integration.json").read_text())
    policy = json.loads(Path("data/scenarios/policy-loop-rules.json").read_text())
    scenario = "policy-demo-" + uuid4().hex
    moment = datetime.fromisoformat(template["as_of"])
    collected = datetime.now(UTC).isoformat()
    source = {**template["source_definitions"][0]["source"], "collected_at": collected}
    guide_source = {**template["source_definitions"][1]["source"], "collected_at": collected}
    base = "/internal/v1/policy/scenarios/" + scenario
    steps, generations = [], []

    with httpx.Client(
        base_url=args.base_url,
        timeout=20,
        headers={"Authorization": "Bearer " + settings.service_token.get_secret_value()},
    ) as client:

        def put(path, body):
            response = client.put(path, json=body)
            if response.status_code != 202:
                raise RuntimeError(f"입력 실패: HTTP {response.status_code} {response.text[:200]}")
            return response.json()

        def get(path):
            response = client.get(path)
            response.raise_for_status()
            return response.json()

        def wait(callback, description, seconds=180):
            deadline = time.monotonic() + seconds
            while time.monotonic() < deadline:
                value = callback()
                if value:
                    return value
                time.sleep(0.5)
            raise RuntimeError("대기 시간 초과: " + description)

        def plan(user, scope=base):
            response = client.get(scope + f"/users/{user}/plans/fire")
            return response.json() if response.status_code == 200 else None

        def all_ready():
            values = [plan(user) for user in ("independent", "assistance", "with-child")]
            if all(value and value["content"] and not value["pending_update"] for value in values):
                return values

        def capture(name):
            values = wait(all_ready, name)
            steps.append(
                {
                    "step": name,
                    "users": [
                        {
                            "user_id": value["content"]["user_id"],
                            "revision": value["revision"],
                            "state": value["content"]["state"],
                            "actions": [item["action_id"] for item in value["content"]["actions"]],
                            "level": value["content"]["personal_response"]["level"],
                            "prediction": value["content"]["prediction"]["status"],
                            "context": value["content"]["context"]["status"],
                        }
                        for value in values
                    ],
                }
            )
            return values

        def seed_rules(scope, clock):
            for guide in policy["guidance"]:
                put(
                    scope + "/guidance/" + guide["guidance_id"],
                    {
                        "revision": 1,
                        "review_state": "simulation_only",
                        "text": guide["text"],
                        "source": guide_source,
                        "valid_from": guide_source["published_at"],
                        "expires_at": (clock + timedelta(hours=2)).isoformat(),
                    },
                )
            put(
                scope + "/rules",
                {"revision": 1, "review_state": "simulation_only", "rules": policy["rules"]},
            )

        put(base + "/clock", {"revision": 1, "evaluation_at": moment.isoformat()})
        seed_rules(base, moment)
        for user, profile in {
            "independent": {},
            "assistance": {"mobility_assistance": True},
            "with-child": {"children_accompanying": True},
        }.items():
            put(base + f"/users/{user}/profile", {"revision": 1, **profile})
            put(
                base + f"/users/{user}/location",
                {
                    "revision": 1,
                    "latitude": 36.4,
                    "longitude": 129.35,
                    "accuracy_m": 10,
                    "observed_at": moment.isoformat(),
                    "expires_at": (moment + timedelta(minutes=10)).isoformat(),
                },
            )
        notice = template["official_alerts"][0]
        put(
            base + "/incidents/fire/alerts/historical-notice",
            {
                "revision": 1,
                "state": "issued",
                "authority": notice["authority"],
                "severity": notice["severity"],
                "issued_at": notice["issued_at"],
                "expires_at": (moment + timedelta(hours=1)).isoformat(),
                "raw_text": notice["original_excerpt"],
                "source": source,
                "validity_confirmed": False,
            },
        )

        def observation(revision):
            event = {
                "mode": "simulation",
                "scenario_id": scenario,
                "event_id": "observation-" + str(revision),
                "origin": "historical_replay",
                "queue": "analysis",
                "payload": {
                    "text": template["source_definitions"][0]["text"],
                    "search_query": "영덕 대피",
                    "as_of": moment.isoformat(),
                    "source": source,
                    "policy_context": {
                        "incident_id": "fire",
                        "incident_revision": revision,
                        "expires_at": (moment + timedelta(hours=1)).isoformat(),
                        "area": AREA,
                    },
                },
            }
            response = client.post("/internal/v1/scenario-events", json=event)
            response.raise_for_status()
            job_id = response.json()["job_id"]
            duplicate = client.post("/internal/v1/scenario-events", json=event).json()
            assert duplicate["duplicate"] and duplicate["job_id"] == job_id

            def complete():
                value = get(base + "/integrations/" + job_id)
                if value["status"] == "failed":
                    raise RuntimeError("Qwen 통합 실패: " + str(value["error_code"]))
                return value if value["status"] == "complete" else None

            integration = wait(complete, "Qwen 통합")
            generations.append(
                {
                    "job_id": job_id,
                    "status": integration["status"],
                    "generation": integration["generation"],
                }
            )
            wait(
                lambda: (
                    all_ready()
                    and all(
                        value["content"]["context"]["status"] == "complete"
                        and value["content"]["input_versions"]["incident:fire"] == revision
                        for value in all_ready()
                    )
                ),
                "통합 결과의 사용자별 계획 반영",
            )

        observation(1)
        initial = capture("처음 통합·세 사용자 개인화")
        assert [len(value["content"]["actions"]) for value in initial] == [1, 2, 2]
        prediction = {
            "revision": 1,
            "status": "simulation",
            "probability": 0.73,
            "model_id": "synthetic-loop-demo",
            "model_revision": "simulation-only",
            "target": "synthetic_probability_no_operational_use",
            "area": AREA,
            "observed_at": moment.isoformat(),
            "expires_at": (moment + timedelta(minutes=5)).isoformat(),
        }
        put(base + "/incidents/fire/prediction", prediction)
        capture("모의 예측 입력 갱신")
        put(base + "/users/independent/profile", {"revision": 2, "mobility_assistance": True})
        updated = capture("한 사용자 이동 지원 프로필 변경")
        assert len(updated[0]["content"]["actions"]) == 2
        put(
            base + "/users/assistance/location",
            {
                "revision": 2,
                "latitude": 35,
                "longitude": 127,
                "accuracy_m": 10,
                "observed_at": moment.isoformat(),
                "expires_at": (moment + timedelta(minutes=10)).isoformat(),
            },
        )
        outside = capture("한 사용자 구역 밖 이동")
        assert outside[1]["content"]["state"] == "outside_scope"
        observation(2)
        capture("두 번째 관측→검색→Qwen→정책 자동 갱신")
        put(
            base + "/rules",
            {"revision": 2, "review_state": "simulation_only", "rules": policy["rules"]},
        )
        capture("정책 규칙 버전 변경")
        put(
            base + "/incidents/fire/prediction",
            {**prediction, "revision": 2, "status": "unavailable", "probability": None},
        )
        capture("예측 불가 갱신·경보 기록 보존")
        put(
            base + "/clock",
            {"revision": 2, "evaluation_at": (moment + timedelta(minutes=11)).isoformat()},
        )
        final = capture("재생 시각 전진·위치 만료")
        assert all(value["content"]["state"] == "needs_refresh" for value in final)

        # 새 입력 없이 벽시계만 흘러도 별도 계획 실행기가 만료를 처리하는지 확인한다.
        periodic_scope = base + "-wall"
        wall = datetime.now(UTC)
        seed_rules(periodic_scope, wall)
        put(periodic_scope + "/users/periodic/profile", {"revision": 1})
        put(
            periodic_scope + "/users/periodic/location",
            {
                "revision": 1,
                "latitude": 36.4,
                "longitude": 129.35,
                "accuracy_m": 10,
                "observed_at": wall.isoformat(),
                "expires_at": (wall + timedelta(seconds=8)).isoformat(),
            },
        )
        put(
            periodic_scope + "/incidents/fire",
            {
                "revision": 1,
                "origin": "synthetic",
                "title": "[합성] 벽시계 주기 만료 시연",
                "observed_at": wall.isoformat(),
                "expires_at": (wall + timedelta(hours=1)).isoformat(),
                "area": AREA,
                "sources": [source],
            },
        )
        periodic_before = wait(
            lambda: (
                value
                if (value := plan("periodic", periodic_scope))
                and value["content"]
                and value["content"]["actions"]
                else None
            ),
            "벽시계 최초 계획",
            seconds=15,
        )
        periodic_after = wait(
            lambda: (
                value
                if (value := plan("periodic", periodic_scope))
                and value["revision"] > periodic_before["revision"]
                and not value["pending_update"]
                and value["content"]["state"] == "needs_refresh"
                else None
            ),
            "새 입력 없는 주기 만료",
            seconds=30,
        )
        report = {
            "mode": "simulation",
            "operational_use": False,
            "finished_at": datetime.now(UTC).isoformat(),
            "scenario_id": scenario,
            "notes": [
                "모든 사용자·위치·사각 구역과 예측값은 합성 시연이다.",
                "사건 자료·경보는 과거 기록이며 현재 경보나 실제 산불 경계가 아니다.",
                "예측값은 학습 모델의 실제 출력이 아닌 입력 갱신용 합성값이다.",
            ],
            "steps": steps,
            "initial_plans": initial,
            "final_plans": final,
            "generations": generations,
            "periodic_without_new_input": {"before": periodic_before, "after": periodic_after},
            "history": get(base + "/users/independent/plans/fire/history"),
            "response_levels": "회의 결정 대기",
            "notification_dispatched": False,
        }
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        print(
            json.dumps(
                {
                    "report": str(args.report),
                    "steps": len(steps),
                    "qwen_calls": len(generations),
                    "users": 3,
                    "periodic_without_new_input": True,
                    "notification_dispatched": False,
                },
                ensure_ascii=False,
            )
        )


if __name__ == "__main__":
    main()
