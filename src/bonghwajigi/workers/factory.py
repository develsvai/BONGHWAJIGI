from celery import Celery
from kombu import Queue

from bonghwajigi.common.config import Settings

QUEUES = ("urgent", "analysis", "delivery")


def create_worker(queue: str, task_module: str) -> Celery:
    if queue not in QUEUES:
        raise ValueError("알 수 없는 워커 큐")
    settings = Settings()
    if settings.broker_url is None or not settings.broker_url.get_secret_value().strip():
        raise RuntimeError("BONGHWA_BROKER_URL을 설정해야 워커를 시작할 수 있습니다.")
    app = Celery(
        f"bonghwajigi.{queue}",
        broker=settings.broker_url.get_secret_value(),
        include=[task_module],
    )
    app.conf.update(
        task_queues=(Queue(queue),),
        task_default_queue=queue,
        task_create_missing_queues=False,
        task_routes={f"bonghwajigi.{name}.*": {"queue": name} for name in QUEUES},
        task_serializer="json",
        accept_content=["json"],
        task_ignore_result=True,
        worker_prefetch_multiplier=1,
        worker_concurrency=1,
        broker_connection_retry_on_startup=True,
        timezone="UTC",
        enable_utc=True,
    )
    return app
