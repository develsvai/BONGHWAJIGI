from bonghwajigi.workers.factory import create_worker

app = create_worker("urgent", "bonghwajigi.workers.urgent")


@app.task(name="bonghwajigi.urgent.process")
def process(event_id: str) -> None:
    from bonghwajigi.common.config import Settings
    from bonghwajigi.db.session import session_factory
    from bonghwajigi.events.urgent import process_urgent

    sessions = session_factory(Settings())
    try:
        process_urgent(sessions, event_id)
    finally:
        sessions.kw["bind"].dispose()
