from datetime import timedelta

from sqlalchemy import select

from bonghwajigi.common.public_ids import opaque_resource_id
from bonghwajigi.db.analysis_models import new_id, now
from bonghwajigi.db.delivery_models import Delivery, Device
from bonghwajigi.db.policy_models import PolicyEntity, PolicyProjection
from bonghwajigi.notifications.providers import PushError


def dispatch_deliveries(session, publisher, redelivery_seconds):
    count = 0
    rows = session.scalars(
        select(Delivery)
        .where(
            Delivery.status.in_(["pending", "retry", "processing"]),
            Delivery.next_attempt_at <= now(),
            Delivery.next_dispatch_at <= now(),
        )
        .order_by(Delivery.created_at)
        .limit(20)
        .with_for_update(skip_locked=True)
    ).all()
    for row in rows:
        try:
            publisher.send_task(
                "bonghwajigi.delivery.send",
                args=[row.id],
                queue="delivery",
                task_id=f"{row.id}:{row.dispatch_count}",
                retry=False,
            )
        except Exception:
            row.error_code = "BROKER_UNAVAILABLE"
            row.next_dispatch_at = now() + timedelta(seconds=5)
            continue
        row.dispatch_count += 1
        row.next_dispatch_at = now() + timedelta(seconds=redelivery_seconds)
        count += 1
    return count


def stale(session, row):
    incident_id = row.resource_id.split("/", 1)[0]
    incident = session.get(PolicyEntity, (row.scenario_id, "incident", incident_id))
    if incident and incident.body.get("feed_visibility") == "archived":
        return True
    if row.resource_type == "response":
        projection = session.scalar(
            select(PolicyProjection).where(
                PolicyProjection.scenario_id == row.scenario_id,
                PolicyProjection.user_id == row.user_id,
                PolicyProjection.incident_id == row.resource_id,
            )
        )
        return (
            not projection
            or projection.revision != row.revision
            or projection.requested > projection.applied
        )
    entity = session.get(PolicyEntity, (row.scenario_id, "alert", row.resource_id))
    return not entity or entity.revision != row.revision


def send_delivery(sessions, sender, identifier, *, resource_id_key):
    lease, payload, token, urgency = new_id(), None, None, None
    with sessions.begin() as session:
        row = session.scalar(select(Delivery).where(Delivery.id == identifier).with_for_update())
        if (
            not row
            or row.status not in {"pending", "retry", "processing"}
            or row.next_attempt_at > now()
        ):
            return False
        device = session.get(Device, row.device_id)
        if not device or not device.enabled or device.revision != row.device_revision:
            row.status = "device_revoked"
            return True
        if row.expires_at <= now():
            row.status = "expired"
            return True
        if stale(session, row):
            row.status = "superseded"
            return True
        row.status, row.lease_id = "processing", lease
        row.attempts += 1
        row.next_attempt_at = now() + timedelta(seconds=60)
        payload, token, urgency = dict(row.payload), device.token, row.urgency
        if row.resource_type == "alert":
            # DB 내부 ID는 만료·취소·중복 판정에 유지하고 전송용 ID만 인증 API와 맞춘다.
            payload["resource_id"] = opaque_resource_id(
                resource_id_key, row.scenario_id, row.user_id, "alert", row.resource_id
            )
    # 외부 네트워크 호출 동안 DB 트랜잭션과 행 잠금을 유지하지 않는다.
    result, provider_id, error = None, None, None
    try:
        result, provider_id = sender.send(token, payload, urgency)
    except PushError as exc:
        error = exc
    except Exception:
        error = PushError("PUSH_EXECUTION_FAILED", retryable=True)
    with sessions.begin() as session:
        row = session.scalar(select(Delivery).where(Delivery.id == identifier).with_for_update())
        if row.lease_id != lease:
            return True
        if error:
            row.error_code = error.code
            row.status = "retry" if error.retryable and row.attempts < 5 else "failed"
            if error.code == "PUSH_NOT_CONFIGURED":
                row.status = "disabled"
            row.next_attempt_at = now() + timedelta(seconds=min(300, 2**row.attempts))
            row.next_dispatch_at = row.next_attempt_at
            if error.unregister:
                device = session.get(Device, row.device_id)
                if device and device.revision == row.device_revision:
                    device.enabled, device.token, device.token_hash = False, None, None
        else:
            row.status, row.provider_message_id, row.error_code = result, provider_id, None
    return True
