"""공개 기록과 분리된 A/B 설정을 실제 큐·모델·정책으로 재생한다.

자격정보는 권한 600 상태 파일에만 보관한다. 실제 푸시·GPS·119·예측은 호출하지 않는다.
"""

import argparse
import json
import os
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import httpx

from bonghwajigi.api.user_auth import issue_token
from bonghwajigi.common.config import Settings
from bonghwajigi.db.app_models import AppAccount
from bonghwajigi.db.policy_models import PolicyEntity
from bonghwajigi.db.session import session_factory

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BUNDLE = ROOT / "data/filming/yeongdeok-20250325.json"
INCIDENT = "yeongdeok-20250325"
PHRASES = {"A": "지금 아이랑 있습니다.", "B": "혼자라 이동할 수 있어요."}


def role_profile(existing, role):
    return {
        **existing,
        "mobility": "independent" if role == "A" else "walking_aid",
        "dependents": ["child"] if role == "A" else [],
    }


def stamp():
    return datetime.now(UTC).isoformat()


def timed(revision=1, minutes=120):
    return {
        "revision": revision,
        "observed_at": stamp(),
        "expires_at": (datetime.now(UTC) + timedelta(minutes=minutes)).isoformat(),
    }


def private_write(path, value, *, create=False):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    flags = os.O_WRONLY | os.O_CREAT | (os.O_EXCL if create else os.O_TRUNC)
    descriptor = os.open(path, flags, 0o600)
    os.fchmod(descriptor, 0o600)
    with os.fdopen(descriptor, "w") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def wait(callback, label, seconds=180):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        value = callback()
        if value:
            print(label + " 완료", flush=True)
            return value
        time.sleep(0.5)
    raise RuntimeError(label + " 확인 시간 초과")


class Replay:
    def __init__(self, settings, state, path, bundle, base_url):
        self.settings, self.state, self.path, self.bundle = settings, state, path, bundle
        self.scenario = state["scenario_id"]
        self.base = "/internal/v1/policy/scenarios/" + self.scenario
        self.http = httpx.Client(base_url=base_url, timeout=35)
        self.sessions = session_factory(settings)

    def close(self):
        self.http.close()
        self.sessions.kw["bind"].dispose()

    def save(self):
        private_write(self.path, self.state)

    def request(self, method, path, body=None, *, role=None, code=200, params=None):
        token = (
            self.state["roles"][role]["access_token"]
            if role
            else self.settings.service_token.get_secret_value()
        )
        response = self.http.request(
            method,
            path,
            json=body,
            params=params,
            headers={"Authorization": "Bearer " + token},
        )
        if response.status_code != code:
            # 입력·응답·JWT를 로그에 출력하지 않는다.
            raise RuntimeError(f"{method} {path.split('?')[0]} HTTP {response.status_code}")
        return response.json()

    def app(self, method, path, role, body=None, code=200, params=None):
        return self.request(method, "/v1/" + path, body, role=role, code=code, params=params)[
            "data"
        ]

    def next_revision(self, kind, identifier):
        with self.sessions() as session:
            row = session.get(PolicyEntity, (self.scenario, kind, identifier))
            return row.revision + 1 if row else 1

    def submit(self, endpoint, body):
        return self.request("POST", endpoint, body, code=202)["job_id"]

    def job(self, job_id, statuses):
        result = self.request(
            "GET", f"/internal/v1/scenarios/{self.scenario}/analysis-jobs/{job_id}"
        )
        if result["status"] in {"failed", "superseded"}:
            raise RuntimeError("큐 처리 실패: " + str(result.get("error_code")))
        return result if result["status"] in statuses else None

    def position(self, role):
        config = self.bundle["synthetic_staging"]["roles"][role]
        return {"latitude": config["latitude"], "longitude": config["longitude"]}

    def refresh_locations(self):
        for role, account in self.state["roles"].items():
            self.app(
                "PUT",
                "me/location",
                role,
                {
                    "fix_id": uuid4().hex,
                    "installation_id": account["installation_id"],
                    **self.position(role),
                    "accuracy_m": 10,
                    "captured_at": stamp(),
                },
            )

    def source(self, identifier):
        return next(
            x["source"] for x in self.bundle["source_definitions"] if x["document_id"] == identifier
        )

    def setup_source(self):
        return {
            "title": "A·B 위치와 이동 조건 설정",
            "url": "https://github.com/develsvai/BONGHWAJIGI/blob/develop/data/filming/yeongdeok-20250325.json",
            "published_at": self.state["created_at"],
            "collected_at": stamp(),
            "publisher": "봉화지기 검증 자료",
            "verified": True,
        }

    def register_roles(self, phone_user=None, phone_role="A"):
        roles = [phone_role] if phone_user else ["A", "B"]
        for role in roles:
            user = phone_user or "filming-" + role.lower() + "-" + uuid4().hex[:12]
            with self.sessions.begin() as session:
                account = session.get(AppAccount, (self.scenario, user))
                if phone_user:
                    if not account or not account.enabled:
                        raise RuntimeError("지정한 기존 단말 계정이 없거나 비활성입니다.")
                else:
                    account = AppAccount(scenario_id=self.scenario, user_id=user, token_version=1)
                    session.add(account)
                token = issue_token(self.settings, user, self.scenario, account.token_version)
            installation = "filming-" + uuid4().hex[:16]
            self.state["roles"][role] = {
                "user_id": user,
                "installation_id": installation,
                "access_token": token,
                "existing_phone": bool(phone_user),
            }
            self.save()
            self.app(
                "PUT",
                "me/devices/" + installation,
                role,
                {
                    "platform": "android",
                    "push_provider": "fcm",
                    "push_token": None,
                    "notification_permission": "granted",
                    "app_version": "pipeline-verification",
                },
            )
            previous = self.app("GET", "me/profile", role)
            if phone_user:
                self.state["phone_before"] = {
                    "profile": previous,
                    "location": self.app("GET", "me/location", role),
                }
                self.save()
            self.app(
                "PUT",
                "me/profile",
                role,
                {
                    "base_revision": previous["revision"],
                    "profile": role_profile(previous["profile"], role),
                },
            )
        self.refresh_locations()

    def install_routes(self):
        for role, account in self.state["roles"].items():
            config = self.bundle["synthetic_staging"]["roles"][role]
            identifier = INCIDENT + "/" + account["user_id"]
            body = {
                **timed(self.next_revision("route", identifier)),
                "status": "blocked" if config["blocked_escape"] else "open",
                "source": self.setup_source(),
                "reason": config["stage_reason"],
            }
            if config.get("route_reference"):
                reference = json.loads((ROOT / config["route_reference"]).read_text())
                reference["label"] = "참고 경로 · 실제 통행 여부 확인 필요"
                reference["start"]["name"] = "안내 시작 위치"
                reference["destination"]["name"] = "참고 목적지 · 지정 대피소 아님"
                for step in reference["steps"]:
                    step["text"] = {
                        1: "현재 설정된 위치와 경로를 확인하세요.",
                        2: "실제 이동 전 공식 통행 안내를 확인하세요.",
                        3: "공식 안내에 따라 도착 장소를 확인하세요.",
                    }[step["sequence"]]
                body["reference_route"] = reference
            self.request(
                "PUT",
                self.base + f"/incidents/{INCIDENT}/users/{account['user_id']}/route",
                body,
                code=202,
            )

    def regional_conditions(self):
        config = self.bundle["regional_facts"]
        return {
            **timed(self.next_revision("regional_conditions", "yeongdeok")),
            "region_id": "yeongdeok",
            "mode": "simulation",
            "origin": "synthetic",
            "area": self.bundle["synthetic_staging"]["area"],
            "original_observed_at": config["original_observed_at"],
            "forest_nearby": self.bundle["synthetic_staging"]["forest_nearby"],
            "dry_warning": config["dry_warning"],
            "fog_observed": config["fog_observed"],
            "sources": [
                self.source(x)
                for x in config["dry_warning_source_ids"] + config["geography_source_ids"]
            ]
            + [self.setup_source()],
        }

    def analysis(self, *, regional=False, revision=None):
        source = self.source("gov-wildfire-20250326")
        incident_text = next(
            x["text"]
            for x in self.bundle["source_definitions"]
            if x["document_id"] == "gov-wildfire-20250326"
        )
        payload = {
            "text": incident_text,
            "search_query": "2025년 3월 25일 26일 영덕 산불 건조 강풍 대피 정부",
            "as_of": stamp(),
            "source": source,
        }
        if regional:
            payload["regional_conditions"] = self.regional_conditions()
            payload["as_of"] = stamp()
        if revision:
            payload["policy_context"] = {
                "incident_id": INCIDENT,
                "incident_revision": revision,
                "area": self.bundle["synthetic_staging"]["area"],
                "expires_at": timed()["expires_at"],
            }
        job = self.submit(
            "/internal/v1/scenario-events",
            {
                "mode": "simulation",
                "scenario_id": self.scenario,
                "event_id": "filming-analysis-" + uuid4().hex,
                "origin": "historical_replay",
                "queue": "analysis",
                "payload": payload,
            },
        )
        self.state.setdefault("analysis_jobs", []).append(job)
        self.save()
        wait(lambda: self.job(job, {"ready_for_qwen"}), "분석 큐·임베딩·자료 검색", 240)
        return job

    def prepare(self, phone_user=None, phone_role="A"):
        self.request("POST", self.base + "/bootstrap-policy", code=202)
        self.register_roles(phone_user, phone_role)
        for document in self.bundle["source_definitions"]:
            job = self.submit(
                "/internal/v1/retrieval-documents",
                {
                    "mode": "simulation",
                    "scenario_id": self.scenario,
                    "document_id": document["document_id"],
                    "origin": "historical_replay",
                    "revision": 1,
                    "text": document["text"],
                    "source": document["source"],
                    "valid_from": document["source"]["published_at"],
                },
            )
            wait(lambda job=job: self.job(job, {"indexed"}), "수집 자료 임베딩 저장", 180)
        self.analysis(regional=True)
        self.refresh_locations()
        self.install_routes()
        homes = {role: self.app("GET", "home", role) for role in self.state["roles"]}
        for role, home in homes.items():
            self.validate_home(home, role)
        self.state["before_alert"] = homes
        self.state["phase"] = "prepared"
        self.save()
        print("지역 행동요령·공통/개인 준비 완료. 경보 발령 전입니다.", flush=True)

    @staticmethod
    def validate_home(home, role):
        items = home["preparations"]["items"]
        if [item["kind"] for item in items] != ["common", "personal"]:
            raise AssertionError("공통 위·개인 아래 준비 카드 계약이 다릅니다.")
        term = "어린이" if role == "A" else "보조기구"
        if term not in items[1]["title"] + items[1]["text"]:
            raise AssertionError(role + " 맞춤 준비가 반영되지 않았습니다.")
        today = home["today_guidance"]
        if today["status"] != "available" or not today["items"]:
            raise AssertionError("지역 근거 기반 행동요령이 없습니다.")
        if any("안개" in item["text"] for item in today["items"]):
            raise AssertionError("관측되지 않은 안개를 안내했습니다.")

    def trigger(self):
        if self.state.get("phase") not in {"prepared", "triggered", "verified"}:
            raise RuntimeError("prepare를 먼저 완료하세요.")
        self.refresh_locations()
        self.install_routes()
        item = self.bundle["official_alerts"][0]
        source = self.source(item["source_id"])
        incident_revision = self.next_revision("incident", INCIDENT)
        incident = {
            **timed(incident_revision),
            "origin": "historical_replay",
            "title": self.bundle["incident"]["title"],
            "area": self.bundle["synthetic_staging"]["area"],
            "sources": [source],
        }
        urgent_started = time.monotonic()
        job = self.submit(
            "/internal/v1/scenario-events",
            {
                "mode": "simulation",
                "scenario_id": self.scenario,
                "event_id": "filming-urgent-" + uuid4().hex,
                "origin": "historical_replay",
                "queue": "urgent",
                "payload": {
                    "incident_id": INCIDENT,
                    "alert_id": item["alert_id"],
                    "incident": incident,
                    "alert": {
                        "revision": self.next_revision("alert", INCIDENT + "/" + item["alert_id"]),
                        "state": "issued",
                        "authority": item["authority"],
                        "severity": item["severity"],
                        "instruction_kind": "information",
                        "issued_at": item["issued_at"],
                        "expires_at": timed()["expires_at"],
                        "area": self.bundle["synthetic_staging"]["area"],
                        "source": source,
                        "validity_confirmed": True,
                        "raw_text": item["original_excerpt"],
                    },
                },
            },
        )
        urgent = wait(lambda: self.job(job, {"complete"}), "공식 기록 긴급 큐", 60)
        urgent_visible = {}
        for role in self.state["roles"]:
            visible = wait(
                lambda role=role: next(
                    (
                        alert
                        for alert in self.app("GET", "me/alerts", role)["items"]
                        if alert["incident_id"] == INCIDENT
                        and alert["status"] == "active"
                        and alert["relevance"]["status"] == "inside"
                    ),
                    None,
                ),
                role + " Qwen 통합 전 공식 경보 노출",
                60,
            )
            if visible["requires_qwen"] is not False:
                raise AssertionError("공식 경보가 Qwen 통합에 의존합니다.")
            urgent_visible[role] = round(time.monotonic() - urgent_started, 3)
        # 전국 심각 등급을 개인 위험 H3로 추정하지 않는다. 촬영의 국소 조건은 별도 입력이다.
        self.request(
            "PUT",
            self.base + f"/incidents/{INCIDENT}/environment",
            {
                **timed(self.next_revision("environment", INCIDENT)),
                "hazard_band": "H3",
                "source": self.setup_source(),
                "reason": (
                    "A·B 비교를 위한 국소 산불 접근 조건. 전국 경보 등급의 개인 위험 추정값이 아님."
                ),
            },
            code=202,
        )
        analysis_job = self.analysis(revision=incident_revision + 1)

        def integrated():
            value = self.request("GET", self.base + "/integrations/" + analysis_job)
            if value["status"] == "failed":
                raise RuntimeError("Qwen 통합 실패: " + str(value.get("error_code")))
            return value if value["status"] == "complete" else None

        integration = wait(integrated, "Qwen 사건 통합", 420)
        self.state["pipeline"] = {
            "urgent": urgent,
            "integration": integration,
            "urgent_visible_before_qwen_seconds": urgent_visible,
        }
        self.state["phase"] = "triggered"
        self.save()

    def response(self, role):
        disasters = self.app("GET", "disasters", role)["items"]
        target = next((x for x in disasters if x["id"] == INCIDENT), None)
        if not target or not target.get("response_id"):
            return None
        value = self.app("GET", "me/responses/" + target["response_id"], role)
        return value if not value["pending_update"] and value.get("content") else None

    def verify(self):
        self.refresh_locations()
        results = {}
        for role in self.state["roles"]:
            expected = "request_assistance" if role == "A" else "act"
            first = wait(
                lambda role=role, expected=expected: (
                    r
                    if (r := self.response(role))
                    and r["content"]["personal_response"]["level"] == expected
                    else None
                ),
                role + " 개인 대응 단계",
            )
            path = "me/responses/" + first["id"]
            before = first["user_context"]["revision"]
            turn = self.app(
                "POST",
                path + "/text-turns",
                role,
                {
                    "client_turn_id": uuid4().hex,
                    "text": PHRASES[role],
                    "base_response_revision": first["revision"],
                    "base_context_revision": before,
                },
            )
            if turn["assistant"]["source"] != "qwen_grounded" or not turn.get("proposal"):
                raise RuntimeError(role + " 실제 Qwen 상태 제안을 얻지 못했습니다.")
            if self.app("GET", path, role)["user_context"]["revision"] != before:
                raise AssertionError("확인 전 상태가 변경됐습니다.")
            proposal = turn["proposal"]
            proposed = proposal["state"]
            if role == "A" and proposed.get("child_present") is not True:
                raise AssertionError("현재 아이 동반 답변을 추출하지 못했습니다.")
            if role == "A" and proposed.get("can_move") is not None:
                raise AssertionError("아이 동반 답변에서 이동 능력을 추정했습니다.")
            if role == "B" and (
                proposed.get("can_move") is not True or proposed.get("alone_now") != "yes"
            ):
                raise AssertionError("혼자 있음과 이동 가능 답변이 정확히 추출되지 않았습니다.")
            self.app(
                "PUT",
                path + "/context",
                role,
                {
                    "base_revision": proposal["base_revision"],
                    "state": proposal["state"],
                    "overrides": proposal["overrides"],
                    "proposal_turn_id": turn["turn_id"],
                    "confirmation": "user_confirmed",
                    "observed_at": stamp(),
                },
                code=202,
            )
            final = wait(
                lambda role=role, before=before: (
                    r
                    if (r := self.response(role)) and r["user_context"]["revision"] == before + 1
                    else None
                ),
                role + " 확인 후 안내 갱신",
            )
            route = self.app("GET", path + "/route", role)
            if role == "A" and route["route"] is not None:
                raise AssertionError("통제 상태에 이동 경로선을 반환했습니다.")
            if role == "B" and route["route"] is None:
                raise AssertionError("설정된 참고 경로가 반환되지 않았습니다.")
            if final["content"]["personal_response"]["level"] != expected:
                raise AssertionError("답변 확인 후 개인 대응 단계가 설정과 다릅니다.")
            results[role] = {
                "before": first,
                "turn": turn,
                "after": final,
                "route": route,
                "home": self.app("GET", "home", role),
                "alerts": self.app("GET", "me/alerts", role),
            }
        self.state["verification"] = results
        self.state["phase"] = "verified"
        self.save()
        self.export_report()
        print("A·B 실제 Qwen·확인 후 상태·개인 정책·경로 검증 완료", flush=True)

    def export_report(self):
        """원문 발화·사용자/세션 ID·자격정보 없이 확인한 결과만 내보낸다."""
        roles = {}
        for role, value in self.state["verification"].items():
            self.validate_home(value["home"], role)
            before, after = value["before"], value["after"]
            roles[role] = {
                "response_before": before["content"]["personal_response"],
                "response_after": after["content"]["personal_response"],
                "initial_question": before["content"]["assistant_utterance"]["text"],
                "context_revision_before": before["user_context"]["revision"],
                "context_revision_after": after["user_context"]["revision"],
                "confirmed_state": after["user_context"]["data"],
                "assistant_source": value["turn"]["assistant"]["source"],
                "actions_after": [a["text"] for a in after["content"]["actions"]],
                "preparations": value["home"]["preparations"]["items"],
                "today_guidance": value["home"]["today_guidance"],
                "route_status": value["route"]["status"],
                "route_geometry_returned": value["route"]["route"] is not None,
                "official_alert_count": len(value["alerts"]["items"]),
                "actual_prediction_connected": False,
            }
        report = {
            "verified_at": stamp(),
            "mode": "simulation",
            "roles": roles,
            "incident_origin": "historical_replay",
            "personal_locations_and_route_conditions_origin": "synthetic",
            "urgent_queue_status": self.state["pipeline"]["urgent"]["status"],
            "qwen_integration_status": self.state["pipeline"]["integration"]["status"],
            "urgent_visible_before_qwen_seconds": self.state["pipeline"][
                "urgent_visible_before_qwen_seconds"
            ],
            "actual_gps_used": False,
            "real_push_sent": False,
            "actual_119_used": False,
            "original_times_and_collection_limits": self.bundle["collection_note"],
            "official_evacuation_sms_available": False,
            "limitations": self.bundle["limitations"],
        }
        private_write(self.path.with_suffix(".report.json"), report)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=["prepare", "trigger", "verify", "all"])
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--bundle", type=Path, default=DEFAULT_BUNDLE)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--scenario")
    parser.add_argument("--phone-user")
    parser.add_argument("--phone-role", choices=["A", "B"], default="A")
    args = parser.parse_args()
    settings = Settings()
    if settings.mode != "simulation" or settings.push_provider != "simulation":
        parser.exit(2, "검증용 데이터 범위와 모의 원격 전송 설정이 필요합니다.\n")
    if args.phase in {"prepare", "all"}:
        if args.phone_user and args.scenario != settings.app_registration_scenario:
            parser.exit(2, "기존 단말은 설치 계정의 scenario를 명시해야 합니다.\n")
        state = {
            "scenario_id": args.scenario or "filming-" + uuid4().hex[:16],
            "created_at": stamp(),
            "roles": {},
            "phase": "created",
        }
        private_write(args.state, state, create=True)
    else:
        if args.state.stat().st_mode & 0o077:
            parser.exit(2, "상태 파일 권한은 600이어야 합니다.\n")
        state = json.loads(args.state.read_text())
    bundle = json.loads(args.bundle.read_text())
    replay = Replay(settings, state, args.state, bundle, args.base_url)
    try:
        if args.phase in {"prepare", "all"}:
            replay.prepare(args.phone_user, args.phone_role)
        if args.phase in {"trigger", "all"}:
            replay.trigger()
        if args.phase in {"verify", "all"}:
            replay.verify()
    finally:
        replay.close()


if __name__ == "__main__":
    main()
