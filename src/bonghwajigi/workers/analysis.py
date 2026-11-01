import logging

from bonghwajigi.workers.factory import create_worker

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

app = create_worker("analysis", "bonghwajigi.workers.analysis")
app.conf.update(
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_soft_time_limit=90,
    task_time_limit=120,
    broker_transport_options={"visibility_timeout": 180, "socket_connect_timeout": 3},
)


@app.task(name="bonghwajigi.analysis.process")
def process(job_id: str) -> dict:
    from bonghwajigi.common.config import Settings
    from bonghwajigi.db.session import session_factory
    from bonghwajigi.retrieval.embedding import EmbeddingClient
    from bonghwajigi.retrieval.pipeline import run_job
    from bonghwajigi.retrieval.web_search import NewsSearch

    settings = Settings()
    if not settings.analysis_enabled:
        raise RuntimeError("분석 흐름이 비활성화되어 있습니다.")
    sessions = session_factory(settings)
    client = EmbeddingClient(settings)
    try:
        return run_job(
            job_id,
            sessions,
            client,
            NewsSearch(
                settings.web_search_max_results, lookback_days=settings.web_search_lookback_days
            ),
            settings,
        )
    finally:
        client.close()
        sessions.kw["bind"].dispose()
