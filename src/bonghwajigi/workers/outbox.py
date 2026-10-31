import argparse
import logging
import time
from datetime import timedelta

from celery import Celery
from kombu import Queue
from sqlalchemy import select

from bonghwajigi.common.config import Settings
from bonghwajigi.db.analysis_models import AnalysisJob, AnalysisOutbox, now
from bonghwajigi.db.session import session_factory


def publisher(settings):
    app = Celery("analysis_dispatcher", broker=settings.broker_url.get_secret_value())
    app.conf.update(
        task_queues=(Queue("analysis"),),
        task_default_queue="analysis",
        task_create_missing_queues=False,
        task_serializer="json",
        accept_content=["json"],
        broker_connection_timeout=3,
        broker_transport_options={"socket_connect_timeout": 3, "socket_timeout": 5},
    )
    return app


def dispatch_once(sessions, sender, redelivery_seconds=180):
    count = 0
    with sessions.begin() as session:
        rows = session.scalars(
            select(AnalysisOutbox)
            .join(AnalysisJob, AnalysisJob.id == AnalysisOutbox.job_id)
            .where(
                AnalysisOutbox.next_dispatch_at <= now(),
                AnalysisJob.status.in_(["queued", "processing", "retry"]),
            )
            .order_by(AnalysisOutbox.next_dispatch_at)
            .limit(20)
            .with_for_update(skip_locked=True, of=AnalysisOutbox)
        ).all()
        for row in rows:
            try:
                sender.send_task(
                    "bonghwajigi.analysis.process",
                    args=[row.job_id],
                    queue="analysis",
                    task_id=f"{row.id}:{row.dispatch_count}",
                    retry=False,
                )
            except Exception:
                row.error_code = "BROKER_UNAVAILABLE"
                row.next_dispatch_at = now() + timedelta(seconds=5)
                continue
            row.dispatch_count += 1
            row.error_code = None
            row.next_dispatch_at = now() + timedelta(seconds=redelivery_seconds)
            count += 1
    return count


def main():
    parser = argparse.ArgumentParser(description="DB outbox를 분석 큐로 전달한다.")
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    settings = Settings()
    if not settings.analysis_enabled or not settings.broker_url:
        parser.exit(2, "분석 흐름과 DB·브로커 설정이 필요합니다.\n")
    sessions, sender = session_factory(settings), publisher(settings)
    while True:
        try:
            count = dispatch_once(sessions, sender, settings.outbox_redelivery_seconds)
            if args.once:
                print({"published": count})
                return
        except Exception:
            logging.error("OUTBOX_DISPATCH_FAILED")
            if args.once:
                raise SystemExit(1) from None
        time.sleep(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
