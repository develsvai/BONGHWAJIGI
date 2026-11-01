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
- Task count: `9`

## Task

- Title: 확정한 산불 3단계 정책과 공식 경보·알림 전달 경로 구현
- Description: 사용자가 확정한 준비·대피이동·긴급지원요청 정책을 기존 개인 계획 루프에 적용하고 공식 경보 우선 처리·발령 대상 확인·정정/해제 및 내구성 있는 알림 전송을 구현한다. 실제 예측 모델 연결은 제외하고 GPU 학습은 보존한다.
- Expected output: 정책·상태 계약, 검토된 국내 기본 지침, 정책 실행기, 긴급 수신/워커, 알림 큐·모의/FCM 어댑터, DB migration, 검증 및 response-policy.md
- Done condition: 세 사용자·경로/조력자/자료 부족·상향/하향에서 3단계가 재현되고 공식 원문 처리가 GPU와 독립적이며 알림 중복/재시도·수신 상태가 구분된다. 실제 푸시 자격이 없으면 미설정과 모의 전송을 실제 전송 성공으로 표시하지 않는다.
- In scope: 확정 정책 및 국내 지침; 사용자 상태·검토된 환경 입력; 공식 경보 독립 경로; 알림 저장·전달·장애 복구; 공용 갱신 이력; 문서와 검증
- Out of scope: 실제 예측 모델 학습/추론 연결; 진행 중인 training 작업 수정·중단; BONGHAWJIGI_APP; 3D; 실제 K8s 수집; 서버 음성; 실제 119 연락; 자격정보 커밋; 사용자 동의 없는 외부 연락
- Validation hint: 실제 PostgreSQL/Redis 검증, 정책 경계·인증·격리·재시도·만료 시험, API 명세/예제·Ruff·migration·Loom strict; 서버 배포 Task는 실제 사설망 요청과 재시작 검사
- Required docs: -
- Memory refs: -
- Document outputs: `docs/V2/delivery/response-policy.md`
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

No task-level required docs or memory refs recorded.

## Verified Team Policies

No verified Team Policy Snapshot is active.

## Active Workflow Memory

No active workflow memory recorded.
