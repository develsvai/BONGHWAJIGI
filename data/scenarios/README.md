# MVP 시나리오 자료

MVP는 실제 K8s 상시 수집 없이, 수동 확보한 자료·뉴스·합성 자료를 시나리오로 재생한다. K8s 구성은 후속 수집을 위해 보존한다.

재생 경로는 JSONL 자료 → 이벤트 수신 API → DB/outbox → 분석 큐다. 분석 경로는 인터넷 뉴스와 저장 자료를 임베딩 검색해 Qwen 호출 직전 자료까지 만드는 단계가 구현되어 있다. urgent 수신과 실제 K8s 수집은 아직 구현하지 않았다. 각 행은 `bonghwajigi.contracts.scenarios.ScenarioEvent`, analysis payload는 `AnalysisInput`을 따른다.

- `mode`: 항상 `simulation`
- `scenario_id`, `event_id`: 재생 시나리오와 중복 처리를 위한 식별자
- `origin`: `synthetic`, `historical_replay`, `collected_sample` 중 자료의 실제 성격
- `queue`: `urgent` 또는 `analysis`
- `payload`: 원문 출처·시각 등을 포함할 후속 자료 계약의 객체

```sh
uv run --no-sync python -m bonghwajigi.ingestion.replay /path/to/scenario.jsonl --check
```

`analysis-event.jsonl`과 `retrieval-document.json`은 합성 입력 형식 예제다. `example.invalid`는 실제 출처가 아니다. 현재 시각으로 인터넷 검색까지 자동 시연하려면 [분석 흐름 안내](../../docs/V2/delivery/analysis-retrieval-flow.md)의 실행 도구를 사용한다.

`yeongdeok-integration.json`은 공식 게시물의 산불 경보 발령 기록과 행동요령 요약을 포함한 과거 재생 입력이다. 발령 기록은 현재 경보나 직접 수신한 재난문자 원본이 아니다. 실행할 때 별도 scenario ID와 실제 수집 시각을 부여하고, 지역·과거 시점으로 뉴스를 검색한 뒤 실제 Qwen3를 호출한다. [통합 결과와 사용법](../../docs/V2/delivery/qwen-integration-result.md)을 따른다.

실제 수집 원본은 `data/raw/`에 두고 Git에 넣지 않는다. 재사용 가능한 시연 자료도 출처·사용 조건과 개인정보를 검토한 뒤 포함한다. 대표 재난 사례·정답·대응 레벨은 이 예제로 확정하지 않는다.

`policy-loop-rules.json`은 DB 지침과 사용자별 조건 적용·버전 갱신을 확인하는 합성 규칙이다. `simulation_only`이며 운영 승인이나 대응 단계 확정을 뜻하지 않는다. `run_policy_loop_demo.py`가 개인별 계획까지 이어지는 실제 큐·Qwen 처리와 사용자 변경·주기 만료를 시연한다. 사용한 사용자·좌표·사각 구역·확률은 전부 합성이며 학습 모델의 국내 실제 예측값으로 제시하지 않는다.
