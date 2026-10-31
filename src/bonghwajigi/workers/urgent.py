from bonghwajigi.workers.factory import create_worker

app = create_worker("urgent", "bonghwajigi.workers.urgent")


@app.task(name="bonghwajigi.urgent.process")
def process(event_id: str) -> None:
    # 실제 원문·발령 대상·outbox 처리는 D4에서 구현한다. GPU를 호출하지 않는다.
    raise NotImplementedError("공식 경보 우선 처리기가 아직 구현되지 않았습니다.")
