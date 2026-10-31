# MVP 시나리오 자료

MVP는 실제 K8s 상시 수집 없이, 수동 확보한 자료·뉴스·합성 자료를 시나리오로 재생한다. K8s 구성은 후속 수집을 위해 보존한다.

재생 경로는 JSONL 자료 → 이벤트 수신 API → DB/outbox → urgent 또는 analysis 큐다. 현재는 입력 검사와 미준비 수신 경로만 있으며 실제 DB·큐 적재는 후속 구현한다. 각 행은 `bonghwajigi.contracts.scenarios.ScenarioEvent` 초안에 맞춘다.

- `mode`: 항상 `simulation`
- `scenario_id`, `event_id`: 재생 시나리오와 중복 처리를 위한 식별자
- `origin`: `synthetic`, `historical_replay`, `collected_sample` 중 자료의 실제 성격
- `queue`: `urgent` 또는 `analysis`
- `payload`: 원문 출처·시각 등을 포함할 후속 자료 계약의 객체

```sh
uv run --no-sync python -m bonghwajigi.ingestion.replay /path/to/scenario.jsonl --check
```

실제 수집 원본은 `data/raw/`에 두고 Git에 넣지 않는다. 재사용 가능한 시연 자료도 출처·사용 조건과 개인정보를 검토한 뒤 포함한다. 아직 대표 사례나 재생 시각, 정답·대응 레벨을 임의로 고정하지 않았다.
