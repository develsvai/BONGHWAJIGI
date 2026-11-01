"""OpenAPI와 고정 모의 응답을 검사한다. 실제 서버/긴급 연락을 호출하지 않는다."""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator, FormatChecker, ValidationError
from openapi_spec_validator import validate_spec

ROOT = Path(__file__).resolve().parents[1]
API = ROOT / "docs/V2/delivery/api"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, help="검증 보고서를 기록할 경로")
    args = parser.parse_args()
    spec = yaml.safe_load((API / "openapi.yaml").read_text())
    fixtures = json.loads((API / "examples.json").read_text())
    mapping = json.loads((API / "screen-map.json").read_text())
    validate_spec(spec)
    schemas = spec["components"]["schemas"]

    def validate(schema: dict, value: object) -> None:
        document = {"components": spec["components"], **schema}
        Draft202012Validator(document, format_checker=FormatChecker()).validate(value)

    for schema in schemas.values():
        Draft202012Validator.check_schema(schema)
    operations = {}
    for path, methods in spec["paths"].items():
        for method, operation in methods.items():
            oid = operation["operationId"]
            assert oid not in operations, f"중복 operationId: {oid}"
            operations[oid] = (path, method, operation)
            assert set(operation["x-screen-ids"]) <= set(mapping["screens"])
            for p in operation.get("parameters", []):
                if "example" in p:
                    validate(p["schema"], p["example"])
            if "requestBody" in operation:
                content = operation["requestBody"]["content"]["application/json"]
                validate(content["schema"], content["example"])
            for response in operation["responses"].values():
                for content in response.get("content", {}).values():
                    validate(content["schema"], content["example"])

    covered = set()
    for exchange in fixtures["exchanges"]:
        oid = exchange["operation_id"]
        path, method, operation = operations[oid]
        assert (path, method.upper()) == (exchange["path"], exchange["method"])
        for p in operation.get("parameters", []):
            params = exchange["request"]["parameters"]
            assert not p.get("required") or p["name"] in params, (exchange["id"], p["name"])
            if p["name"] in params:
                validate(p["schema"], params[p["name"]])
        if "requestBody" in operation:
            validate(operation["requestBody"]["content"]["application/json"]["schema"], exchange["request"]["body"])
        status = str(exchange["response"]["status"])
        declared = operation["responses"][status]
        if status == "204":
            assert "body" not in exchange["response"]
        else:
            media = "application/problem+json" if int(status) >= 400 else "application/json"
            body = exchange["response"]["body"]
            validate(declared["content"][media]["schema"], body)
            if int(status) >= 400:
                assert body["status"] == int(status)
            else:
                assert body["meta"]["mode"] == "simulation"
        covered.add(oid)
    assert covered == set(operations), "예제가 없는 API"
    assert {m["operation_id"] for m in mapping["operations"]} == set(operations)
    for row in mapping["operations"]:
        path, method, operation = operations[row["operation_id"]]
        assert row == {"operation_id": operation["operationId"], "method": method.upper(), "path": path,
                       "screens": operation["x-screen-ids"], "stage": operation["x-stage"]}
    validate({"$ref": "#/components/schemas/PushPayload"}, fixtures["push_payload"])

    # 단순 구문 검사에서 놓칠 수 있는 위험한 데이터 해석을 검사한다.
    def semantics(value: object) -> None:
        if isinstance(value, dict):
            if value.get("type") == "Polygon":
                assert all(ring[0] == ring[-1] for ring in value["coordinates"]), "닫히지 않은 영역"
            if value.get("type") == "MultiPolygon":
                assert all(ring[0] == ring[-1] for polygon in value["coordinates"] for ring in polygon)
            if "detail_navigation" in value:
                assert value["detail_navigation"] is False
                if value["status"] == "past":
                    assert "발생" not in value["display_title"]
            if "impact" in value:
                impact = value["impact"]
                if impact["status"] == "unavailable":
                    assert impact["probability"] is None
                source_ids = {s["id"] for s in value["sources"]}
                assert set(value["area_source_ids"]) <= source_ids
                assert set(value["relevance"]["evidence_source_ids"]) <= source_ids
                assert all(action["source_id"] in source_ids for action in value["actions"])
                if value["status"] in ("resolved", "expired", "superseded"):
                    assert value["route_availability"]["status"] != "available"
                if value["route_availability"]["status"] == "available":
                    assert value["route_availability"]["expires_at"] is not None
                assert all(tag["origin"] == "user_confirmed" for tag in value["context"]["tags"] if tag["code"] == "alone_now")
            if "proposed_context" in value and value["proposed_context"]:
                assert value["proposed_context"]["requires_user_confirmation"] is True
                assert "confirmation" not in value["proposed_context"]
            if "delivery_status" in value:
                assert value["delivery_status"] == "not_sent"
            if "route" in value and value["status"] == "available":
                assert value["route"]["response_revision"] == value["response_revision"]
                assert datetime.fromisoformat(value["route"]["checked_at"]) < datetime.fromisoformat(value["route"]["valid_until"])
            for child in value.values():
                semantics(child)
        elif isinstance(value, list):
            for child in value:
                semantics(child)

    semantics(fixtures)
    personas = [e['response']['body']['data'] for e in fixtures['exchanges'] if e['id'].startswith('persona_')]
    assert len(personas) == 3
    assert all(p['impact'] == personas[0]['impact'] for p in personas), '이동 능력만으로 환경 영향 확률을 바꾸면 안 됨'
    invalid = [
        ("Impact", {"status": "unavailable", "probability": 0, "target": None, "model_version": None, "reason_codes": ["MISSING_INPUT"]}),
        ("LocationWrite", {**next(e for e in fixtures["exchanges"] if e["id"] == "putLocation")["request"]["body"], "latitude": 100}),
        ("ContextWrite", {**next(e for e in fixtures["exchanges"] if e["id"] == "putCurrentContext")["request"]["body"], "confirmation": "ai_inferred"}),
        ("Route", {"status": "available", "response_revision": 1, "reason_code": None, "route": None, "sources": []}),
    ]
    for name, value in invalid:
        try:
            validate({"$ref": "#/components/schemas/" + name}, value)
        except ValidationError:
            continue
        raise AssertionError("잘못된 입력이 통과함: " + name)
    # 실제 앱 코드 대신, 전달 계약의 필수 억제 조건을 명시적으로 대조한다.
    def may_apply(current_revision: int, incoming_revision: int, valid_until: str) -> bool:
        return incoming_revision > current_revision and datetime.fromisoformat(valid_until) > datetime.fromisoformat(fixtures["reference_clock"])
    assert not may_apply(3, 2, "2026-10-31T03:05:00Z")
    assert not may_apply(3, 3, "2026-10-31T03:05:00Z")
    assert not may_apply(3, 4, "2026-10-31T02:59:00Z")
    assert may_apply(3, 4, "2026-10-31T03:05:00Z")

    docs = [ROOT / "docs/V2/delivery" / name for name in
            ("app-api-contract.md", "api-handoff.md", "api-job-review.md", "api-reference.md")]
    reference = docs[-1].read_text()
    docs += [ROOT / 'docs/README.md', ROOT / 'docs/V2/04-execution-backlog.md']
    for oid, (_, _, operation) in operations.items():
        assert f"id=\"{oid}\"" in reference, f"사용법 문서 누락: {oid}"
        section = reference.split(f'<a id="{oid}"></a>', 1)[1].split('<a id="', 1)[0]
        success = next(v for k, v in operation['responses'].items() if k.startswith('2'))
        if 'content' in success:
            shown = json.loads(re.search(r'```json\n(.*?)\n```', section, re.S).group(1))
            assert shown == success['content']['application/json']['example'], f'사용법 응답 예제 불일치: {oid}'
    for doc in docs:
        for target in re.findall(r"\]\(([^)]+)\)", doc.read_text()):
            if "://" in target or target.startswith("#"):
                continue
            linked = doc.parent / target.split("#", 1)[0]
            generated_report = args.report is not None and linked.resolve() == args.report.resolve()
            assert linked.exists() or generated_report, (doc, target)
    report = {
        "결과": "통과", "계약": spec["info"]["version"], "API수": len(operations), "스키마수": len(schemas),
        "HTTP예제수": len(fixtures["exchanges"]), "푸시예제수": 1, "오류거부검사수": len(invalid),
        "검사": ["OpenAPI 3.1 구조", "JSON Schema 2020-12와 날짜 형식", "모든 API 요청·응답 예제", "화면 매핑과 사용법 누락",
                 "예측 불가와 위치/경로/현재 상태 불변 조건", "오래된 안내 억제 조건 예시", "문서 내부 파일 링크"],
        "한계": "서버 미배포. 실제 인증·푸시·상태 전이·정책·모델·119·3D·음성·동시성 동작을 검증한 결과가 아니다."
    }
    if args.report:
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
