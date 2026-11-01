# Context

## Loom 코드 계약

아래 항목은 Loom 코드에 고정된 runtime 동작 계약입니다. 관련 흐름을 바꾸기 전 `loom contract show <id>`로 확인합니다.

- `task-execution`: Task 실행 전 prompt/context/previous-results에 들어가는 입력 경계입니다. 명령: `loom contract show task-execution`. Source: `loom/application/context_pack.py`, `loom/application/team_policy.py`
- `done-guardrail`: Task를 DONE으로 인정하기 전에 필요한 산출물과 상태 전이를 검증하는 계약입니다. 명령: `loom contract show done-guardrail`. Source: `loom/application/services.py`

## Project Memory

# 프로젝트 분석: BONGHWAJIGI

## 루트

`/Users/hongyongjae/Desktop/helloworld/BONGHWAJIGI`

## 요약

- 주요 스택: 확인 필요
- 패키지 / 런타임 파일: -
- 테스트 진입점: -
- 앱 진입점: docs/

## 최상위 구조

- ./
  - .gitignore
  - AGENTS.md
  - CLAUDE.md
  - README.md
-   docs/
    - README.md
    - ai-and-infrastructure.md
    - architecture-and-data-flow.md
    - decisions-and-meeting-review.md
    - product-and-scenarios.md
    - ui-ux-handoff.md

## 레포 규칙

- 기존 프로젝트 스타일과 로컬 helper API를 우선합니다.
- 수정 전에 관련 파일을 먼저 확인합니다.
- 변경 범위는 현재 Loom Task 계약 안에 유지합니다.
- 사용자 변경분을 버리는 destructive git reset/checkout을 사용하지 않습니다.
- 넓은 리팩터링이나 cross-domain 변경이 필요하면 먼저 boundary warning을 기록합니다.

## 실행 힌트

- 설치 / 런타임: -
- 테스트 / 검증: -
- 개발 서버: -

## 위험 영역

- 주의가 필요한 경로:
  - `No obvious sensitive path detected`

## Loom Task 가이드

- 좋은 Task는 예상 산출물, 완료 조건, 작업 범위, 검증 힌트를 가져야 합니다.
- repo 맥락이 약하면 architecture docs를 보강한 뒤 `loom analyze-repo`를 다시 실행합니다.
- agent 실행 전 `loom task validate <task-id>`로 경계를 확인합니다.
- 중단 이후에는 `loom resume`으로 현재 workflow 상태를 복구합니다.

## 보완할 맥락

- 아키텍처 ownership boundary는 수동 note가 필요할 수 있습니다.
- 배포, credential, 외부 서비스 정책은 자동으로 추론하지 않습니다.
- 프로젝트별 규칙은 Job note 또는 context reference에 추가합니다.

## Workspace Policy

- Output language: `ko`
- Agent provider: `claude`
- Agent model: `adapter-default`
- Reasoning effort: `high`
- Required branch: `develop`
- Dirty branch switch: `blocked`
- Commit policy: `manual`
- Include `.loom` metadata in Git: `yes`
- Read-only parallel execution: `allowed`
- Validation environment: `auto`
- Previous Task result limit: `2`
- Workspace required docs: -
- Loom fixed guardrails and verified Team required policies take precedence over this Workspace Policy.

## Job

- Title: 개인별 대응 정책과 알림 서버
- Goal: 검토·버전 관리한 산불 정책과 사용자 상태로 개인 대응·텍스트 안내를 구현한다. 공식 원문은 정책 계산·GPU와 독립적으로 먼저 전달하며 Qwen3·Embedding은 추출·검색·선택된 행동 설명에 사용한다. 3D·서버 음성은 오늘 제외한다. 이 갱신은 사용자 지시에 따른 계약 재고정이며 구현 실행·Queue 등록은 포함하지 않는다. 기존 완료 이력과 Task ID를 보존한다.
- Branch: HeoNey
- Task count: `8`

## Task

- Title: 새 관측·사용자 변경과 주기 점검을 개인별 대응 계획 갱신 루프로 연결
- Description: 사용자가 승인한 최신 정보 기반 개인별 대응 계획의 반복 갱신을 지금 직접 구현한다. 기존 수신·분석·Qwen 통합과 연결하고 사용자 프로필·위치·예측·공식 기록·지침 버전을 반영한 계획과 변경 이력을 조회한다. 대응 레벨·확률 기준·알림 방식은 미정으로 유지한다.
- Expected output: 시나리오별 사용자·위치·사건·경보·예측·지침 입력과 DB migration, 내구성 있는 재평가·주기 점검·Qwen 연계 실행기, 개인별 계획·변경 이력 API, 반복 시연과 결과 문서
- Done condition: 실제 DB·큐와 기존 분석에서 사용자별 계획까지 자동 처리된다. 입력 갱신·중복·역순·위치/자료 만료·정책 변경·Qwen 장애 및 재시도에서 재평가와 변경 이력이 검증된다. 미정 레벨·운영 미승인·모의 예측과 미발송을 보존하고 검증·Loom 기록을 커밋한다.
- In scope: simulation 전용 내부 API와 DB 상태·내구성 있는 갱신 작업, 조건형 시연 지침, 사건별 사용자 관련성, 기존 분석에서 Qwen 통합과 정책 연결, 주기 점검·만료 처리, 조회·이력·실행 문서 및 실제 연결 시연
- Out of scope: 회의 미정 레벨/확률 임계값/푸시 규칙 확정, 실제 정책 승인 위조, XGBoost 학습/재학습 및 국내 운영 성능 주장, 긴급 연락/푸시 발송, 앱 저장소, 실제 K8s 수집, 다른 채팅의 학습 파일 변경, 공개 배포
- Validation hint: 실제 PostgreSQL migration·Redis 분석 큐·Qwen 연결에서 세 사용자 개인화와 두 번 이상 입력 갱신, 중복/역순 거부·시나리오 격리·미래/만료 위치·확률 unavailable·공식 경보 보존·Qwen 실패 템플릿 대체·변경 없는 평가의 이력 억제·주기 복구·기존 검사와 Loom strict
- Required docs: `docs/V2/delivery/analysis-retrieval-flow.md`, `docs/V2/delivery/qwen-integration-result.md`
- Memory refs: -
- Document outputs: `docs/V2/delivery/personal-policy-loop.md`
- Document output exceptions: -
- Source proposal: `-`
- Status: PENDING
- Assigned agent: foreground

## Advisor Source Prompt

No Advisor source prompt recorded for this Task.

## Inclusion Policy

- Mandatory execution files: `prompt.md`, `context.md`, and `previous-results.md`.
- Always included: project memory, current Job/Task metadata, and Job notes.
- Previous results: up to the latest 2 recorded results from earlier Tasks in this Job.
- Job context refs: explicit Job-scoped references selected by the controlling agent or user.
- Task required docs: mandatory Task-scoped documents; missing refs block validation and execution.
- Task memory refs: mandatory Task-scoped workflow memory references; missing or non-memory refs block validation and execution.
- Repository documents, validation documents, and skill rules: included only through explicit Job context refs, Task required docs, or Task memory refs.
- Verified Team Policy Snapshot: included before Active Memory; required policy cannot be overridden by lower-priority context.
- Active workflow memory with an `always` category is included automatically while its status is `ACTIVE`.
- `task_selected` and `reference_only` memory is included only through explicit Task memory refs.
- Consumed proposals, rejected proposals, resolved memory, superseded memory, and archived memory are excluded.
- Unreferenced repository files and results from other Jobs are not included.
- `AGENTS.md` and `CLAUDE.md` remain session-level controlling-agent entrypoints and are not treated as task context artifacts by default.

## Job Notes

# Notes

## 2026-10-31T00:26:26+00:00

설계 기준은 docs/V2이며 HeoNey는 참고다. 앱 구현은 제외하고 앱팀에 API 명세를 제공한다. 이 등록은 작업 계약 고정이며 후속 구현 Task를 지금 실행하거나 Queue에 넣지 않는다. 기준 원문은 docs/V2/01, 02, 03 문서이고 실행 작업표는 docs/V2/04-execution-backlog.md이다. 등록 시 의존관계는 Job 경계를 넘어 적용한다.
- Tags: `v2`, `scope`, `backlog`
## 2026-10-31T00:50:01+00:00

GPU 상태 조회에서 NVIDIA L4 1대와 CUDA driver API 초기화 성공을 확인했다. 현재 기본 Python 3.12.3 환경에는 torch transformers vllm xgboost sentence-transformers numpy pandas 배포 메타데이터가 없고 Docker 실행 파일 및 nvcc도 PATH에서 확인되지 않았다. D3에서 전용 모델 환경과 실제 메모리 지연 동시성을 측정해야 한다. GPU 유휴 상태만으로 모델 처리량을 보장하지 않는다.

- Task: `task-20261031-002629-qwen-617b8d58`
- Tags: `infrastructure`, `model-runtime`
## 2026-10-31T01:30:16+00:00

검증 전부 실행 지시를 확인했다. 계약 형식 검증은 통과했지만 실제 검증에 필요한 선행 작업 B2, D1, A2의 산출물이 아직 없어 기능 검증은 실행할 수 없다. 모델 또는 API가 완성된 것으로 간주하지 않고 PENDING 유지하며 선행 구현 완료 후 이 Task를 실행한다. 현황은 A2 환경 검증 보고서에 함께 정리한다.

- Task: `task-20261031-002629-qwen-617b8d58`
- Tags: `validation`, `prerequisites`
## 2026-10-31T08:01:46+00:00

# 2026-10-31-wildfire-mvp 작업 계약 재고정

사용자 지시: “오케 우선은 그거대로 loom에 타스크를 재고정 해”.

2026-10-31 KST 사용자 재고정: 오늘 MVP는 산불 한 종류이며 3D와 서버 STT/TTS·오디오 스트리밍을 제외하고 서버는 텍스트를 제공한다. 공식 경보는 출처·원문·발령 대상을 확인해 개인별 정책 계산과 GPU를 기다리지 않고 우선 전달한다. 일반 분석은 정형 파싱 또는 필요한 Qwen 문서 추출·저장 문서의 임베딩 검색, 사건 통합·위치 관련성·입력 검사, 영향 확률 또는 예측 불가, 검토된 개인별 정책 순서다. 공식 등급·환경 영향 확률·개인 대응 단계를 분리하고 정책은 검토·버전 관리하며 입력 변경 때 재적용한다. 실제 자료·과거 재생·합성 시나리오를 구분하고 실제 정답이 없으면 학습·추론 연결은 simulation으로 검증하며 실제 예측은 unavailable로 둔다. 이 지시는 작업 계약 재고정만 승인하며 구현 실행·Queue 등록·서버 설치·원격 push를 지금 승인한 것으로 취급하지 않는다. 오늘 범위는 이 계약과 Job 재고정 노트를 우선하고 기존 V2 문서는 배경 설계로 참조한다.

이 갱신은 재고정만 수행하며 Task 실행 또는 Queue 등록을 시작하지 않는다.

미정: 시연 지역·사례, 모델의 실제 정답 출처·격자·예측 기간, 개인 대응 단계 매핑, 2D 실제 경로 계산 채택 여부. 60분은 예시이며 실제 확정값이 아니다. 실제 정답 부족은 C4에서 실제 예측 보류로 판정한다.

착수 순서: A1 → B1 → B2 및 C1 → A3·D1·D6 → 수집/긴급 전달·개인 정책·모델 준비 → 안내 갱신 → E2·A4 통합 검증. 공식 원문 전달 D4는 개인 정책 D1/D2와 모델 준비를 선행 조건으로 삼지 않는다.

- D1 `task-20261031-002627-task-a70543d3`: 산불 공식 지침과 개인별 대응 단계·행동·승급 및 해제 정책표 고정. 선행: A1, B1, B2. 현재 PENDING.
- D2 `task-20261031-002629-task-80e56e11`: 사용자 프로필·현재 상태 저장과 버전 기반 산불 대응 정책 엔진 구현. 선행: A3, B2, D1. 현재 PENDING.
- D3 `task-20261031-002629-qwen-617b8d58`: GPU의 Qwen3·Embedding 모델 준비와 산불 문서 추출·검색·텍스트 설명 검증. 선행: A2, A3, B2, D1. 현재 PENDING.
- D4 `task-20261031-002630-task-91ec9d3f`: 개인별 정책·GPU와 독립된 산불 공식 원문 우선 알림 구현. 선행: A3, B3. 현재 PENDING.
- D5 `task-20261031-002630-task-bc07e7d7`: 산불 사건·위치·사용자 상태·정책 버전 변경에 따른 안내와 화면 갱신 연결. 선행: B5, C5, D2, D3, D4. 현재 PENDING.
- D6 `task-20261031-002630-3d-tts-8f1e43b5`: 오늘 산불 MVP의 3D·서버 음성 제외와 2D·경로 경계 문서화. 선행: A1, A2, B1. 현재 PENDING.
- D7 `task-20261031-002630-tts-bb28f882`: 후속 보류: 별도 채택한 경로·서버 음성 기능 구현. 선행: B5, D2, D6. 오늘 범위 밖 후속 보류.

구체적 완료 조건은 각 Task의 재고정 계약을 따른다. 기존 docs/V2/04-execution-backlog.md는 이전 계획이며 실제 계약 정본은 현재 Task와 이 노트다.
- Tags: `mvp`, `산불`, `2026-10-31`, `계약재고정`
## 2026-10-31T08:33:37+00:00

2026-10-31 구현 기술 스택 결정: docs/V2/delivery/implementation-stack.md; Task task-20261031-082929-mvp-3188b68a. Python 3.12 + FastAPI/Pydantic 2 + SQLAlchemy 2.x/psycopg 3/Alembic + PostgreSQL 16/PostGIS/pgvector + Celery/Redis + Transformers/Sentence Transformers + XGBoost. 일반 서버 API/정책/CPU 추론, GPU 서버 모델/별도 학습, K8s 수집으로 배치한다. 사용자는 대응 레벨과 레벨별 알림 방식을 회의 중이며 정해지는 대로 제공한다고 밝혔다. D1은 PENDING이고 임계값·단계·알림 정책을 임의 확정하지 않는다. 모델 로딩 준비와 최종 정책 설명 검증을 구분한다. Qwen은 선택된 행동 설명, 정책 선택은 검토된 Python 규칙으로 한다. 이번 실행은 스택 문서와 계약 연결만 수행하며 다른 구현 Task·Queue·서버 설치는 시작하지 않는다.
- Tags: `기술스택`, `산불`, `MVP`

## Context References

No explicit context references recorded for this job.

## Required Documents and Memory

### required-doc: docs/V2/delivery/analysis-retrieval-flow.md

- Path: `docs/V2/delivery/analysis-retrieval-flow.md`
- Status: present

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

### required-doc: docs/V2/delivery/qwen-integration-result.md

- Path: `docs/V2/delivery/qwen-integration-result.md`
- Status: present

# 경보 포함 Qwen3 통합 결과 — 추론 입력 직전

실행: **2026-10-31 19:40 KST**. 과거 영덕 산불 자료를 실제 분석 큐·임베딩·Qwen3로 처리했다. 공식 경보 발령 기록 1건과 근거 자료 5개를 묶었고, 모델이 선택한 근거 문장 3개의 출처 일치를 확인했다. 마지막 상태는 `pre_inference_review`다. XGBoost 추론·개인 대응 단계 결정·알림 발송은 실행하지 않았다.

이전에 제공한 `analysis-demo.json`은 합성 입력과 넓은 인터넷 검색 결과였고 공식 경보를 포함하지 않았다. 이번에는 공식 발령 기록과 지역·과거 시점을 지정한 별도 시나리오를 사용했다.

## Qwen3가 실제 작성한 통합 요약

> 당시 경상북도 영덕군 전 지역에 산불 확산이 보도됐으며, 산에서 떨어진 곳으로 대피가 안내됐다. 정부는 전국 산불경보를 심각 단계로 확대하고 국가소방동원령을 발동했다.

위 문장은 모델의 실제 출력이다. **2025년 과거 사건에 관한 내부 검토용 요약**이며 현재 사용자에게 보내는 대피 안내가 아니다. `summary_review_status=not_reviewed`, `approved_policy=false`로 저장했다. JSON 형식과 근거 인용의 일치는 자동 검사했지만 요약 전체의 의미·사실성을 자동 승인한 것은 아니다.

[생성 응답 원본](qwen-integration/generation-response.json)에서 모델이 돌려준 문자열·모델 revision·토큰 수·처리 시간을 확인할 수 있다. [모델에 보낸 자료와 지시](qwen-integration/generation-request.json)도 함께 보관했다.

## 이번에 포함한 재난 경보

| 항목 | 값 |
| --- | --- |
| 자료 종류 | 공식 게시물에 남은 과거 산불 위기경보 발령 기록 |
| 발령 기관 | 산림청 |
| 발령 시각 | 2025-03-25 16:00 KST |
| 대상 지역 | 전국 |
| 공식 등급 | 심각 |
| 원자료 | 2025-03-26 대한민국 정책브리핑의 발령·확대 사실 기록 |
| 직접 수신한 재난문자 원본 | 없음 (`original_sms_available=false`) |
| 현재 발효 여부 | 확인하지 않음 (`current_effective_status=not_checked`) |
| 개인별 대응 레벨 | 미결정·생성하지 않음 |

전국 경보 확대와 산림청 발령 사실은 [대한민국 정책브리핑 원자료](https://www.korea.kr/news/policyNewsView.do?newsId=148940993)에 근거한다. 발령 시각과 게시일을 별도 필드로 보존했다. 게시일만 공개되어 있어 `published_at`은 2025-03-26의 마지막 초를 상한으로 사용하고, 날짜 단위라는 표시도 남겼다.

발령 필드는 원자료를 확인해 작성한 시나리오 입력이다. Qwen이 경보 발령 여부를 판단한 결과는 아니다. 경보 기록은 검색 순위와 관계없이 통합 자료에 포함하며 모델이 등급·발령 시각·대상을 변경하도록 허용하지 않는다. 원문 짧은 발췌는 JSON의 `official_alerts[].original_excerpt`에 있다. 이 분석 시연에서는 경보를 발송하지 않는다. 실제 긴급 경보 수신·우선 전달 API는 아직 구현하지 않았고, 이 생성 과정을 기다리도록 연결하지 않았다.

## 무엇을 합쳤는가

재생 기준 시각은 **2025-03-27 00:00 KST**, 사건 지역 표시는 **경상북도 영덕군**이다. 지역명은 시나리오 작성자가 지정했으며 좌표 변환이나 사용자의 현 위치 확인은 수행하지 않았다.

인터넷 질의는 `산불 영덕 대피 after:2025-03-20 before:2025-03-28`이었다. RSS 결과 5건 중 발표 시각 조건을 적용하고 저장 문서까지 함께 임베딩 검색했다. 최종 통합 입력은 아래 5개다.

| 자료 | 성격 | 통합에 넣은 방식 |
| --- | --- | --- |
| 산불경보 심각 확대·경북 산불 상황 | 정책브리핑 공식 자료의 짧은 발췌와 작성자 요약 | 필수 근거로 고정 |
| 산불 발생 시 행동 요령 | 행정안전부 안전한TV 자료의 작성자 요약 | 필수 참고 자료로 고정, 정책 미승인 |
| 의성산불 확산에 영양·영덕군 주민 대피 재난문자 | 중앙일보, 인터넷 검색의 제목·짧은 설명 | 임베딩 검색 |
| 영덕군 전 지역 산불 확산·대피 안내 보도 | 연합뉴스TV, 인터넷 검색의 제목·짧은 설명 | 임베딩 검색 |
| 영덕군 전 지역 산불 확산·대피 안내 보도 | 연합뉴스, 인터넷 검색의 제목·짧은 설명 | 임베딩 검색 |

기본 행동요령의 원출처는 [행정안전부 안전한TV](https://www.safetv.go.kr/base/video/view?idx=2759&menuLevel=&menuNo=&playlistManagementIdx=8)다. 이번에는 참고 문서로 포함했으며 개인 정책 DB에 승인된 지침으로 등록하지 않았다. 나머지 뉴스 URL·발표/수집 시각·검색 점수는 [검색 결과 원본](qwen-integration/retrieval-handoff.json)에 있다. 서로 다른 URL의 유사 보도가 남아 있어 3개 뉴스가 독립적인 3개 확인을 뜻하지는 않는다.

Qwen3는 공식 자료의 경북 확산·대피·기반시설 장애 요약, 중앙일보의 주민 대피 재난문자 제목, 연합뉴스TV의 영덕군 대피 안내 제목을 근거로 선택했다. 각 `evidence_id`가 실제 입력 자료에 있고 `quote`가 해당 텍스트에 그대로 존재하는지 검사했다. 여기서 인용 대상은 보관한 요약·RSS 텍스트이며 뉴스 기사 본문 전체가 아니다.

## 추론 모델 앞에 남긴 자료

완전한 결과는 [추론 전 통합 JSON](qwen-integration/pre-inference.json)이다. 핵심 필드만 줄이면 다음과 같다.

```json
{
  "mode": "simulation",
  "origin": "historical_replay",
  "stage": "pre_inference_review",
  "incident": {
    "disaster_type": "wildfire",
    "area_name": "경상북도 영덕군",
    "coordinates": null,
    "grid_id": null
  },
  "user_context": {"profile": null, "location": null, "policy": null},
  "inference_gate": {
    "status": "blocked",
    "input_matrix_created": false,
    "xgboost_invoked": false,
    "probability": null,
    "personal_response_level": null
  }
}
```

사건 개요와 공식 경보는 통합했지만 **수치 추론에 투입할 행렬은 만들지 않았다.** 현재 저장소의 [학습 입력 계약](../../../training/reports/dataset-report.json)은 미국 NDWS 자료의 다음 일별 위성 화재 관측(`fire_next_day`)을 위한 20개 피처다. 개인의 산불 피해 확률을 바로 예측하는 계약이 아니며 국내 적용도 검증되지 않았다.

| 필요한 입력 | 이번 확보 상태 |
| --- | --- |
| 고도 `elevation`, 가뭄 `pdsi`, 식생 `NDVI` | 해당 격자의 관측값 없음 |
| 강수 `pr`, 비습 `sph`, 풍향 `th`, 최저/최고기온 `tmmn`/`tmmx`, 풍속 `vs` | 시간·격자·단위가 정렬된 자료 없음 |
| 연료 관련 `erc`, 인구 `population` | 학습과 같은 전처리·해상도의 입력 없음 |
| 이전 화재 관측 `PrevFireMask` | 위성 관측 격자 없음 |
| 주변 화재/관측 수, 거리, 풍향 sin/cos, 품질 지표 등 파생 피처 8개 | 원래 래스터가 없어 계산하지 않음 |
| 사용자 상태·현 위치·검토된 개인 정책 | 이번 시나리오에 없음 |

20개 값은 모두 `null`로 보존했다. 뉴스의 지역명이나 단편적인 수치를 격자 관측값으로 바꾸거나 임의 값으로 채우지 않는다. 차단 사유는 `MISSING_STRUCTURED_RASTER_INPUTS`, `MISSING_GRID_AND_GEOGRAPHIC_ALIGNMENT`, `MODEL_DOMAIN_NOT_VALIDATED_FOR_KOREA`다.

## 실제 실행과 검증

흐름: **공식 자료 확인 → 로컬 수신 API → PostgreSQL/outbox → Redis/Celery → L4 임베딩·인터넷 검색 → Qwen3 생성 → 근거 검사 → 추론 전 JSON 저장**.

| 항목 | 실제 결과 |
| --- | --- |
| 최종 실행 시각 | 2026-10-31 19:40:47 KST |
| 공식 사이트 확인 | 정책브리핑·안전한TV 모두 HTTP 200, 본문 표식 확인 및 HTML SHA256 기록 |
| 모델 | `Qwen/Qwen3-4B-Instruct-2507` |
| 고정 revision | `cdbee75f17c01a7cc42f958dc650907174af0554` |
| 생성 입력 / 출력 | 1,021 / 334토큰 |
| 모델 처리 시간 | 13,404.69ms (전체 파이프라인 시간과 다름) |
| 입력 예산 | 실제 서버 tokenizer 검사, 입력 + 출력 예약 512 ≤ 4,096 |
| 근거 인용 검사 | 3개 모두 출처 ID·원문 텍스트 일치 |
| 추론·정책·알림 | 실행하지 않음 |

첫 생성에서는 과거 뉴스의 대피 표현이 요약에서 권고형으로 남았다. 지시에 과거 보고체와 권고형 금지를 추가해 다시 실행했고 위 문서에는 두 번째 실제 결과를 보존했다. 모델 원문을 사람이 대신 고쳐서 모델 출력으로 표시하지 않았다.

게시일이 기준 시각 이후인 자료, 다른 시나리오, 근거 없는 경보 원문, 없는 출처·인용, 모델의 임의 수치 필드, 잘린 JSON·출력 토큰 한도 도달·다른 모델 revision을 거부하는 검사를 추가했다. **실제 DB를 사용한 기존 검사와 신규 검사를 합쳐 42개 통과**했고 Ruff 검사·포맷과 기존 앱 API 계약 검사도 통과했다. 최종 검증 기록은 Loom Task `task-20261031-103324-qwen3-b1f9a853`에 남긴다.

현재 수집한 과거 자료의 **발표 시각 기준 필터**를 적용했다. 현재의 검색 인덱스·수정된 게시물에서 확보했으므로 2025년 당시 실제로 수집할 수 있었는지까지 입증하는 백테스트는 아니다. 기본 지침과 뉴스의 적합성·최신성·정책 승인은 별도다.

## 직접 다시 실행하기

[분석 환경 안내](analysis-retrieval-flow.md)에 따라 `.env.analysis`, 로컬 DB/Redis, 기존 GPU SSH 터널과 `serve_analysis.py`를 준비한다. 기존 분석 API의 토큰과 GPU 토큰은 서로 별도다. 토큰을 명령행에 적지 않는다.

```sh
BONGHWA_ENV_FILE=.env.analysis uv run --no-sync python tools/run_integration_demo.py
```

기본 출력은 새 `data/artifacts/yeongdeok-.../` 디렉터리다. `--output-dir`로 경로를 정할 수 있고 기존 디렉터리를 덮어쓰지 않는다. 도구는 수신 API와 기존 분석 워커를 이용하고 그 다음 Qwen3를 한 번 호출한다. 분석 워커가 자동으로 생성 단계를 실행하는 배포 구성은 이번에 추가하지 않았다.

보관 파일: [시나리오 입력](qwen-integration/scenario-input.json), [공식 자료 확인](qwen-integration/source-checks.json), [검색 결과](qwen-integration/retrieval-handoff.json), [생성 요청](qwen-integration/generation-request.json), [생성 원본](qwen-integration/generation-response.json), [추론 전 JSON](qwen-integration/pre-inference.json), [실행 메타데이터](qwen-integration/run-metadata.json).

## Verified Team Policies

No verified Team Policy Snapshot is active.

## Active Workflow Memory

No active workflow memory recorded.
