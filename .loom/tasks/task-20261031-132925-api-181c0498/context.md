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

- Title: 앱 연동 API 계약과 인계
- Goal: 산불 MVP의 공식 경보·개인 대응·영향 또는 예측 불가·텍스트·변경 이벤트를 OpenAPI와 예제로 고정하고 실제 서버 호환을 검증해 앱팀에 인계한다. live/simulation과 미검증 푸시 구간을 구분하고 앱 구현은 제외한다. 이 갱신은 사용자 지시에 따른 계약 재고정이며 구현 실행·Queue 등록은 포함하지 않는다. 기존 완료 이력과 Task ID를 보존한다.
- Branch: HeoNey
- Task count: `4`

## Task

- Title: 사용자 인증과 프로필·위치·개인 안내·변경 조회의 앱용 서버 API 구현
- Description: 실제 예측 모델 연결을 제외한 나머지 구현을 진행하라는 직접 지시에 따라 서비스 토큰과 분리한 사용자 JWT 인증·소유권 검사·프로필/상태/위치·기기 등록·경보/현재 정책/변경 조회·수신 확인 API를 기존 문서와 맞춰 구현한다. 앱 저장소는 변경하지 않는다.
- Expected output: 실행 가능한 앱용 FastAPI 경로와 JWT 설정·개발 계정 도구, 갱신/기기/수신 기록, 계약·인계 문서와 접근 제어 시험
- Done condition: 일반 앱 API가 자기 사용자 데이터만 읽고 수정하며 서비스 토큰을 앱에 요구하지 않고 cursor/revision/만료/중복과 오류 상태를 검증한다. 실제 예측은 unavailable이며 미구현 경로를 성공으로 가장하지 않는다.
- In scope: 사용자 JWT·소유권; 프로필·현재 상태·위치; 기기 토큰·경보·개인 안내·변경/영수증 조회; 문서·계약 검증
- Out of scope: 실제 예측 모델 학습/추론 연결; 진행 중인 training 작업 수정·중단; BONGHAWJIGI_APP; 3D; 실제 K8s 수집; 서버 음성; 실제 119 연락; 자격정보 커밋; 사용자 동의 없는 외부 연락
- Validation hint: 실제 PostgreSQL/Redis 검증, 정책 경계·인증·격리·재시도·만료 시험, API 명세/예제·Ruff·migration·Loom strict; 서버 배포 Task는 실제 사설망 요청과 재시작 검사
- Required docs: -
- Memory refs: -
- Document outputs: `docs/V2/delivery/mvp-app-api.md`
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
## 2026-10-31T01:30:16+00:00

검증 전부 실행 지시를 확인했다. 계약 형식 검증은 통과했지만 실제 검증에 필요한 선행 작업 E1, D5, D6의 산출물이 아직 없어 기능 검증은 실행할 수 없다. 모델 또는 API가 완성된 것으로 간주하지 않고 PENDING 유지하며 선행 구현 완료 후 이 Task를 실행한다. 현황은 A2 환경 검증 보고서에 함께 정리한다.

- Task: `task-20261031-002631-api-0f38b4c1`
- Tags: `validation`, `prerequisites`
## 2026-10-31T03:52:04+00:00

사용자가 Job 2는 앱 연동 API 계약과 인계라고 명확히 확인했다. 이번 직접 실행은 최신 5개 화면과 V2 기준의 API 초안 및 앱팀 문서 작성이다. B2 D1 미완료 때문에 기존 E1 최종 계약과 E2 실제 서버 호환 검증을 완료로 바꾸지 않고 선행 초안 Task로 수행한다. 음성 3D 자동 신고의 구현 채택은 문서 작성과 구분한다.

- Task: `task-20261031-035154-v2-5-api-39004d37`
- Tags: `user-direction`, `api`, `scope`
## 2026-10-31T04:11:49+00:00

사용자 지정 Job 2 재검토 결과와 앱팀 전달 패키지 작성: docs/V2/delivery/api-job-review.md, app-api-contract.md, api-reference.md, api-handoff.md. 25 API와 5개 화면 연결, 48 HTTP 모의 예제 및 OpenAPI 정적 검사 완료. 기존 E1은 B2 D1과 인증 결정을 반영한 승인본 고정으로, E2는 실제 서버 단말 검증으로 남긴다. 이번 초안은 배포 완료가 아니며 음성 3D는 조건부, 119는 미전송 문자 초안이다.

- Task: `task-20261031-035154-v2-5-api-39004d37`
- Tags: `api`, `handoff`, `verified`, `draft`
## 2026-10-31T08:01:46+00:00

# 2026-10-31-wildfire-mvp 작업 계약 재고정

사용자 지시: “오케 우선은 그거대로 loom에 타스크를 재고정 해”.

2026-10-31 KST 사용자 재고정: 오늘 MVP는 산불 한 종류이며 3D와 서버 STT/TTS·오디오 스트리밍을 제외하고 서버는 텍스트를 제공한다. 공식 경보는 출처·원문·발령 대상을 확인해 개인별 정책 계산과 GPU를 기다리지 않고 우선 전달한다. 일반 분석은 정형 파싱 또는 필요한 Qwen 문서 추출·저장 문서의 임베딩 검색, 사건 통합·위치 관련성·입력 검사, 영향 확률 또는 예측 불가, 검토된 개인별 정책 순서다. 공식 등급·환경 영향 확률·개인 대응 단계를 분리하고 정책은 검토·버전 관리하며 입력 변경 때 재적용한다. 실제 자료·과거 재생·합성 시나리오를 구분하고 실제 정답이 없으면 학습·추론 연결은 simulation으로 검증하며 실제 예측은 unavailable로 둔다. 이 지시는 작업 계약 재고정만 승인하며 구현 실행·Queue 등록·서버 설치·원격 push를 지금 승인한 것으로 취급하지 않는다. 오늘 범위는 이 계약과 Job 재고정 노트를 우선하고 기존 V2 문서는 배경 설계로 참조한다.

이 갱신은 재고정만 수행하며 Task 실행 또는 Queue 등록을 시작하지 않는다.

미정: 시연 지역·사례, 모델의 실제 정답 출처·격자·예측 기간, 개인 대응 단계 매핑, 2D 실제 경로 계산 채택 여부. 60분은 예시이며 실제 확정값이 아니다. 실제 정답 부족은 C4에서 실제 예측 보류로 판정한다.

착수 순서: A1 → B1 → B2 및 C1 → A3·D1·D6 → 수집/긴급 전달·개인 정책·모델 준비 → 안내 갱신 → E2·A4 통합 검증. 공식 원문 전달 D4는 개인 정책 D1/D2와 모델 준비를 선행 조건으로 삼지 않는다.

- E1 `task-20261031-002631-openapi-d96e2bb5`: 산불 MVP 텍스트 API와 공식 경보·개인 대응·실제 및 모의 계약 고정. 선행: B2, C1, D1, D6. 현재 PENDING.
- E2 `task-20261031-002631-api-0f38b4c1`: 산불 MVP 실제 서버의 텍스트·경보·갱신 API와 모의 모드 계약 검증. 선행: D5, D6, E1. 현재 PENDING.

구체적 완료 조건은 각 Task의 재고정 계약을 따른다. 기존 docs/V2/04-execution-backlog.md는 이전 계획이며 실제 계약 정본은 현재 Task와 이 노트다.
- Tags: `mvp`, `산불`, `2026-10-31`, `계약재고정`
## 2026-10-31T08:33:38+00:00

2026-10-31 구현 기술 스택 결정: docs/V2/delivery/implementation-stack.md; Task task-20261031-082929-mvp-3188b68a. Python 3.12 + FastAPI/Pydantic 2 + SQLAlchemy 2.x/psycopg 3/Alembic + PostgreSQL 16/PostGIS/pgvector + Celery/Redis + Transformers/Sentence Transformers + XGBoost. 일반 서버 API/정책/CPU 추론, GPU 서버 모델/별도 학습, K8s 수집으로 배치한다. 기존 OpenAPI를 FastAPI/Pydantic 계약으로 대조한다. 전경 getUpdates long polling, PushGateway/FCM HTTP v1 첫 어댑터를 기준으로 앱의 실제 fcm/apns 토큰과 인증·HTTPS를 E1에서 합의한다. 모의 전송과 실제 단말 전달을 구분한다. 이번 실행은 스택 문서와 계약 연결만 수행하며 다른 구현 Task·Queue·서버 설치는 시작하지 않는다.
- Tags: `기술스택`, `산불`, `MVP`

## Context References

No explicit context references recorded for this job.

## Required Documents and Memory

No task-level required docs or memory refs recorded.

## Verified Team Policies

No verified Team Policy Snapshot is active.

## Active Workflow Memory

No active workflow memory recorded.
