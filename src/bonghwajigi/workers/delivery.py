from bonghwajigi.workers.factory import create_worker

app = create_worker("delivery", "bonghwajigi.workers.delivery")


@app.task(name="bonghwajigi.delivery.send")
def send(delivery_id: str) -> None:
    raise NotImplementedError("실제·모의 알림 전달기가 아직 구현되지 않았습니다.")
