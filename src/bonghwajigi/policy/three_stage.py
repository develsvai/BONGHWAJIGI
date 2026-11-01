"""사용자가 확정한 MVP 정책. 예측 확률이나 생성 문장으로 단계를 결정하지 않는다."""

from datetime import timedelta

from bonghwajigi.contracts.analysis import Source
from bonghwajigi.contracts.policy import GuidanceInput, RuleSetInput

POLICY_VERSION = "wildfire-three-stage-v1"
LABELS = {
    "prepare": "경고",
    "act": "대피",
    "request_assistance": "위급",
    "information": "대피 후 확인",
    "unknown": "확인 중",
}
RANK = {"unknown": 0, "information": 0, "prepare": 1, "act": 2, "request_assistance": 3}
GUIDES = {
    "ready-bag": "대피할 때 바로 챙길 수 있도록 비상가방을 미리 준비해 두세요.",
    "ready-bag-check": "평소 준비한 비상용품의 보관 위치와 사용 가능한 상태를 확인하세요.",
    "ready-helper": "이동을 도와줄 사람과 미리 연락 방법을 정하고 함께 대피할 준비를 해두세요.",
    "ready-dependent": "함께 대피할 보호 대상과 미리 연락 방법과 만날 장소를 정해두세요.",
    "ready-child": "아이에게 필요한 물·간식·여벌 옷을 비상가방에 챙기세요.",
    "ready-aid": "평소 사용하는 보조기구가 바로 사용 가능한지 확인하세요.",
    "ready-local": "주변 산림과 입산 통제 정보를 확인하고 가족과 연락 방법을 정해두세요.",
    "regional-dry": ("건조한 산림 주변에서는 불씨에 주의하고 입산 통제 정보를 확인하세요."),
    "regional-fog": "주변 지역에서 안개가 관측됐어요. 시야를 확인하고 이동할 때 주의하세요.",
    "regional-forest": "산림 주변에서는 불씨를 조심하고 입산 통제 정보를 확인하세요.",
    "avoid-entry": "입산통제구역과 폐쇄된 등산로에 들어가지 마세요.",
    "avoid-direction": "산불이 번지는 방향이나 산과 가까운 위험한 길로 이동하지 마세요.",
    "prepare-follow": "공식 대피 안내와 재난문자를 확인하고 대피할 장소를 확인하세요.",
    "prepare-bag": "즉시 이동할 수 있도록 비상용품과 가방을 준비하세요.",
    "prepare-helper": "이동을 도와줄 사람에게 지금 연락하고 함께 이동할 방법을 준비하세요.",
    "act-follow": "관계자의 대피 안내에 따라 안내된 장소로 즉시 이동하세요.",
    "act-assist": "혼자 이동하기 어렵다면 주변 사람이나 조력자에게 도움을 요청해 함께 이동하세요.",
    "act-child": "아이와 떨어지지 않도록 손을 잡고 함께 대피하세요.",
    "assist-child": (
        "아이와 떨어지지 마세요. 119에 현재 위치와 아이 동반·경로 통제 상황을 알리세요."
    ),
    "assist-child-stay": (
        "아이와 떨어지지 마세요. 119에 현재 위치와 아이 동반·도움이 필요한 상황을 알리세요."
    ),
    "act-aid": "보조기구를 챙기고 관계자의 대피 안내에 따라 이동하세요.",
    "assist-call": "119에 연락해 현재 위치와 대피할 수 없는 상황을 알리고 도움을 요청하세요.",
    "assist-location": (
        "알고 있는 주소나 주변 지형지물, 함께 있는 인원과 이동에 필요한 도움을 알리세요."
    ),
    "assist-follow": (
        "구조기관의 안내를 따르세요. 안내를 받는 동안에도 신고 연결 수단을 사용할 수 있습니다."
    ),
    "information-arrived": (
        "부상 여부를 확인하고 가족이나 지인에게 현재 상황을 알리세요. "
        "귀가는 관할 기관의 안내를 따르세요."
    ),
}


def bootstrap(session, scenario, moment):
    from bonghwajigi.db.policy_models import PolicyEntity
    from bonghwajigi.policy.service import put_entity

    current = session.get(PolicyEntity, (scenario, "rules", "active"))
    unchanged = current and current.body.get("policy_version") == POLICY_VERSION

    # 이 시각은 정규화한 지침 버전의 게시 시각이다. 원본 웹페이지의 최초 게시일은 미확인이다.
    source = Source(
        title="국민안전24 산불 행동요령 확인본",
        url="https://www.safekorea.go.kr/safekorea-kor/acts/nacts/action-guide.do?category=forestFires&menuSn=4",
        published_at=moment,
        collected_at=moment,
        verified=True,
    )
    for identifier, text in GUIDES.items():
        if unchanged and session.get(PolicyEntity, (scenario, "guidance", "mvp-" + identifier)):
            continue
        put_entity(
            session,
            scenario,
            "guidance",
            "mvp-" + identifier,
            GuidanceInput(
                revision=1,
                review_state="approved_mvp",
                text=text,
                source=source,
                valid_from=moment,
                expires_at=moment + timedelta(days=30),
            ),
        )
    if unchanged:
        return {"revision": current.revision, "duplicate": True}
    return put_entity(
        session,
        scenario,
        "rules",
        "active",
        RuleSetInput(
            revision=current.revision + 1 if current else 1,
            review_state="approved_mvp",
            policy_version=POLICY_VERSION,
            rules=[],
        ),
    )


def decide(profile, state, environment, route, alerts, previous, related):
    reasons, questions = [], []
    mobility = state.get("mobility_override") or profile.get("mobility", "unknown")
    if profile.get("mobility_assistance") and mobility == "unknown":
        mobility = "needs_time"
    if state.get("can_move") is False:
        mobility = "requires_help"
    child_present = state.get("child_present") is True
    needs_time = mobility in {"needs_time", "requires_help"} or child_present
    helper = state.get("helper_present") is True and state.get("alone_now") != "yes"
    hazard = state.get("observed_hazard", "unknown")
    active = [
        a
        for a in alerts
        if a["record_status"] == "active_record" and a["user_relevance"] == "inside"
    ]
    evacuation = any(a.get("instruction_kind") == "evacuate" for a in active)
    prepare_notice = any(a.get("instruction_kind") == "prepare" for a in active)
    band = environment.get("hazard_band", "unknown") if related else "unknown"
    if evacuation or hazard in {"smoke", "flames", "fear", "trapped"}:
        band = "H3"
    if band == "unknown" and prepare_notice:
        band = "H1"
    level = "unknown"
    if hazard == "trapped" or (state.get("injured") is True and state.get("can_move") is False):
        level, reasons = "request_assistance", ["USER_CANNOT_EVACUATE"]
    elif band in {"H2", "H3"} and route.get("status") == "blocked":
        level, reasons = "request_assistance", ["NO_AVAILABLE_EVACUATION_ROUTE"]
    elif band == "H3":
        level = "request_assistance" if mobility == "requires_help" and not helper else "act"
        reasons.append("OFFICIAL_EVACUATION" if evacuation else "IMMEDIATE_LOCAL_HAZARD")
        if level == "request_assistance":
            reasons.append("HELPER_NOT_PRESENT")
    elif band == "H2":
        level = "act" if needs_time else "prepare"
        reasons.append("EARLY_MOVEMENT_SUPPORT" if needs_time else "PREPARE_FOR_APPROACHING_FIRE")
        if mobility == "unknown":
            questions.append("지금 스스로 이동할 수 있나요?")
        elif mobility == "requires_help" and not helper:
            questions.append(
                "지금 이동을 도울 사람이 곁에 있나요? "
                "도움이 확보되지 않으면 즉시 지원을 요청하세요."
            )
    elif band == "H1":
        level, reasons = "prepare", ["RELATED_FIRE_PREPARATION"]
    if state.get("evacuation_status") == "arrived" and level != "request_assistance":
        level, reasons = "information", ["USER_REPORTED_ARRIVAL_NOT_SAFETY_CLEARANCE"]
    old = (previous or {}).get("personal_response", {}).get("level", "unknown")
    if level not in {"unknown", "information"} and RANK[level] < RANK.get(old, 0):
        recovered = (
            old == "request_assistance"
            and level == "act"
            and route.get("status") == "open"
            and (mobility != "requires_help" or helper)
        )
        confirmed = state.get("deescalation_confirmed") is True and band == "H1" and not evacuation
        if not recovered and not confirmed:
            level = old
            reasons.append("DEESCALATION_REQUIRES_FRESH_CONFIRMATION")
    ids = {
        "unknown": [],
        "prepare": ["prepare-follow", "prepare-bag"],
        "act": ["act-follow"],
        "request_assistance": ["assist-call", "assist-location", "assist-follow"],
        "information": ["information-arrived"],
    }[level].copy()
    if level == "prepare" and needs_time:
        ids.insert(0, "prepare-helper")
    if level == "act" and mobility in {"needs_time", "requires_help"}:
        ids.append("act-assist")
    if level == "act" and child_present:
        ids.append("act-child")
    if level == "request_assistance" and child_present:
        ids.append("assist-child" if route.get("status") == "blocked" else "assist-child-stay")
    if level == "act" and profile.get("assistive_device") and state.get("can_move") is True:
        ids.append("act-aid")
    # Questions refine current observations after the level is already determined. They do
    # not delay emergency guidance or turn a potential companion into a present companion.
    if level in {"prepare", "act", "request_assistance"}:
        if profile.get("child_registered") and state.get("child_present") is None:
            questions = ["지금 아이와 함께 계신가요?"]
        elif profile.get("assistive_device") and state.get("can_move") is None:
            questions = ["보조기구를 사용해 혼자 이동할 수 있나요?"]
        elif level == "request_assistance":
            questions = []
    return {
        "level": level,
        "number": RANK[level] or None,
        "label": LABELS[level],
        "policy_version": POLICY_VERSION,
        "hazard_band": band,
        "reason_codes": reasons,
        "questions": questions[:1],
        "support_available": True,
        "automatic_emergency_call": False,
    }, ["mvp-" + i for i in ids]
