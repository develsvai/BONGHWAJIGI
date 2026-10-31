"""Reviewed home cards based on valid location and sourced regional observations."""

from sqlalchemy import select

from bonghwajigi.db.policy_models import PolicyEntity
from bonghwajigi.policy.service import at, fresh, relevance
from bonghwajigi.policy.three_stage import POLICY_VERSION


def guide(session, scenario, identifier, moment):
    row = session.get(PolicyEntity, (scenario, "guidance", identifier))
    if (
        not row
        or row.body["review_state"] != "approved_mvp"
        or not row.body["source"]["verified"]
        or at(row.body["source"]["published_at"]) > moment
        or not fresh(row.body, moment, "valid_from")
    ):
        return None
    return {
        "id": identifier,
        "text": row.body["text"],
        "source": row.body["source"],
        "revision": row.revision,
        "valid_until": row.body["expires_at"],
    }


def regional_observation(session, actor, moment):
    scenario, user = actor["scenario_id"], actor["sub"]
    location = session.get(PolicyEntity, (scenario, "location", user))
    if not location or not fresh(location.body, moment):
        return location, None
    rows = session.scalars(
        select(PolicyEntity).where(
            PolicyEntity.scenario_id == scenario, PolicyEntity.kind == "regional_conditions"
        )
    ).all()
    eligible = [
        row
        for row in rows
        if (
            fresh(row.body, moment)
            and all(
                source["verified"] and at(source["published_at"]) <= moment
                for source in row.body["sources"]
            )
            and relevance(location.body, row.body["area"], moment)[0] == "inside"
        )
    ]
    return location, max(
        eligible, key=lambda r: (at(r.body["observed_at"]), r.revision), default=None
    )


def today_guidance(session, actor, moment):
    location, observation = regional_observation(session, actor, moment)
    items = []
    if observation:
        conditions = observation.body
        selected = []
        if conditions.get("forest_nearby") is True:
            selected.append(
                ("regional-dry", "건조한 산림 화재 주의")
                if conditions.get("dry_warning") is True
                else ("regional-forest", "주변 산림 화재 예방")
            )
        if conditions.get("fog_observed") is True:
            selected.append(("regional-fog", "관측된 안개에 주의"))
        for identifier, title in selected:
            item = guide(session, actor["scenario_id"], "mvp-" + identifier, moment)
            if item:
                items.append(
                    {
                        **item,
                        "title": title,
                        "evidence": conditions["sources"],
                        "origin": conditions["origin"],
                        "original_observed_at": conditions.get("original_observed_at"),
                        "valid_until": min(
                            at(item["valid_until"]),
                            at(conditions["expires_at"]),
                            at(location.body["expires_at"]),
                        ),
                    }
                )
    return {
        "status": "available" if items else "unavailable",
        "location_input_revision": location.revision if location else 0,
        "generated_at": moment,
        "valid_until": min((item["valid_until"] for item in items), default=None),
        "reason_codes": [] if items else ["REGIONAL_EVIDENCE_OR_LOCATION_UNAVAILABLE"],
        "items": items,
    }


def preparations(session, actor, moment):
    scenario, user = actor["scenario_id"], actor["sub"]
    profile = session.get(PolicyEntity, (scenario, "app_profile", user))
    values = profile.body["data"] if profile else {}
    location, observation = regional_observation(session, actor, moment)
    second, title, reason = "ready-bag-check", "비상용품 상태 확인", "BASIC_PREPARATION"
    if "child" in values.get("dependents", []):
        second, title, reason = "ready-child", "어린이 비상용품 준비", "CHILD_PREPARATION"
    elif values.get("mobility") in {"walking_aid", "wheelchair"}:
        second, title, reason = "ready-aid", "이동 보조기구 점검", "MOBILITY_PREPARATION"
    elif values.get("mobility") == "assistance_required" or values.get("stairs") in {
        "difficult",
        "unable",
    }:
        second, title, reason = "ready-helper", "이동 도움 준비", "MOBILITY_PREPARATION"
    elif values.get("dependents"):
        second, title, reason = "ready-dependent", "보호 대상과 연락 계획", "DEPENDENT_PREPARATION"
    elif observation and observation.body.get("forest_nearby") is True:
        second, title, reason = (
            "ready-local",
            "주변 산림과 통제 정보 확인",
            "LOCAL_FOREST_PREPARATION",
        )
    items = []
    for identifier, kind, item_title, item_reason in [
        ("ready-bag", "common", "비상가방 준비", "BASIC_PREPARATION"),
        (second, "personal", title, reason),
    ]:
        item = guide(session, scenario, "mvp-" + identifier, moment)
        if not item:
            items = []
            break
        if identifier == "ready-local":
            item["valid_until"] = min(
                at(item["valid_until"]),
                at(location.body["expires_at"]),
                at(observation.body["expires_at"]),
            )
        items.append({**item, "kind": kind, "title": item_title, "reason_code": item_reason})
    return {
        "status": "available" if len(items) == 2 else "unavailable",
        "policy_version": POLICY_VERSION,
        "profile_revision": profile.revision if profile else 0,
        "location_input_revision": location.revision if location else 0,
        "generated_at": moment,
        "items": items,
    }
