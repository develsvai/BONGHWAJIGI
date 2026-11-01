"""촬영 자료의 출처·불확실성과 실제 입력 변환 경계를 검사한다."""

import json

from bonghwajigi.contracts.analysis import RegionalConditionsInput, Source
from tools.filming_scenario import DEFAULT_BUNDLE, Replay, role_profile


def make_replay():
    replay = Replay.__new__(Replay)
    replay.bundle = json.loads(DEFAULT_BUNDLE.read_text())
    replay.state = {"created_at": "2026-10-31T19:40:00+00:00"}
    replay.next_revision = lambda *_: 1
    return replay


def test_source_dates_are_valid_and_precision_is_retained():
    replay = make_replay()
    for document in replay.bundle["source_definitions"]:
        source = Source.model_validate(document["source"])
        assert source.published_at <= source.collected_at
        assert document["published_at_precision"]
    assert replay.bundle["official_evacuations"] == []
    assert replay.bundle["official_alerts"][0]["evacuation_order"] is False
    assert replay.bundle["official_alerts"][0]["original_sms_available"] is False


def test_replay_does_not_promote_unobserved_fog_or_synthetic_forest_to_history():
    replay = make_replay()
    body = replay.regional_conditions()
    RegionalConditionsInput.model_validate(body)
    assert body["origin"] == "synthetic"
    assert replay.bundle["regional_facts"]["forest_nearby"] is None
    assert body["forest_nearby"] is True
    assert body["fog_observed"] is None
    assert body["original_observed_at"] is None
    assert body["sources"][0]["published_at"].startswith("2025-")


def test_preprofile_does_not_claim_child_present_or_mobility_incapacity():
    roles = make_replay().bundle["synthetic_staging"]["roles"]
    assert roles["A"]["child_present_before_answer"] is None
    assert roles["B"]["can_move_before_answer"] is None
    assert roles["B"]["alone_before_answer"] is None
    assert roles["A"]["route_state_origin"] == "synthetic"
    assert roles["A"]["route_geometry"] is None


def test_phone_role_changes_preserve_unrelated_profile_and_consent():
    existing = {
        "display_name": "검증 계정",
        "communication": "text",
        "stairs": "difficult",
        "medical_notes": "검증용 문자열",
        "medical_consent": True,
        "mobility": "unknown",
        "dependents": [],
    }
    updated = role_profile(existing, "A")
    assert updated["mobility"] == "independent" and updated["dependents"] == ["child"]
    for key in ("display_name", "communication", "stairs", "medical_notes", "medical_consent"):
        assert updated[key] == existing[key]
    assert existing["mobility"] == "unknown"
