# 시나리오 입력부터 분석·검색과 Qwen 전달 직전까지

기준일: 2026-10-31 KST. Loom Task: `task-20261031-095141-qwen-9e2979ea`.

사용자 지시에 따라 실제 K8s 수집 없이 시나리오 데이터를 받는다. 추가 검색은 **저장 자료와 인터넷 뉴스 모두** 포함한다. 마지막 산출물은 출처가 붙은 `ready_for_qwen` 자료이며 Qwen 생성·사건 통합·영향 예측·개인 정책·알림은 실행하지 않는다.

```mermaid
flowchart LR
    S["확보 자료 · 시나리오 JSONL"] --> A["이벤트 수신 API"]
    A --> D[("PostgreSQL: 입력 + outbox")]
    D --> O["outbox 전달기"]
    O --> R["Redis analysis 큐"]
    R --> W["분석 전용 Celery 워커"]
    W --> N["인터넷 뉴스 검색"]
    N --> E["문서·질의 임베딩 API"]
    W --> E
    E --> V[("pgvector: 저장 자료 + 웹 자료")]
    V --> P["출처·시각·버전이 있는 Qwen 전달 자료"]
```

## 실행 위치와 현재 상태

API·DB·Redis·분석 워커는 이 Mac의 별도 로컬 환경에서, 임베딩은 기존 GPU 서버에서 실제 연결 검증했다. GPU localhost API에는 SSH 터널로 접근했다. 일반 서버에 이 흐름을 배포하거나 K8s·공개 포트·Tailnet 정책을 바꾸지 않았다.

검증용 `.env.analysis`는 이 Mac에 권한 600으로 준비했으며 Git에서 제외한다. 내부 수신 API 토큰과 GPU 임베딩 토큰은 다른 설정으로 분리했다. 새 환경에서는 `.env.example`을 기준으로 아래 항목을 별도로 주입한다.

| 설정 | 현재 로컬 검증 값·의미 |
| --- | --- |
| `BONGHWA_ANALYSIS_ENABLED` | `true`일 때 실제 분석 경로 활성화 |
| `BONGHWA_DATABASE_URL` | localhost `15432`, DB `bonghwajigi_analysis` |
| `BONGHWA_BROKER_URL` | `redis://127.0.0.1:16379/0` |
| `BONGHWA_SERVICE_TOKEN` | 내부 시나리오·자료·결과 API 인증 |
| `BONGHWA_GPU_BASE_URL` | SSH 터널의 `http://127.0.0.1:18001` |
| `BONGHWA_EMBEDDING_SERVICE_TOKEN` | 기존 GPU 서비스 토큰. 출력·커밋하지 않음 |
| `BONGHWA_EMBEDDING_REVISION` | `97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3` |
| `BONGHWA_WEB_SEARCH_ENABLED` | 기본 `true` |
| `BONGHWA_WEB_SEARCH_MAX_RESULTS` | 기본 5, 최대 10 |
| `BONGHWA_WEB_SEARCH_LOOKBACK_DAYS` | 기본 7일. 시나리오 `as_of` 기준 |
| `BONGHWA_RETRIEVAL_TOP_K` | 기본 5, 최대 10 |
| `BONGHWA_OUTBOX_REDELIVERY_SECONDS` | 기본 180초. 미완료 작업의 재전달 간격 |

## 로컬에서 재현하기

저장소 루트에서 의존성과 DB·큐를 준비한다. 아래 DB 비밀번호는 개발 컨테이너 전용이며 원격 SSH 계정과 무관하다.

```sh
uv sync --frozen --extra server --extra collector --group api-contract
docker compose -f deploy/compose/analysis-dev.yaml up -d --wait
BONGHWA_ENV_FILE=.env.analysis uv run --no-sync alembic upgrade head
```

다른 터미널에서 GPU 터널을 유지한다.

```sh
ssh -N -L 127.0.0.1:18001:127.0.0.1:8001 inno-gpu-011
```

다시 저장소 터미널에서 API·워커·outbox를 함께 실행한다.

```sh
BONGHWA_ENV_FILE=.env.analysis uv run --no-sync python tools/serve_analysis.py
```

별도 터미널에서 전체 시연을 실행한다.

```sh
BONGHWA_ENV_FILE=.env.analysis uv run --no-sync python tools/run_analysis_demo.py
```

도구는 새 scenario ID로 합성 저장 자료를 적재하고, 그 인덱싱이 끝나면 현재 시각의 합성 관측 이벤트를 제출한다. 같은 이벤트를 재전송해 동일 job ID인지 검사한다. 실제 워커 결과는 `data/artifacts/analysis-demo.json`에 저장한다. 이 파일은 Git에 포함하지 않는다.

`serve_analysis.py`는 개발용 localhost·단일 워커 실행기이며 Ctrl+C로 자식 프로세스를 정리한다. 검증용 DB·Redis는 `docker compose -f deploy/compose/analysis-dev.yaml stop`으로 중지하며 볼륨은 유지한다. 일반 서버의 상시 배치는 후속 작업이다.

## 입력 API와 수신 의미

모든 경로는 내부 Bearer 서비스 토큰을 요구한다. 기존 앱 `/v1` 명세와 별개의 내부 계약이다.

| 경로 | 역할 |
| --- | --- |
| `POST /internal/v1/retrieval-documents` | 저장 자료·지침·뉴스를 받아 인덱싱 작업과 outbox를 DB에 함께 기록 |
| `POST /internal/v1/scenario-events` | `queue=analysis`인 시나리오 관측 입력과 outbox를 함께 기록 |
| `GET /internal/v1/scenarios/{scenario_id}/analysis-jobs/{job_id}` | 작업 상태·오류·완성 자료 조회. 다른 scenario이면 404 |
| `POST /internal/v1/scenarios/{scenario_id}/analysis-jobs/{job_id}/retry` | 실패한 작업만 재시도. 완료된 결과를 임의로 다시 쓰지 않음 |
| `GET /internal/v1/analysis-health` | 현재 분석 DB와 브로커 연결 검사 |

202는 **입력과 작업이 DB에 내구성 있게 기록됨**을 뜻한다. 브로커 전달이나 분석 완료를 뜻하지 않는다. 입력과 outbox는 같은 트랜잭션이다. 동일 scenario·종류·외부 ID의 같은 본문은 동일 작업으로 반환하고, 다른 본문은 409다. 문서 revision과 임베딩 revision도 인덱싱 식별에 반영한다.

수신 예제는 [시나리오 이벤트](../../../data/scenarios/analysis-event.jsonl), [저장 문서](../../../data/scenarios/retrieval-document.json)를 따른다. 문서 원문·검색 질의·발표/수집 시각을 분리하고 `mode=simulation`을 강제한다. `search_query`만 외부 검색에 전송하며 전체 원문이나 사용자 프로필을 자동으로 전송하지 않는다.

```sh
BONGHWA_ENV_FILE=.env.analysis uv run --no-sync python -m bonghwajigi.ingestion.replay data/scenarios/analysis-event.jsonl --check
BONGHWA_ENV_FILE=.env.analysis uv run --no-sync python -m bonghwajigi.ingestion.replay data/scenarios/analysis-event.jsonl --submit --base-url http://127.0.0.1:18000
```

고정 예제의 `as_of`는 2026-10-31이며 현재 시각이 아니다. 같은 ID의 새 자료는 충돌하므로 새로운 event ID나 문서 revision을 사용한다. 파일 전송은 행 단위로 처리한다.

## 워커·검색·장애 처리

- outbox 전달기는 DB 행을 잠그고 미완료 작업을 analysis 큐로 전달한다. 브로커 실패 시 DB 작업을 남기고 다시 시도한다. Redis 전달 후 DB 반영 전에 종료돼도 재전달을 허용한다.
- 워커는 job 행 잠금과 완료 상태 검사로 중복 실행을 억제한다. 늦은 ACK·worker lost 재전달을 사용한다. 전체 작업 결과와 문서 벡터는 트랜잭션/SAVEPOINT로 묶어 임베딩 실패 때 부분 결과를 완료로 남기지 않는다.
- 일시적 임베딩 장애는 최대 3번 시도한다. 잘못된 인증·입력·벡터 차원·모델 revision 등 계약 오류는 실패로 기록한다. 실패 상태는 인증된 retry 경로로 재개한다.
- 인터넷 검색은 API 키가 필요 없는 Google News RSS 어댑터다. 제목·짧은 설명·링크·매체·발표 시각만 확보하고 기사 본문은 수집하지 않는다. RSS 형식/가용성 변경은 `unavailable`로 드러난다.
- 웹 검색 결과를 문서 임베딩으로 인덱싱하고 사건 검색어와 원문을 질의 임베딩으로 만든다. 1024차원·정규화·모델 ID·revision·유한한 숫자를 확인한다.
- pgvector의 정확 cosine 검색을 사용한다. scenario·산불 유형·모델 revision·발표 시각·유효기간으로 제한하고 같은 출처 URL의 중복을 줄인다. 과거 시나리오에 미래 자료를 넣지 않는다.
- 문서는 512문자 청크와 64문자 겹침을 사용한다. 이는 첫 연결을 위한 기본값이며 검색 품질 검증 결과가 아니다. 검색 점수는 cosine 유사도이며 산불 영향 확률이 아니다.
- 웹 장애 시 저장 자료로 진행하고 `WEB_SEARCH_UNAVAILABLE`, 근거가 없으면 `NO_RETRIEVED_EVIDENCE`를 남긴다. 자료가 없다는 이유로 안전을 판정하거나 지침을 만들어 넣지 않는다.
- 웹 자료의 `verified=false`, 출처와 검색 시각을 보존한다. 검색됐다는 이유로 승인된 정책이 되지 않으며 모든 근거에 `approved_policy=false`를 붙인다.
- 긴급 큐와 워커는 이 분석 경로의 모듈을 import하지 않는다. 실제 긴급 수신·전달은 이번 작업에서 구현하지 않았다.

## Qwen 전달 직전 결과

작업 상태는 `queued → processing → ready_for_qwen`이다. 문서 인덱싱은 `indexed`, 임베딩 장애는 `retry/failed`로 구분한다. `processing`은 트랜잭션 안의 상태라 조회에서 queued/retry로 보일 수 있다. 결과에는 다음이 들어간다.

- 원래 관측 입력과 origin, scenario/event 식별자, simulation 표시
- 추가 근거의 청크·문서·revision·원문 링크·매체·발표/수집 시각·확인 상태
- 임베딩 모델·revision·1024차원 및 cosine 검색 점수
- 인터넷 검색 질의·검색 시각·성공/실패·결과 수와 자료 부족 경고
- `qwen_invoked=false`, `evidence_is_untrusted_data=true`, `token_budget_checked=false`

`ready_for_qwen`은 자료 묶음 생성 완료이며 사건 통합 완료를 뜻하지 않는다. 다음 단계에서 근거 텍스트를 명령과 분리하고 Qwen tokenizer로 전체 토큰 예산을 검사해야 한다. 현재는 생성 모델을 호출하지 않는다.

## 실제 검증

[연결 검증 근거](analysis-retrieval-evidence.json)에 비밀정보나 기사 본문 없이 기록했다. 실제 PostgreSQL/pgvector·Redis/Celery·GPU 임베딩·인터넷 검색을 사용한 마지막 시연에서 인터넷 뉴스 5건을 확보했고, 검색 근거 5개를 저장해 `ready_for_qwen`으로 완료했다. 중복 이벤트는 같은 job ID였고 Qwen 호출은 없었다.

DB 회귀 검사는 별도 테스트 scenario ID만 정리하며 다른 자료는 삭제하지 않는다.

```sh
BONGHWA_TEST_DATABASE_URL=postgresql+psycopg://bonghwajigi:local-analysis-only@127.0.0.1:15432/bonghwajigi_analysis uv run --no-sync pytest
```

27개 검사에서 API 인증·멱등 충돌·시나리오 격리·outbox 실패/복구·중복 전달·유효기간·미래 자료·모델 버전·웹 장애 대체·벡터 계약·생성 미호출을 확인했다. CI도 PostgreSQL/pgvector와 migration 후 같은 검사를 실행하도록 구성했다. 원격 CI 실행·일반 서버 배포·프로세스 강제 종료/장시간 부하·실제 재난 자료 품질은 이번 검증 범위가 아니다.
