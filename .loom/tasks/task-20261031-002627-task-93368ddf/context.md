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

- Title: 기관 데이터와 위치 관련성 파이프라인
- Goal: 산불 공식 경보·관측·기상·근거 문서의 수집과 시연 자료를 확보하고 공통 형식·사건 이력·위치 관련성을 구현한다. 실제 자료·과거 재생·합성 자료 및 학습 정답 확보 가능성을 구분한다. 이 갱신은 사용자 지시에 따른 계약 재고정이며 구현 실행·Queue 등록은 포함하지 않는다. 기존 완료 이력과 Task ID를 보존한다.
- Branch: HeoNey
- Task count: `4`

## Task

- Title: 산불 사건·관측·위치·모델 입력과 실제 및 모의 데이터 공통 계약 고정
- Description: 2026-10-31 KST 사용자 재고정: 오늘 MVP는 산불 한 종류이며 3D와 서버 STT/TTS·오디오 스트리밍을 제외하고 서버는 텍스트를 제공한다. 공식 경보는 출처·원문·발령 대상을 확인해 개인별 정책 계산과 GPU를 기다리지 않고 우선 전달한다. 일반 분석은 정형 파싱 또는 필요한 Qwen 문서 추출·저장 문서의 임베딩 검색, 사건 통합·위치 관련성·입력 검사, 영향 확률 또는 예측 불가, 검토된 개인별 정책 순서다. 공식 등급·환경 영향 확률·개인 대응 단계를 분리하고 정책은 검토·버전 관리하며 입력 변경 때 재적용한다. 실제 자료·과거 재생·합성 시나리오를 구분하고 실제 정답이 없으면 학습·추론 연결은 simulation으로 검증하며 실제 예측은 unavailable로 둔다. 이 지시는 작업 계약 재고정만 승인하며 구현 실행·Queue 등록·서버 설치·원격 push를 지금 승인한 것으로 취급하지 않는다. 오늘 범위는 이 계약과 Job 재고정 노트를 우선하고 기존 V2 문서는 배경 설계로 참조한다. 

개별 작업: 발생·관측·발표·수집·유효 시각, 기관 ID·원문·사건 ID·수정 버전·GeoJSON 좌표와 결측을 정의한다. 공식 경보, 환경 영향 평가, 사용자 프로필/현재 상태, 개인 대응 결과와 정책 버전을 분리한다. live/simulation 및 실제 관측/과거 재생/합성 provenance를 구분하고 C1에서 확정할 목표·기간·격자에 연결할 입력 인터페이스를 제공한다. 개인정보 최소 수집·보관·삭제와 인증 경계를 기존 API 초안과 대조한다.
- Expected output: docs/V2/delivery/data-contract.md; 산불 공통 스키마·정상 및 누락 예제, provenance/시각/수정 규칙, 저장·삭제 및 API 초안 대응표
- Done condition: 실제 표본과 시연 입력을 같은 구조로 변환하고 실제·모의, 공식 등급·영향 확률·개인 대응이 혼합되지 않는 계약이 고정된다.
- In scope: 발생·관측·발표·수집·유효 시각, 기관 ID·원문·사건 ID·수정 버전·GeoJSON 좌표와 결측을 정의한다. 공식 경보, 환경 영향 평가, 사용자 프로필/현재 상태, 개인 대응 결과와 정책 버전을 분리한다. live/simulation 및 실제 관측/과거 재생/합성 provenance를 구분하고 C1에서 확정할 목표·기간·격자에 연결할 입력 인터페이스를 제공한다. 개인정보 최소 수집·보관·삭제와 인증 경계를 기존 API 초안과 대조한다.
- Out of scope: 다른 재난 유형; 모바일 앱 저장소 및 앱 화면 구현; 3D 지도; 서버 STT/TTS·음성 스트리밍; LLM의 임의 행동 결정 또는 자동 정책 변경; 미검증 확률의 실제 안내 적용; 실제 긴급 연락; 인증정보 커밋; 승인 없는 운영 변경·원격 push
- Validation hint: 시각·단위·좌표·결측·중복 키·버전·개인정보와 실제/모의 식별 예제 검증
- Required docs: `docs/V2/01_서비스_핵심_정리.md`, `docs/V2/02_실시간_서버_배치도.md`, `docs/V2/03_학습_검증_흐름도.md`, `docs/V2/delivery/app-api-contract.md`
- Memory refs: -
- Document outputs: `docs/V2/delivery/data-contract.md`
- Document output exceptions: -
- Source proposal: `-`
- Status: PENDING
- Assigned agent: unassigned

## Advisor Source Prompt

오케 우선은 그거대로 loom에 타스크를 재고정 해

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
## 2026-10-31T08:01:46+00:00

# 2026-10-31-wildfire-mvp 작업 계약 재고정

사용자 지시: “오케 우선은 그거대로 loom에 타스크를 재고정 해”.

2026-10-31 KST 사용자 재고정: 오늘 MVP는 산불 한 종류이며 3D와 서버 STT/TTS·오디오 스트리밍을 제외하고 서버는 텍스트를 제공한다. 공식 경보는 출처·원문·발령 대상을 확인해 개인별 정책 계산과 GPU를 기다리지 않고 우선 전달한다. 일반 분석은 정형 파싱 또는 필요한 Qwen 문서 추출·저장 문서의 임베딩 검색, 사건 통합·위치 관련성·입력 검사, 영향 확률 또는 예측 불가, 검토된 개인별 정책 순서다. 공식 등급·환경 영향 확률·개인 대응 단계를 분리하고 정책은 검토·버전 관리하며 입력 변경 때 재적용한다. 실제 자료·과거 재생·합성 시나리오를 구분하고 실제 정답이 없으면 학습·추론 연결은 simulation으로 검증하며 실제 예측은 unavailable로 둔다. 이 지시는 작업 계약 재고정만 승인하며 구현 실행·Queue 등록·서버 설치·원격 push를 지금 승인한 것으로 취급하지 않는다. 오늘 범위는 이 계약과 Job 재고정 노트를 우선하고 기존 V2 문서는 배경 설계로 참조한다.

이 갱신은 재고정만 수행하며 Task 실행 또는 Queue 등록을 시작하지 않는다.

미정: 시연 지역·사례, 모델의 실제 정답 출처·격자·예측 기간, 개인 대응 단계 매핑, 2D 실제 경로 계산 채택 여부. 60분은 예시이며 실제 확정값이 아니다. 실제 정답 부족은 C4에서 실제 예측 보류로 판정한다.

착수 순서: A1 → B1 → B2 및 C1 → A3·D1·D6 → 수집/긴급 전달·개인 정책·모델 준비 → 안내 갱신 → E2·A4 통합 검증. 공식 원문 전달 D4는 개인 정책 D1/D2와 모델 준비를 선행 조건으로 삼지 않는다.

- B1 `task-20261031-002627-task-35e0acc7`: 산불 수집 경로와 시연 재생 자료·학습 정답 확보 가능성 확인. 선행: A1. 현재 PENDING.
- B2 `task-20261031-002627-task-93368ddf`: 산불 사건·관측·위치·모델 입력과 실제 및 모의 데이터 공통 계약 고정. 선행: B1. 현재 PENDING.
- B3 `task-20261031-002628-task-4b3ae684`: 산불 공식 경보 및 일반 자료 수집기와 시간순 재생·재시도 구현. 선행: A3, B2. 현재 PENDING.
- B4 `task-20261031-002628-task-52ce54a6`: 산불 사건의 근거 연결과 수정·해제·상충 정보 이력 구현. 선행: B3. 현재 PENDING.
- B5 `task-20261031-002628-task-79e4938c`: 산불 발령 구역과 사용자 위치·풍향·주변 영향 관련성 구현. 선행: B4. 현재 PENDING.

구체적 완료 조건은 각 Task의 재고정 계약을 따른다. 기존 docs/V2/04-execution-backlog.md는 이전 계획이며 실제 계약 정본은 현재 Task와 이 노트다.
- Tags: `mvp`, `산불`, `2026-10-31`, `계약재고정`
## 2026-10-31T08:33:37+00:00

2026-10-31 구현 기술 스택 결정: docs/V2/delivery/implementation-stack.md; Task task-20261031-082929-mvp-3188b68a. Python 3.12 + FastAPI/Pydantic 2 + SQLAlchemy 2.x/psycopg 3/Alembic + PostgreSQL 16/PostGIS/pgvector + Celery/Redis + Transformers/Sentence Transformers + XGBoost. 일반 서버 API/정책/CPU 추론, GPU 서버 모델/별도 학습, K8s 수집으로 배치한다. 기관 수집은 HTTPX와 공통 Pydantic 계약으로 구현하며 공간 처리는 PostGIS를 사용한다. 실제/재생/합성 provenance와 시각·원본 참조를 보존한다. 이번 실행은 스택 문서와 계약 연결만 수행하며 다른 구현 Task·Queue·서버 설치는 시작하지 않는다.
- Tags: `기술스택`, `산불`, `MVP`

## Context References

No explicit context references recorded for this job.

## Required Documents and Memory

### required-doc: docs/V2/01_서비스_핵심_정리.md

- Path: `docs/V2/01_서비스_핵심_정리.md`
- Status: present

# 재난 대응 비서 - 서비스 핵심 정리

작성일: 2026-10-31  |  버전: 1.0

이 문서는 재난 대응 비서 관련 대화의 핵심과 설계 후보를 정리한 문서다. 구현·배포·학습·성능 검증이 완료됐다는 의미는 아니다.

## 1. 서비스의 핵심과 목표

> 위험이 사용자에게 영향을 주기 전에, 그 사람이 준비하고 대응하는 데 필요한 시간을 확보해 주는 재난 대응 비서.

공식 경보·관측·뉴스를 지속적으로 수집하고 사용자 위치·상태에 연결한다. 관련 사건의 변화를 추적해 **언제 무엇을 준비해야 하는지** 개인별로 안내하는 것이 서비스의 중심이다. 해커톤에서는 AI 기반 개인별 대응 행동 추천이라는 방향으로 설명할 수 있다.

### 10m 이내의 두 사용자도 서로 다른 안내를 받을 수 있다

| 구분 | 달라질 수 있는 대응 |
| --- | --- |
| 혼자 이동할 수 있는 사용자 | 적용되는 준비 사항과 공식 행동요령 안내 |
| 이동 지원이 필요한 사용자 | 지원 요청·연락·준비 사항을 추가하고, 검토된 정책에 따라 안내 시점 조정 |
| 언어·음성·화면 설정이 다른 사용자 | 선호·접근성 설정에 맞는 전달 방식 적용 |

사용자 상태는 필요한 대응을 바꾼다. 동일한 환경 위험을 평가할 때 이동 능력만으로 화재·연기·물의 도달 확률이 달라지지는 않는다. 가까운 두 지점도 층수·지형·건물 조건에 따라 노출이 다를 수 있으므로, 10m 거리만으로 위험까지 동일하다고 단정하지 않는다.

### 시간을 번다는 의미

상류에서 이미 재난이 발생했더라도 하류 사용자에게 영향이 오기 전에 준비를 시작하게 했다면 목표에 부합한다. 목표는 모든 재난의 발생 시각을 맞히는 것이 아니라, **사용자에게 영향이 도달하기 전 필요한 준비 시간**을 확보하는 것이다.

현재 상태: 서비스 방향과 구성 후보를 정리한 단계다. 실제 예측 모델·개인별 정책·확보 가능한 선행 시간은 검증되지 않았다. 서비스명, 첫 재난 유형, 지역, 세부 대상 사용자는 미정이다.

## 2. 실시간 처리와 판단 주체

### 기본 파이프라인

자료 수집 → 정형 필드 파싱 또는 Qwen 문서 추출 → 사건 통합 → 사용자·관심 장소 관련성 확인 → 필요한 자료 보강 → 모델 입력 검사 → 위험 평가 → 대응 정책 적용 → 알림·안내 갱신. 위치·프로필·통제 정보가 바뀌어도 필요한 단계부터 재평가한다.

| 구성 | 맡기는 역할 |
| --- | --- |
| Qwen3-4B-Instruct-2507 | 약 40억 파라미터의 사전 학습된 텍스트 모델. 사실·장소·시각·상태·근거 추출과 선택된 안내의 설명. Non-thinking 전용 업데이트 모델.[1] |
| Qwen3-Embedding-0.6B | 수집한 문서의 벡터 생성과 관련 문서 검색 지원. 웹 수집 자체는 별도 기능.[2] |
| XGBoost 기반 모델 | 관측값·정리된 입력으로 정해진 영향 확률 추정. 우리 목표에 맞는 학습·검증이 필요하며 현재는 후보.[3] |
| 정책 엔진 | 공식 지침과 사전 검토한 규칙에 사용자 상태·위험 평가를 대입해 알림과 행동 선택 |

### 공식 긴급 경보는 별도 경로

공식 출처와 발령 대상의 관련성을 확인하면 **원문·출처·발령 시각을 우선 전달**한다. 추가 검색·확률 계산·Qwen 설명·음성·지도 로딩을 기다리지 않는다. 낮은 모델 예측값이 공식 긴급 지침을 보류하거나 낮추지 않게 한다.

공식 경보의 긴급성과 행동 지침을 보존한다. 경보가 있다는 이유만으로 모든 상황에 대피를 지시하지 않는다. 공식 경보 상태와 서비스의 개인별 대응 상태는 별도로 표시한다.[6]

### 개인별 정책은 사람이 설계하고 서버가 실행

사용자 정보(위치·이동·지원·설정), 주변 상황(경보·관측·통제), 공통 대응 규칙을 분리한다. 규칙은 공식 행동요령을 바탕으로 작성·검토하며, 실행 시에는 정책 엔진이 자동 적용한다. Qwen은 행동을 임의로 결정하지 않고 선택된 지침을 설명한다.

## 3. 세 가지 검사와 지도 데이터

### 사건 통합·출처·시각 확인

공식 API·기관 원문·뉴스 매체를 구분하고 원문 URL·식별자를 보관한다. 같은 문서의 중복과 같은 사건의 연결을 구분한다. 공식 사건 ID나 갱신 참조가 있으면 우선 사용하고, 없으면 종류·장소·시간으로 후보를 찾는다. 근거가 부족하면 합치지 않고 별도로 유지한다.

발생·관측 시각, 발표 시각, 수집 시각, 유효 종료 시각을 분리한다. 늦게 수집한 과거 기사를 새 사건으로 취급하지 않는다. 발령·수정·해제 관계를 따라 상태를 갱신하며, 문서 추출 성공 자체를 사실 확인 완료로 보지 않는다.[6]

### 내 위치·관심 장소와의 관련성

현재 좌표·위치 정확도·갱신 시각·관심 장소를 공식 발령 구역, 사건 위치, 통제 구간과 비교한다. 공간 포함·교차·거리 계산을 사용하며, 주변 사건은 추가 평가 후보로 본다. 장소가 모호하거나 위치가 오래됐으면 판단 보류·관련 가능성을 유지한다.[7]

### 검증 모델·필요 입력 확보

사전에 등록한 모델의 예측 목표·지역·시간 범위·검증 상태를 확인한다. 실행할 때는 필수 항목, 단위, 시간 기준, 최신성, 검증된 결측 처리 조건을 검사한다. 조건을 만족하지 않으면 예측 불가로 처리하며, 위험 0으로 바꾸지 않는다. 공식 정보 기반 안내는 계속한다.

| 지도 데이터 사용 지점 | 필요한 자료 |
| --- | --- |
| 위치 관련성 | 장소 좌표, 행정구역·발령 구역, 통제 위치 |
| 영향 예측의 입력 | 선택한 재난·모델에 필요한 고도·경사·하천·유역 등 |
| 경로 기능 | 보행·도로 연결망, 계단·경사·출입구·통제·시설 정보 |
| 화면 표시 | 배경 지도와 사건·경로. 3D이면 지형·건물 자료 추가 |

현재 GPS 좌표는 사용자 기기에서 받는다. 지도는 좌표를 구역·도로·지형과 연결한다. 경로 탐색 알고리즘이나 3D 표시 도구만으로 실제 통행 가능성·안전성이 확인되는 것은 아니다.

## 4. 학습해야 할 대상과 개선 과정

> 학습 목표: 이미 발생했거나 발생할 수 있는 재난이, 정해진 시간 안에 특정 위치·경로에 영향을 미칠 확률.

이미 확인된 재난의 발생 여부를 다시 예측하는 것이 아니다. 예를 들어 특정 관측지점의 향후 30분 이내 기준 수위 초과 여부를 목표로 정할 수 있다. 이 결과를 곧바로 사용자 집의 침수 확률로 바꾸어 해석할 수는 없다.

### 학습 자료

| 구분 | 기록할 내용 |
| --- | --- |
| 당시 입력 | 그 시점까지 실제 이용 가능했던 관측·위치·사건 정보와 시각 |
| 예측·운영 기록 | 모델 버전, 예측값, 선택한 안내, 전송 시각 |
| 이후 실제 결과 | 정의한 기간·위치·기준에 따라 영향이 관측됐는지. 발생하지 않은 사례 포함 |

이전 모델의 예측값 자체를 정답으로 사용하지 않는다. 입력과 실제 결과를 연결하는 현재 계획은 **지도학습 기반 재학습**에 가깝다. 행동 선택을 보상으로 개선하는 강화학습은 별도 설계 과제이며 현재 확정된 구현이 아니다.[12]

### 검증·보정·교체

학습·확률 보정·최종 평가 자료를 분리하고 사건·시간 관계를 고려해 정보 누출을 막는다. 놓친 위험, 오경보, 예측 확률과 실제 발생 비율을 확인한다. 단순히 0~1 값을 출력하거나 위험 점수로 이름을 바꾼 것만으로 유효성이 확보되지는 않는다.[4][5]

추론은 새 입력에 맞춰 갱신한다. 재학습은 실제 결과가 누적된 뒤 별도로 수행하고, 사용 기준을 통과한 모델 버전만 교체한다. 미통과하면 기존 모델 또는 공식 정보 기반 운영을 유지한다.

### 아직 구분해야 하는 시간 문제

“30분 안에 영향이 있을 확률”은 정확한 도달 시각을 뜻하지 않는다. 개인별 안내 시점을 결정하려면 예상 영향 시점·불확실성과 준비·이동·지원 소요시간을 어떻게 다룰지 추가 설계가 필요하다.

## 5. 배치 방향과 과거 사례 시연

| 실행 위치 | 제안된 배치 |
| --- | --- |
| 내 K8s | 기관별 수집기, 수집 재시도·상태 관리, 과거 자료 재생, 학습 자료 준비·평가 |
| 제공 일반 서버 | 사용자 API·DB, 긴급·일반 큐와 워커, 사건·공간 분석, XGBoost CPU 추론, 대응 정책·알림 |
| 제공 GPU 서버 | Qwen3-4B·Embedding 추론. 별도 시간의 XGBoost 학습 |
| 사용자 기기 | 위치·설정 전달, 알림 수신, 지도·경로 렌더링 |

GPU 학습 모델은 CPU에서도 실행할 수 있으므로 XGBoost 운영 추론은 일반 서버에 둔다.[3] MeloTTS를 붙이면 일반 서버의 낮은 우선순위 작업으로 검토한다. 경로 계산은 일반 서버, Cesium 화면 표시는 사용자 기기에서 수행하는 방향이다.[10][11]

공유된 GPU 사양은 NVIDIA L4 24GB·4 vCPU·48GB RAM이며 실측 확인 전이다. 일반 서버 사양은 미정이다. 두 Qwen 모델의 실제 메모리·처리량과 네 K8s에서 제공 서버로의 VPN·방화벽 연결을 확인해야 한다.

### 시연 시나리오

1. 한 재난 유형·한 지역의 과거 사례와 원본 발표·관측 시각을 준비한다.

2. 가까운 위치에 있지만 이동·지원·전달 설정이 다른 두 사용자를 등록한다.

3. 당시 공개된 정보만 시간순으로 재생한다.

4. 사전 준비 안내와 사용자별 차이를 보여준다.

5. 공식 긴급 지침 수신 시 AI를 기다리지 않는 전달을 보여준다.

6. 통제·해제 또는 사용자 위치 변경에 따라 안내가 갱신되는 모습을 보여준다.

나중에 알려진 피해 정보를 앞 시점에 넣지 않는다. 시연용 모의 자료·미리 정한 출력과 실제 모델 출력을 구분한다. 한 사례의 시연 성공은 예측 성능 검증을 대신하지 않는다.

### 확인할 지표

발표→서버 수신→단말 도착의 시간, 개인별 안내의 근거·적합성, 준비 가능한 시간, 중복·낡은 경보 억제, 위험 누락·오경보를 확인한다. “어디보다 빠르다”는 비교 검증 전의 목표이며 보장된 성능이 아니다.

## 6. 남은 결정과 검증 항목

| 항목 | 아직 결정하거나 확인할 내용 |
| --- | --- |
| 첫 적용 범위 | 재난 유형·지역·사용자·예측 시간·영향 기준 |
| 자료 확보 | 기관별 API·갱신 주기·과거 자료·실제 결과 라벨·사용 조건 |
| 사건·시간 처리 | 식별자, 수정·해제, 중복·상충 정보, 출처·유효시간 처리 |
| 위치 관련성 | 행정구역·위치 오차·경로·상류하류 등 재난별 관계 기준 |
| 예측 모델 | 학습 가능성, 적용 범위, 결측·노후 입력 처리, 평가·보정 합격 기준 |
| 개인 대응 정책 | 공식 지침과 사용자 상태를 연결하는 규칙, 알림 시점·해제·변경 조건 |
| 필요한 시간 | 영향 예상 시점과 준비·이동·지원 소요시간의 산정 방식 |
| 경로·시설·3D | 실제 통행·접근성·시설 이용 가능 정보 확보 여부와 기능 범위 |
| 실행 환경 | 일반 서버 용량·저장공간, GPU 처리량, 서버 간 통신, 푸시 구현 |
| 운영 개선 | 기록 방식, 실제 결과 확인, 재학습 주기, 검증 후 교체 기준 |

### 현재 MVP 방향으로 제안된 범위

한 지역·한 재난 유형에서 수집→사건 연결→사용자 관련성→개인별 안내 갱신을 우선 완성한다. 공식 경보 즉시 전달은 별도로 확보한다. 확률 예측은 학습·검증과 입력 조건이 확보된 경우에 붙이며, 상세 경로·3D는 데이터 확보에 따라 확장한다.

> 가장 중요한 검증 질문: 특정 재난 사례에서 특정 사용자에게 실제로 필요한 준비 시간을 더 확보해 줄 수 있는가?

서비스명은 미정이다. 이정·지표·파수·기점, BEARING·SENTINEL·AEGIS·MERIDIAN 등의 후보가 논의됐으며 최종 선택·명칭 사용 가능 여부는 확인하지 않았다.

## 7. 참고 자료와 문서 구성

이 문서는 재난 대응 비서 관련 대화의 핵심과 설계 후보를 정리했다. 아래 자료는 도구·개념을 확인하기 위한 참고이며, 우리 서비스의 데이터 확보나 예측 성능을 입증하는 자료는 아니다.

### 공식 참고 자료

[1] [Qwen3-4B-Instruct-2507 모델 설명](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507)

[2] [Qwen3-Embedding-0.6B 모델 설명](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B)

[3] [XGBoost GPU 학습·CPU/GPU 호환](https://github.com/dmlc/xgboost/blob/master/doc/gpu/index.rst)

[4] [scikit-learn 확률 보정](https://scikit-learn.org/stable/modules/calibration.html)

[5] [scikit-learn 시간·그룹 기반 검증](https://scikit-learn.org/stable/modules/cross_validation.html)

[6] [OASIS CAP 1.2 경보 규격](https://docs.oasis-open.org/emergency/cap/v1.2/CAP-v1.2-os.html)

[7] [PostGIS 공간 교차](https://postgis.net/docs/ST_Intersects.html) / [거리 검사](https://postgis.net/docs/ST_DWithin.html)

[8] [UNDRR 조기경보 체계 정의](https://www.undrr.org/terminology/early-warning-system)

[9] [Kubernetes CronJob](https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/)

[10] [MeloTTS 한국어 모델](https://huggingface.co/myshell-ai/MeloTTS-Korean)

[11] [CesiumJS](https://cesium.com/platform/cesiumjs/)

[12] [Google 지도학습·실제 정답 용어 설명](https://developers.google.com/machine-learning/glossary#supervised-machine-learning)

### 세 문서의 역할

| 문서 | 내용 |
| --- | --- |
| 01 핵심 정리 | 목적·모델·정책·판단 기준·데이터·시연·미정 사항 |
| 02 실시간 서버 배치도 | 사용자가 제공한 Mermaid 배치도와 각 경로의 실행 위치 |
| 03 학습·검증 흐름도 | 실제 결과 연결, 학습·보정·평가, 모델 버전 교체 |

## 함께 볼 문서

- [실시간 서버 배치도](02_실시간_서버_배치도.md)
- [학습·검증 흐름도](03_학습_검증_흐름도.md)

두 문서에는 수정 가능한 Mermaid 원문이 포함돼 있다.

### required-doc: docs/V2/02_실시간_서버_배치도.md

- Path: `docs/V2/02_실시간_서버_배치도.md`
- Status: present

# 재난 대응 비서 - 실시간 서버 배치도

작성일: 2026-10-31  |  버전: 1.0

내 K8s 수집 / 제공 일반 서버 판단·전달 / 제공 GPU 서버 추론

대화에서 정리한 설계안이다. 현재 학습·배포·검증이 완료됐다는 의미는 아니다.

## 다이어그램

```mermaid
flowchart TD
    S["공식 경보·기상·관측·뉴스"]

    subgraph K["내 K8s · 데이터 수집"]
        direction TB
        K1["공식 경보 수집기 · 상시 실행"]
        K2["관측·공지·뉴스 수집기"]
        K3["재시도·중복 전송 관리"]
        K2 --> K3
    end

    subgraph C["제공 일반 서버 · 서비스와 판단"]
        direction TB
        I["이벤트 수신 API"]
        U["긴급 전용 큐·워커"]
        N["일반 분석 큐·워커"]
        T["발령 대상 확인·공식 원문 구성"]
        E["사건 통합·위치 관련성·입력 검사"]
        X["XGBoost 추론 · CPU"]
        P["개인별 대응 정책"]
        A["알림 전송"]
        API["사용자 API · 위치·프로필"]
        DB[("DB · 사건·프로필·로그·공간·벡터")]
        I -->|"공식 긴급 경보"| U
        U --> T
        T --> A
        I -->|"상세 분석 자료"| N
        N --> E
        E -->|"모델·입력 사용 가능"| X
        X --> P
        E -->|"예측 불가·공식 근거 활용"| P
        P --> A
        API --> DB
        API -->|"위치·상태 변경"| E
        DB <--> E
        DB --> T
    end

    subgraph G["제공 GPU 서버 · AI 추론"]
        direction TB
        G1["추론 API · Qwen3-4B"]
        G2["임베딩 API · Qwen3-Embedding"]
    end

    M["모바일·웹 클라이언트"]
    S --> K1
    S --> K2
    K1 --> I
    K3 --> I
    N <-->|"문서 추출"| G1
    N <-->|"벡터 생성"| G2
    P <-->|"필요할 때 보충 설명"| G1
    M -->|"현재 위치·설정"| API
    A -->|"푸시·화면 갱신"| M

    classDef urgent fill:#fff0ee,stroke:#db5347,stroke-width:2px,color:#7f2019;
    classDef gpu fill:#edf8f3,stroke:#299b71,color:#12563c;
    class U,T,A urgent;
    class G1,G2 gpu;
```

## 해설

> 공식 긴급 경보: K8s 수집 → 일반 서버 긴급 큐·워커 → 발령 대상 확인 → 공식 원문 전달. GPU 추론을 기다리지 않는다.

| 영역 | 주요 책임 |
| --- | --- |
| 내 K8s | 기관별 상시 경보 수집과 관측·공지·뉴스 수집. 재시도·수집 상태 관리 |
| 일반 서버 | 이벤트·사용자 API, 긴급/일반 작업 분리, DB, 사건·공간 분석, XGBoost CPU 예측, 대응 정책·알림 |
| GPU 서버 | Qwen3-4B-Instruct-2507의 추출·설명, Qwen3-Embedding-0.6B의 벡터 생성 |
| 사용자 기기 | 위치·설정 전달, 알림 수신, 지도 표시 |

### 도표를 읽는 기준

일반 분석 워커는 문서가 필요할 때 GPU를 호출한다. 구조화된 관측자료는 Qwen을 생략할 수 있다. 벡터 생성은 GPU, 벡터 저장·검색은 일반 서버다. 사건 통합·위치 관련성·입력 검사는 일반 서버에서 수행한다.

XGBoost는 검증된 모델과 입력 조건이 확보된 경우에만 호출한다. 사용할 수 없으면 공식 정보 기반 대응을 유지한다. 사용자 위치·지원 상태가 바뀌면 필요한 단계부터 재평가한다.

빨간 노드는 긴급 경보 전달 경로다. 마지막 알림 전송 노드는 일반 안내도 공유한다. 초록 노드는 GPU 모델 API다. 양방향 연결은 요청과 결과 반환을 뜻하며 실시간 자동 재학습을 뜻하지 않는다.

### 구현 전에 확인할 사항

긴급·일반 큐와 워커의 실행 자원을 분리하고, 수집·처리·알림의 중복과 갱신·해제를 관리한다. 긴급 수집기에도 자체 재시도·중복 방지 기준이 필요하다. 도표는 핵심 연결을 표현하므로 원문·로그 저장과 모든 DB 접근선은 생략돼 있다.

일반 서버 사양과 네 K8s에서 제공 서버로의 VPN·방화벽 연결은 미확인이다. Qwen 두 모델의 메모리·처리량은 실제 자료로 측정한다. GPU 장애가 있어도 긴급 경보는 처리하도록 구성하되, 수집기·일반 서버·네트워크의 가용성은 별도로 확보해야 한다.

## 함께 볼 문서

- [서비스 핵심 정리](01_서비스_핵심_정리.md)

- [학습·검증 흐름도](03_학습_검증_흐름도.md)

### required-doc: docs/V2/03_학습_검증_흐름도.md

- Path: `docs/V2/03_학습_검증_흐름도.md`
- Status: present

# 재난 대응 비서 - 학습·검증 흐름도

작성일: 2026-10-31  |  버전: 1.0

실제 결과 연결 / 학습 / 확률 보정·평가 / 검증 모델 배포

대화에서 정리한 설계안이다. 현재 학습·배포·검증이 완료됐다는 의미는 아니다.

## 다이어그램

```mermaid
flowchart TD
    subgraph C["제공 일반 서버"]
        L[("입력·예측·안내 로그와 실제 관측 결과")]
        ACTIVE["검증된 XGBoost 모델 · CPU 운영"]
        KEEP["기존 모델 또는 공식 정보 기반 운영 유지"]
    end

    subgraph K["내 K8s · 학습 작업 준비"]
        D["입력·실제 결과 연결"]
        SPLIT["사건·시간 기준으로 데이터 분리"]
        V["확률 보정·별도 평가"]
        CHECK{"사용 기준 통과?"}
        D --> SPLIT
        V --> CHECK
    end

    subgraph G["제공 GPU 서버 · 별도 학습 작업"]
        TRAIN["XGBoost 학습"]
    end

    L --> D
    SPLIT -->|"학습 자료"| TRAIN
    TRAIN -->|"모델 파일"| V
    SPLIT -->|"보정·평가 자료"| V
    CHECK -->|"통과한 버전만 배포"| ACTIVE
    CHECK -->|"미통과"| KEEP
    ACTIVE -->|"새 추론 기록"| L
```

## 해설

> 이전 추론값 자체를 정답으로 삼지 않는다. 당시 입력과 이후 실제 관측 결과를 연결하고, 검증한 모델 버전만 운영에 반영한다.

| 단계·위치 | 처리 내용 |
| --- | --- |
| 기록 - 일반 서버 | 입력·자료 시각·모델 버전·예측값·안내·전송 시각과 실제 결과 보관 |
| 자료 준비 - K8s | 예측 대상·기간에 맞춰 입력과 정답 연결. 사건·시간 기준으로 자료 분리 |
| 학습 - GPU 서버 | XGBoost 학습. 작은 자료라면 CPU 학습 가능성도 있으나 현재 배치안은 GPU 활용 |
| 보정·평가 - K8s | 학습과 분리한 자료로 확률 보정 및 별도 성능 평가 |
| 운영 반영 - 일반 서버 | 사전에 정한 사용 기준을 통과한 버전만 CPU 추론에 배포 |

### 분리해야 하는 자료

학습용, 확률 보정용, 최종 평가용 자료를 구분한다. 같은 사건의 정보나 미래 관측이 경계를 넘어 섞이지 않도록 한다. 당시 수집·이용할 수 없던 후속 기사를 과거 입력에 넣지 않는다. 영향이 없었던 사례도 평가에 포함한다.

### 반복 추론과 재학습의 차이

실시간 반복 추론은 고정된 모델에 최신 입력을 넣는 과정이다. 재학습은 실제 결과가 누적된 뒤 새 모델을 만드는 별도 작업이다. 이 계획은 지도학습 기반 개선이며, 행동 선택을 보상으로 학습하는 강화학습은 별도 과제다.

### GPU 운영과 모델 교체

첫 시연 전에 학습을 끝내고 시연 중 GPU는 Qwen·Embedding 추론에 집중시키는 방향을 권한다. 동일 GPU의 추론과 학습을 동시에 수행할지는 메모리·처리량을 확인한 뒤 결정한다. 새로운 모델이 기준을 통과하지 못하면 기존 모델 또는 공식 정보 기반 운영을 유지한다.

아직 미정: 실제 학습 자료, 예측 목표, 합격 기준, 재학습 주기, 배포 승인·되돌리기 절차. XGBoost는 재난 예측이 완성된 모델이 아니라 목표에 맞게 학습할 도구다.

## 함께 볼 문서

- [서비스 핵심 정리](01_서비스_핵심_정리.md)

- [실시간 서버 배치도](02_실시간_서버_배치도.md)

### required-doc: docs/V2/delivery/app-api-contract.md

- Path: `docs/V2/delivery/app-api-contract.md`
- Status: present

# 봉화지기 앱 API 계약 — 0.1.0 초안

작성일: 2026-10-31 KST. 기준: V2 서비스·배치·학습 설계와 최신 [5개 화면 기획서](../../HeoNey/봉화지기_모바일_화면_기획서.md). API Job: `job-20261031-002626-api-18805e8a`.

**앱팀의 화면 및 모의 연동 개발을 위한 계약 초안이다. 서버가 구현·배포되었다는 뜻은 아니다.** 필드 이름·경로·오류 처리의 협업 기준을 구체화했으며, 공통 데이터 B2와 정책 D1 확정 후 E1에서 승인본으로 고정한다. 모든 예제는 모의 자료이고 실제 재난 대응이나 119 연락에 사용하지 않는다.

## 전달 파일

| 파일 | 용도 |
| --- | --- |
| [앱팀 인계서](api-handoff.md) | 화면별 호출 순서·필드 연결·앱과 서버의 책임·인수 검사 |
| [API별 사용법](api-reference.md) | 전체 25개 API의 경로, 대응 화면, 입력, 오류, curl, 요청·응답 예제 |
| [OpenAPI](api/openapi.yaml) | 기계가 읽는 필드 타입·필수값·열거형·성공 및 오류 스키마 정본 |
| [HTTP·푸시 예제](api/examples.json) | 고정 시각의 48개 HTTP 교환과 푸시 자료. `id`로 선택해 화면 fixture로 사용 |
| [화면 매핑](api/screen-map.json) | 모든 operationId와 화면 번호의 대응 |
| [Job 재검토](api-job-review.md) | 기존 E1/E2와 이번 초안의 관계, 변경 요구·미결정·담당 |
| [정적 검증 결과](api/validation-report.json) | 명세·예제·화면 연결 검증 범위와 한계 |

OpenAPI의 성공 응답은 채택 시의 계약을 표현한다. `x-stage: conditional`인 기능은 현재 구현 대상이 확정되지 않았고 기능 설정의 기본값도 꺼져 있다. 본문과 OpenAPI가 충돌하면 임의로 구현하지 말고 계약 수정으로 해결한다.

## 접속과 인증

- 논리 기준 주소: `https://api.example.invalid`. **자리표시자라 접속되지 않는다.** 운영·개발 API 주소, 인증서, 인증 발급자는 A3/E1 결정 항목이다. 현재 확인된 Tailnet SSH 주소를 모바일 HTTPS API 주소로 사용하지 않는다.
- 경로 접두사: `/v1`. 요청·응답: UTF-8 JSON. 오류: `application/problem+json`.
- `GET /v1/app-config`만 공개. 나머지는 `Authorization: Bearer <access_token>`을 요구한다. 사용자 ID는 토큰 주체에서 결정하고 앱이 임의 `user_id`를 보내 타인의 자료에 접근할 수 없게 한다.
- access token 발급·갱신/로그아웃 흐름과 issuer/audience는 아직 미정이다. 앱은 인증 모듈을 분리하고 fixture 단계에서는 가짜 토큰만 사용한다. 실서버 연동 전 반드시 인증 계약과 테스트 계정을 받아야 한다.
- 로그인 사용자 소유가 아닌 경보·안내·설치·발화 ID는 존재 여부를 노출하지 않는 404로 처리한다. 실제 인증 실패는 401, 계정/권한 자체의 금지는 403이다.
- 푸시 토큰·음성 텍스트·정밀 위치는 URL, 분석 로그, 오류 메시지에 넣지 않는다. 개인 응답은 `Cache-Control: private, no-store`. 앱 내 오프라인 자료는 별도 암호화 저장·삭제 정책을 합의한다.
- `X-Request-ID`는 문의용 추적 ID이고 개인정보를 포함하지 않는다. 문서의 access token·push token은 모두 가짜다.

## 시간·위치·누락값

| 항목 | 계약 |
| --- | --- |
| 시각 | RFC 3339 UTC `Z`. 화면에서 사용자 시간대로 변환. `published_at`, `observed_at`, `collected_at`을 구분 |
| 위치 입력 | `latitude`, `longitude`, `accuracy_m`, `captured_at`, `fix_id`, `installation_id` |
| 지도 좌표 | WGS84 GeoJSON `[경도, 위도]`. 경로의 세 번째 값은 WGS84 타원체고(m)이며 다른 고도 기준과 혼용 금지 |
| 위치 품질 | `available / stale / inaccurate / unavailable`. GPS 실패·권한 거부를 임의 좌표나 안전 판정으로 대체하지 않음 |
| 시간 역전 | 오래된 위치는 409 `STALE_LOCATION`; 단말 시각이 서버보다 120초 이상 미래면 422. `fix_id`의 동일 본문 재전송은 동일 결과, 다른 본문 재사용은 409 |
| 예측 불가 | `impact.status=unavailable`, `probability=null`, `reason_codes` 필수. 0%로 표시 금지 |
| 알 수 없는 값 | `null` 또는 명시된 `unknown`. 생략의 의미는 각 요청 스키마를 따른다. boolean false로 미확인을 표현하지 않음 |
| 자료 없음 | 정상 조회이지만 자료가 없으면 200과 `unavailable`/빈 배열. 통신·인증 실패는 해당 HTTP 오류 |

위치 300초·정확도 100m, 현재 상태 60분, 변경 커서/멱등 기록 24시간, 기본 주변 반경 5km는 **이번 연동을 위한 제안값**이다. 위험 판단의 검증된 임계값이 아니다. 서버 설정이 정본이며 E1에서 조정한다. 앱에서 별도의 위험 임계값을 하드코딩하지 않는다.

## 공통 응답과 기능 상태

성공 응답은 `{ "meta": {...}, "data": {...} }`다. 204에는 본문이 없다.

| meta 필드 | 의미 |
| --- | --- |
| `schema_version` | 자료 계약 `0.1.0` |
| `mode` | `live / simulation`. simulation은 화면과 시연에 식별 표시 |
| `generated_at` | 서버가 이 응답을 만든 시각. 원자료 발표 시각이 아님 |
| `data_status` | `current / partial / stale / unavailable`. 빈 목록만 보고 안전하다고 해석하지 않음 |
| `request_id` | 오류 문의 및 서버 추적 |

설정의 `features`와 홈의 `capabilities`는 해당 서버가 제공하는 기능이다. OS 마이크/위치/알림 권한과는 다르다. `voice_turns`, `guidance_tts`, `route_3d`, `impact_prediction`은 기본 비활성이다. `support_draft`는 문자 **미리보기** 가능 여부이며 실제 신고 가능 여부가 아니다. 영어는 스키마상 확장 후보이며 기본 지원 언어는 한국어다. 미지원 설정은 422; 수칙 번역이 없으면 원문 언어와 `locale_fallback=true`를 반환한다.

## 홈의 기간·지역 계약

1. `scope=current_location`은 서버가 가진 유효 GPS를 사용한다. 위치가 없으면 `feed.scope=unavailable`이고 최근 캐시를 현재 위치 자료처럼 표시하지 않는다.
2. 사용자가 지역을 골랐을 때만 `scope=selected_area&area_code=...`로 조회한다. 지도/설정에 선택 지역임을 표시하고 긴급 경보의 GPS 발령 대상과 혼동하지 않는다. 지역 코드 카탈로그·지도 SDK는 A1/B1/E1에서 확정한다.
3. 진행 중 사건은 발생일이 3개월보다 오래되어도 포함한다. 종료된 사건은 `ended_at`이 `[window_start, window_end]`에 포함되면 표시한다. 종료 시각을 확인할 수 없는 자료는 과거로 단정하지 않고 unknown으로 분류한다.
4. 제안 기간 계산은 Asia/Seoul 기준 조회 시각에서 **달력상 3개월**을 뺀 값이다. 없는 날짜는 해당 월 말일로 보정한다. 90일 고정으로 바꾸지 않는다. 응답의 UTC window 값을 사용한다.
5. 진행 중/unknown 우선, 이후 과거; 각 그룹은 `updated_at DESC, id ASC`의 안정 순서다. cursor는 조회 조건과 snapshot을 고정한다. 재조회 조건 변경·커서 만료는 처음부터 조회한다.
6. 홈은 요약 목록으로 완결한다. 과거 항목의 `display_title`에는 ‘발생’을 제외하고 `original_title`은 근거 보존용이다. 상세 화면 이동을 넣지 않는다. 3개월 자료 확보 여부는 B1에서 검증하며 미확보는 `data_status=partial`로 드러낸다.

## 긴급 화면의 판단 분리

| 데이터 | 화면에서의 사용 | 금지되는 해석 |
| --- | --- | --- |
| `official_alert.official_severity` | 기관이 보낸 코드·명칭·체계를 유지 | 임의로 1~5등급으로 변환하거나 없는 등급 생성 |
| `official_alert.instruction_kind` | 실제 공식 지시 종류 | 모든 경보를 ‘대피 명령’이라고 표시 |
| `personal_response` | 개인별 정책 적용 상태 및 이유 | 환경 위험 확률과 같은 등급으로 혼합 |
| `impact` | 검증 범위 내 특정 목표/기간의 확률 | 특정 관측소 수위 확률을 사용자의 집 침수 확률로 전환 |
| `relevance` | 상류·풍향·발령 구역·인근 관계 및 근거 | 현재 행정구역 밖이라는 이유만으로 사건 제외 |
| `sources` | 발표·관측·수집 시각과 원문 추적 | 재인용 기사 수를 독립 근거 수로 계산 |
| `actions` | 검토된 정책이 선택한 번호별 행동 | 모델 발화를 그대로 행동 명령으로 채택 |

개인 대응 enum은 `information / attention / prepare / act / request_assistance / unknown`을 제안한다. 승급·하향·해제의 수치 조건은 D1 검토 전 확정하지 않았다. 공식 지시가 먼저 도착하면 `getAlert`로 원문부터 표시하며 개인 평가·음성·경로·지도 로딩을 기다리지 않는다. 낮은 예측값으로 공식 지시를 숨기지 않는다. 경보 해제와 ‘사용자가 안전함’은 다르다.

## 프로필과 현재 상태

- 사전 프로필은 S4에서 수정하고 현재 상태는 S2의 해당 `response_id`에만 저장한다. 임시 상태가 사전 프로필을 덮어쓰지 않는다.
- 이번 제안은 이동, 계단, 전달 선호, 감각 지원, 동반 보호 대상만 받는다. 이름·나이·상세 질환·주소·보호자 연락처는 자동 추가하지 않는다. 세부 항목 자체도 화면 기획상 제안이며 E1 확정 대상이다.
- 프로필 미등록은 `revision=0, profile={}`. PUT은 전체 교체이며 빠진 필드는 제거한다. 현재 상태의 mobility/stairs가 null이면 사전 프로필을 상속한다.
- `alone_now`는 `yes/no/unknown`. 1인 가구라는 이유만으로 지금 혼자 있다고 판단하지 않는다. 태그에는 `origin`, `confirmed_at`, `expires_at`을 붙인다.
- `putCurrentContext`는 사용자 확인 후에만 호출한다. 음성 모델의 `proposed_context`는 후보이며 `requires_user_confirmation=true`다. 확인 전에는 태그·경로·정책에 확정 사실로 적용하지 않는다.
- 사용자 확인은 단말 UI 또는 확인된 발화 입력의 의미이며, 단순히 확인 필드를 true로 만드는 것만으로 구현 검증이 끝나지 않는다.

## 버전·동시성·갱신

1. profile/preferences/context의 `base_revision`이 현재 값과 다르면 409. 최신 값을 다시 읽고 사용자의 변경을 재적용한다. 오래된 값을 무조건 덮어쓰지 않는다.
2. 위치·프로필·상태 저장 성공은 새 안내 계산 완료가 아니다. `response.input_versions`가 최신 입력을 반영하기 전까지 ‘갱신 중’으로 다루고 오래된 경로를 사용하지 않는다.
3. 안내 `revision`은 같은 response_id 안에서만 비교한다. 서버는 오래된 계산 결과를 최신 버전으로 발행하지 않아야 한다. 앱은 이미 적용한 revision 이하의 중복/역순 갱신을 버린다.
4. `valid_until`이 지나면 현재 안내/경로를 유효한 것으로 재사용하지 않는다. 재조회 실패 시 캐시에는 시각과 만료 상태를 표시하고 경로 안내는 중단한다. 취소·해제 상태도 원자적인 전체 응답으로 적용한다.
5. `superseded`이면 `superseded_by`를 새로 조회한다. `resolved`는 해당 사건 안내 종료이지 전체 지역의 안전 보장이 아니다. 다른 활성 경보는 유지한다.
6. POST는 `Idempotency-Key` 필수다. 사용자+메서드+경로 범위에서 같은 키/같은 본문은 같은 결과를 반환한다. 같은 키/다른 본문은 409. 본문을 바꿔 새 작업을 요청할 때 새 키를 쓴다.

## 푸시와 전경 앱 갱신

백그라운드는 푸시, 전경은 `getUpdates` long polling을 기본 제안으로 한다. 5분 수집 주기를 단말 갱신 주기로 고정하지 않는다. 푸시/폴링 모두 같은 리소스 버전을 사용하며 중복 처리를 허용한다.

- 초기/재동기화: `getHome`의 `sync_cursor`는 홈 스냅샷과 일관된 변경 경계다. 활성 경보/안내를 읽은 뒤 이 커서부터 변경을 소비한다. 서버는 홈 스냅샷 이후 변화가 커서 뒤에서 빠지지 않도록 보장해야 한다.
- 푸시의 `PushPayload`는 논리 JSON이다. FCM/APNs 실제 payload 포장과 문자열 인코딩은 서버 어댑터의 책임이다. 잠금 화면에 위치·상태 태그·전체 맞춤 행동을 넣지 않는다.
- `alert.upserted`는 공식 경보 GET 우선, `alert.cancelled`는 취소 상태 GET 우선이다. 푸시 ID나 본문만으로 대피/해제를 확정하지 않는다. 네트워크 오류 시 최근 유효 원문만 시각과 함께 유지한다.
- 이벤트→조회 매핑: alert.*→getAlert, response.*→getResponse, profile.updated→getProfile, location.changed→getLocation, preferences.updated→getPreferences, voice_turn.ready→getVoiceTurn(이벤트의 response_id 사용), home.changed→getHome. 다른 안내에서 시작한 음성 결과는 현재 S2에 섞지 않는다.
- 페이지를 모두 처리한 뒤 `next_cursor`를 저장한다. `has_more=true`이면 대기 없이 이어서 호출한다. 410이면 커서를 버리고 홈·활성 경보부터 다시 읽는다. 호출 실패 때 커서를 전진시키지 않는다.
- OS가 앱을 깨우거나 화면을 앞으로 가져오는 것, 최대 음량, 실제 푸시 수신 시점은 이 API 계약이 보장하지 않는다. 영수증은 단말의 received/displayed/opened 보고이며 대피·신고 접수 증빙이 아니다.

## 3D·음성·119 경계

**3D:** `route_3d.enabled`이고 최신 안내의 `route_availability.status=available`이며 만료 전일 때만 버튼을 표시한다. 진입 시 현재 `response_revision`으로 getRoute를 다시 확인한다. 조건이 바뀌면 409 또는 unavailable이므로 기존 선을 제거하고 S2로 돌아간다. 생성형 모델로 도로를 만들지 않는다. geometry·접근성 자료·검증 시각·출처가 있다고 절대 안전을 보장하는 문구를 표시하지 않는다. S3 상세 UI는 보류다.

**음성:** 조건부 voice-turn API는 단말 STT 결과 텍스트를 서버에 주고 결과 한 건을 받는 비동기 제안이다. 실시간 오디오 스트리밍/WebSocket 규격이나 끼어들기 성능 약속이 아니다. 기존 D6/D7의 범위 밖인 양방향 음성은 별도 채택 결정이 필요하다. 꺼져 있으면 501을 처리하고 텍스트·현재 상태 수정으로 진행한다. TTS 채택 시에도 최신 발화만 재생하고, 사용자가 끼어들면 단말 재생을 먼저 중단한다. signed audio URL의 수명과 삭제·보관은 E1에서 정한다.

**119:** createSupportDraft는 현재 사용자가 확인한 상태와 유효한 위치의 문자 초안만 만든다. 항상 `delivery_status=not_sent`. 앱에서 미리보기와 사용자 확인 후 OS 문자 작성/전화 화면으로 넘기는 방식이다. API 실패나 오프라인이어도 전화 버튼은 서버 응답을 기다리지 않고 단말에서 접근 가능해야 한다. 실제 전송·통화·접수 완료를 하나의 성공 표시로 합치지 않는다. 시연에서는 실제 119 통화/전송을 하지 않는다.

## 오류와 앱 처리

| HTTP / code 예 | 앱 처리 |
| --- | --- |
| 400 INVALID_REQUEST | query 조합/형식 수정. selected_area인데 area_code 없는 경우 등 |
| 401 UNAUTHENTICATED | 인증 모듈 갱신 후 1회 재시도. 실패하면 로그인 흐름. 무한 재시도 금지 |
| 403 FORBIDDEN | 계정/권한 문제 안내. 위치/마이크 OS 거부와 혼동하지 않음 |
| 404 NOT_FOUND | 없는/접근 불가 리소스. 활성 목록 재조회, 다른 사용자 ID 시도 금지 |
| 409 VERSION_CONFLICT / STALE_LOCATION / RESPONSE_REVISION_CHANGED | 최신 버전을 읽고 재적용. 경로 충돌이면 기존 경로 제거 |
| 410 CURSOR_EXPIRED | cursor 폐기, 홈과 활성 경보부터 재동기화 |
| 422 VALIDATION_ERROR / UNSUPPORTED_LOCALE | 필드 오류를 표시하고 수정. 재시도만 반복하지 않음 |
| 429 RATE_LIMITED | Retry-After 존중, 이후 지수 지연+지터. 최신 안내의 유효시간 확인 |
| 501 FEATURE_UNAVAILABLE | 해당 선택 기능 중단, 텍스트/기본 수칙/단말 연락 기능으로 진행 |
| 503 SERVICE_UNAVAILABLE | Retry-After가 있으면 따름. 실패를 안전·해제·신고 완료로 표시하지 않음 |

네트워크 재시도 제안: 1·2·4·8초, 이후 최대 30초와 지터. 전경 long polling 연결 제한 시간은 wait_seconds보다 길게 설정한다. 실제 요청 제한·백오프 상한은 부하 시험 후 확정한다.

## 재현 가능한 계약 검사

저장소 루트에서 실행한다. API 서버나 긴급 연락처를 호출하지 않는다.

```sh
python3 -m venv /tmp/bonghwajigi-api-check
/tmp/bonghwajigi-api-check/bin/python -m pip install -r docs/V2/delivery/api/requirements-validation.txt
/tmp/bonghwajigi-api-check/bin/python tools/validate_app_api.py
```

OpenAPI/예제 검사는 실제 서버 동작 검사와 다르다. E2에서 인증·실제 푸시·버전 역전·해제·접근 제어·앱 예외 처리의 종단간 결과를 추가한다.

## 표준 근거

기계 명세는 [OpenAPI 3.1 계열](https://spec.openapis.org/oas/v3.1.1.html), 오류 객체는 [RFC 9457](https://www.rfc-editor.org/rfc/rfc9457.html), 지도 좌표 형식은 [RFC 7946](https://www.rfc-editor.org/rfc/rfc7946.html)을 참고했다. 이 표준은 우리 데이터 정확도·재난 정책·운영 가용성을 검증하지 않는다.

## Verified Team Policies

No verified Team Policy Snapshot is active.

## Active Workflow Memory

No active workflow memory recorded.
