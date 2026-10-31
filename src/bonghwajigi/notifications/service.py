from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from bonghwajigi.db.analysis_models import now
from bonghwajigi.db.delivery_models import ChangeSequence, Delivery, Device, UserChange


def emit_change(
    session, scenario, user, kind, identifier, revision, *, urgency=None, expires_at=None
):
    # 호출자는 scope_lock을 먼저 획득한다. 같은 scope의 커밋 순서와 cursor 순서를 일치시킨다.
    session.execute(
        insert(ChangeSequence).values(scenario_id=scenario, value=0).on_conflict_do_nothing()
    )
    sequence = session.scalar(
        select(ChangeSequence).where(ChangeSequence.scenario_id == scenario).with_for_update()
    )
    sequence.value += 1
    session.add(
        UserChange(
            scenario_id=scenario,
            user_id=user,
            sequence=sequence.value,
            resource_type=kind,
            resource_id=identifier,
            revision=revision,
        )
    )
    if urgency is None:
        return
    for device in session.scalars(
        select(Device).where(
            Device.scenario_id == scenario,
            Device.user_id == user,
            Device.enabled.is_(True),
        )
    ).all():
        # 푸시에는 프로필·정밀 위치·경보 원문을 넣지 않는다. 인증된 API에서 최신 내용을 조회한다.
        session.execute(
            insert(Delivery)
            .values(
                scenario_id=scenario,
                user_id=user,
                device_id=device.id,
                device_revision=device.revision,
                resource_type=kind,
                resource_id=identifier,
                revision=revision,
                urgency=urgency,
                payload={
                    "mode": "simulation",
                    "resource_type": kind,
                    "resource_id": identifier,
                    "revision": str(revision),
                },
                expires_at=expires_at or now() + timedelta(minutes=10),
            )
            .on_conflict_do_nothing(
                index_elements=["device_id", "resource_type", "resource_id", "revision"]
            )
        )


def plan_changed(session, row, old):
    content = row.content
    level = content["personal_response"]["level"]
    ranks = {"unknown": 0, "information": 0, "prepare": 1, "act": 2, "request_assistance": 3}
    before = (old or {}).get("personal_response", {}).get("level", "unknown")
    changed_actions = (old or {}).get("actions") != content["actions"]
    urgency = None
    if ranks.get(level, 0) >= 2 and (ranks[level] > ranks.get(before, 0) or changed_actions):
        urgency = "urgent" if level == "request_assistance" else "high"
    elif level == "prepare" and ranks.get(before, 0) == 0:
        urgency = "normal"
    emit_change(
        session,
        row.scenario_id,
        row.user_id,
        "response",
        row.incident_id,
        row.revision,
        urgency=urgency,
    )
