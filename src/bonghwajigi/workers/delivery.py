from bonghwajigi.workers.factory import create_worker

app = create_worker("delivery", "bonghwajigi.workers.delivery")


@app.task(name="bonghwajigi.delivery.send")
def send(delivery_id: str) -> None:
    from bonghwajigi.common.config import Settings
    from bonghwajigi.db.session import session_factory
    from bonghwajigi.notifications.delivery import send_delivery
    from bonghwajigi.notifications.providers import DisabledSender, configured_sender

    settings = Settings()
    sessions = session_factory(settings)
    try:
        try:
            sender = configured_sender(settings)
        except Exception:
            sender = DisabledSender()
        send_delivery(
            sessions, sender, delivery_id, resource_id_key=settings.jwt_secret.get_secret_value()
        )
    finally:
        sessions.kw["bind"].dispose()
