from bonghwajigi.workers.factory import create_worker

app = create_worker("analysis", "bonghwajigi.workers.analysis")


@app.task(name="bonghwajigi.analysis.process")
def process(event_id: str) -> None:
    raise NotImplementedError("사건 통합·검색·모델·정책 분석기가 아직 구현되지 않았습니다.")
