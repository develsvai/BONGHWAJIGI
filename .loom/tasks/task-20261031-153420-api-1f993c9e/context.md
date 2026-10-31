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
- Task count: `5`

## Task

- Title: 앱 설치 계정·세션과 목업 프로필·사전준비 API 구현
- Description: 사용자의 완성 목업 앱 구현·실서버 검증·APK 배포 직접 지시에 따라 사설망 simulation 설치 계정 등록·토큰 갱신·로그아웃을 제공하고 목업 프로필 추가 필드와 별도 사전준비 카드·기본수칙 회피 분류를 구현한다. 실제0.2 계약과 앱 타입을 맞출 수 있도록 출력 스키마·예제를 고정한다.
- Expected output: 설치 계정·회전 세션 API와 migration; 프로필·동의/삭제·준비 카드; 명시적인 실행 응답 계약과 검증; 일반 서버 배포 가능한 변경
- Done condition: 앱에 서버 비밀키를 넣지 않고 등록·갱신·로그아웃·프로필 저장/삭제·개인별 준비 카드가 DB에서 동작한다. 사용자 격리·refresh 회전/재사용·revision·민감 메모 동의·출처와 미제공 상태를 검증하고 기존82개 서버 기능을 보존한다.
- In scope: 사설망 simulation 설치 계정과 세션; 프로필 추가 필드; 동의/삭제; 준비 지침·출처; 실제 응답 계약·테스트·운영 문서
- Out of scope: 진행 중 학습 변경/중단; 실제 예측 연결; 3D/실제 도로 탐색; Firebase 실발신; 서버 STT/TTS; 실제119연락; 외부 계정 생성/결제; 비밀값 커밋
- Validation hint: 실제PostgreSQL migration와 사용자/토큰 경계·동의·준비 카드 테스트, 기존 서버 회귀·Ruff·OpenAPI·Loom strict
- Required docs: `docs/V2/delivery/mvp-app-api.md`, `docs/V2/delivery/mvp-server-runbook.md`
- Memory refs: -
- Document outputs: `docs/V2/delivery/app-integration-api.md`
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

### required-doc: docs/V2/delivery/mvp-app-api.md

- Path: `docs/V2/delivery/mvp-app-api.md`
- Status: present

# 산불 MVP 앱 API 실행 계약

2026-10-31, Loom Task `task-20261031-132925-api-181c0498`. 사용자 확정 단계는 **경고·대피·위급**이며 [정책 기준](response-policy.md)을 따른다. 실제 사설망 접속·계정 발급·배포 결과는 [서버 운영 문서](mvp-server-runbook.md)를 따른다. 앱 저장소는 변경하지 않았다.

## 버전과 인계

실행 계약은 **0.2.0-mvp**다. 종전 `api/openapi.yaml`의 0.1.0-draft는 구현 이전 화면 계약이며 그대로 보존했다. 현재 상태 입력·3단계·모의 전송·예측 제외를 반영한 실행 API는 [현재 OpenAPI](api/mvp-openapi.json)와 서버 `/openapi.json`이다. 0.1 응답 타입을 그대로 서버 완료본으로 사용하지 않는다.

모든 `/v1` 요청에 해당 사용자의 `Authorization: Bearer <access_token>`을 보낸다. 공통 응답은 `meta`와 `data`다. `meta`에는 schema_version, simulation, request_id, generated_at, data_status가 있다. 내부 `/internal/v1`은 다른 서비스 토큰을 사용하며 앱에 서비스 토큰이나 JWT 서명키를 넣지 않는다.

개인 안내는 `data.id`, `data.revision`, `data.pending_update`, `data.content`로 제공한다. `content.personal_response`에 level/number/label/policy_version, `content.actions`에 번호별 행동, `content.official_alerts`에 기관 원문이 있다. `content.prediction`은 항상 unavailable/null이고 실제 예측 모델을 호출하지 않는다. 현재와 과거 snapshot, 최종 확인과 갱신 대기를 구분한다.

## 앱 초기화와 갱신

1. 개발 계정의 사용자 JWT로 `GET /v1/app-config`를 확인한다. 서버 정책과 기능 상태를 따른다.
2. `PUT /v1/me/devices/{installation_id}`로 설치를 등록한다. 푸시 권한이 없어도 token=null로 설치 등록 후 위치를 보낼 수 있다. APNs 직결은 제공하지 않고 FCM 토큰만 받는다.
3. `GET/PUT /v1/me/profile`, `GET/PUT /v1/me/preferences`로 설정한다. 쓰기는 base_revision을 사용한다. 프로필은 전체 스냅샷이며 빠진 값은 unknown/빈 목록이다.
4. `PUT /v1/me/location`으로 fix_id·설치 ID·좌표·정확도·captured_at을 보낸다. 위치 유효기간은 5분이고 역순·미래·만료 관측을 거부한다. 지원 위도는 -85~85도다.
5. `GET /v1/home`, `/v1/disasters`, `/v1/me/alerts`를 조회한다. 원문은 Qwen이나 개인 정책 완료를 기다리지 않는다. 자료가 없거나 관련성이 불명확하면 안전하다고 표시하지 않는다.
6. 사건/경보의 response_id로 `GET /v1/me/responses/{response_id}`를 조회한다. 평가 대기 때 옛 행동·단계를 최신으로 쓰지 않고 `last_known_response`와 구분한다.
7. `GET /v1/me/updates?cursor=...&wait_seconds=25`로 전경 갱신한다. 변경 리소스를 다시 조회하고 같은 리소스의 낮은 revision을 버린다. cursor 만료(410)는 전체 동기화, 사용자 불일치/위조(400)는 cursor 초기화다. cursor를 access_token으로 쓸 수 없다.

`PUT /v1/me/profile`은 선택적인 `Idempotency-Key` 헤더를 지원한다. 위치는 fix_id가 멱등 키다. 같은 키의 다른 본문은 409다. 삭제한 위치를 옛 fix로 되살리지 않는다. DELETE 프로필/위치는 저장값과 관련 멱등 본문을 지우고 재평가를 요청한다.

## 현재 상태와 접근 제한

`PUT /v1/me/responses/{response_id}/context`는 base_revision·observed_at·confirmation=user_confirmed와 `state`를 받는다. state의 후보는 helper_present, can_move, injured, observed_hazard(unknown/none/smoke/flames/fear/trapped), location_type, evacuation_status, deescalation_confirmed다. 유효기간 5분인 현재 관측으로만 적용하고 사전 프로필을 덮어쓰지 않는다.

기존 overrides의 mobility와 alone_now도 받는다. 조력자가 단지 등록돼 있다는 사실을 곁에 있음으로 해석하지 않는다. 클라이언트는 route_status나 H구간을 공식 판단 값으로 등록할 수 없다. 해당 입력은 출처를 확인하는 내부 API 소관이다.

JWT는 고정 HS256, 별도 서명키, issuer/audience/만료/발급·유효 시각/사용자·시나리오·token_version을 검사한다. DB 계정이 비활성이거나 로그아웃한 토큰은 거부한다. 다른 사용자의 response ID와 경보 ID는 404이며 cursor도 사용자/시나리오에 묶인다. 로그인 제공자 연동은 제공하지 않고 이번 사설망 시연 계정은 관리 도구로 발급한다.

## 알림과 수신 확인

`GET /v1/me/deliveries`에서 모의 발신·재시도·실패·만료를 조회한다. 사용자 선택에 따라 현재 발신기는 simulation이다. 푸시 토큰은 응답과 로그에 출력하지 않는다. 토큰 회전·기기 해제 후 이전 기기 revision 작업을 전송하지 않는다. preferences.notifications_enabled=false는 백그라운드 알림만 끄고 전경 갱신은 유지한다.

`POST /v1/me/alerts/{alert_id}/receipts`는 alert_revision, installation_id, event(received/displayed/opened), occurred_at을 받는다. 중복을 저장 규칙으로 합치고 의미는 항상 client_reported_only다. 제공자 수락, 단말 보고, 사람이 열람한 기록, 119 접수는 서로 다르다.

`POST /v1/me/logout`은 사용자 토큰 버전을 바꾸고 모든 설치의 토큰을 지운다. 재로그인은 관리 도구로 새 계정 토큰을 발급받는다.

## 제공 경로와 제외 기능

| 경로 | 동작 |
| --- | --- |
| `/v1/app-config` | 3단계와 실제 기능 상태 |
| `/v1/me/profile`, `/preferences`, `/location` | 자기 자료 조회·수정, 프로필/위치 삭제 |
| `/v1/me/devices/{installation_id}` | 설치 등록·회전·해제 |
| `/v1/home`, `/v1/disasters` | 시나리오 범위의 관련 사건과 기본 지침. 관련 구역을 모르면 unknown |
| `/v1/me/alerts`, `/{alert_id}`, `/{alert_id}/receipts` | 독립 공식 원문·수신 보고 |
| `/v1/me/responses/{response_id}`, `/context`, `/history` | 최신 계획·현재 관측·과거 기록 |
| `/v1/me/updates`, `/v1/me/deliveries`, `/v1/me/logout` | 전경 갱신·전달 상태·로그아웃 |
| `/v1/safety-rules/wildfire` | DB의 검토된 국내 기본 수칙 |
| `/v1/me/responses/{response_id}/route` | 검증된 경로 도형이 없어 unavailable, route=null |
| `/support-drafts` | 서버 대기 없이 단말에서 작성해야 하므로 비활성(503) |
| `/voice-turns`와 하위 조회/삭제 | 서버 음성 제외, 비활성(503) |

서버는 텍스트를 제공한다. 단말 TTS·지도 표시·119 OS 화면은 앱 소관이다. 공식 통제 정보를 검토한 경로 상태와 실제 통행 가능한 경로 도형은 다르며 경로를 만들어 안전하다고 표시하지 않는다. 프로필의 반경·관심 행정구역 설정은 저장하지만 이번 관련성 판정은 입력된 사건/경보 구역을 사용한다. 영어 번역과 행정구역 경계 자료는 미확보이므로 한국어·시연 구역 기준을 표시한다.

## 시연 계정 발급

일반 서버의 비밀 설정이 준비된 뒤 관리자가 실행한다. 출력 파일은 Git 밖에 두고 토큰을 로그에 출력하지 않는다.

```sh
cd /home1/ncloud/bonghwajigi
sudo docker compose --env-file /home1/ncloud/.config/bonghwajigi/general.env \
  -f deploy/compose/mvp.yaml exec -T api python tools/mvp_accounts.py \
  --scenario demo --user user-a --mobility independent --output /accounts/user-a.json
```

사용자 토큰은 기본 24시간 후 만료된다. 계정 파일을 안전하게 앱 개발 환경에 전달하고 내부 토큰·서명키는 전달하지 않는다. 원격 배포 도구의 실제 경로와 사용법은 서버 문서를 따른다.

### required-doc: docs/V2/delivery/mvp-server-runbook.md

- Path: `docs/V2/delivery/mvp-server-runbook.md`
- Status: present

# 산불 MVP 일반 서버 운영과 접속

Loom `task-20261031-132925-mvp-1d561841`. 확정 단계는 **1 경고 → 2 대피 → 3 위급**이다. 일반 서버의 사설망 시연 배포이며 실제 예측 연결·실제 단말 푸시·HTTPS 도메인은 제외한다. 앱 저장소와 진행 중인 학습은 변경하지 않는다. 배포 검증 결과는 [검증 기록](mvp-server-evidence.json)에 기록한다.

## 실제 확인 결과

2026-10-31 KST, 일반 서버에 실행 커밋 `654a9ef`를 배포했다. API/긴급·분석·전달/정책·통합/outbox 7개 상시 프로세스, PostgreSQL/Redis 2개와 완료된 migration 1개를 확인했다. 두 systemd 서비스는 active/enabled다.

- 실제 큐를 거친 합성 사용자 3명의 단계·현재 상태·정정·해제·위치 삭제/복원·모의 전송·자기 자료 접근을 확인했다. GPU 터널을 끊은 상태에서도 같은 검증이 통과했다. 실제 GPU 모델 서비스는 중단하지 않았다.
- 실제 임베딩은 1024차원, 인터넷 검색은 5개 결과, Qwen 통합은 입력 876/출력 257토큰·약 10.36초로 완료됐다. 생성 요약은 미검토 모델 출력이며 실제 경보 판단이나 개인 단계에 사용하지 않았다.
- 일반 서버 전체 서비스 정지/재시작 뒤 해당 시나리오의 계정 3개, 입력 30개, 개인 정책 3개, 전달 기록 17개, 변경 기록 36개, 긴급 작업 3개가 보존됐다. 입력 본문의 해시도 동일했다. migration은 `bde1925b1429`다.
- 개발 컴퓨터 → 사설망 SSH → API에서 readiness 200, 무인증 사용자 조회 401과 OpenAPI `0.2.0-mvp`를 확인했다. 사용자 API는 21개 경로·28개 동작이다. 실제 단말 수신을 검증한 결과는 아니다.
- PostgreSQL 포함 서버 테스트 82개와 Ruff·실행 OpenAPI 구조·기존 초안 계약·migration 일치 검사를 통과했다. 기존 Starlette/httpx 경고 1개가 있다.

## 실행 구성

일반 서버 `inno-server-011`의 `/home1/ncloud/bonghwajigi`에 커밋된 서버 소스를 배포한다. [배포 구성](../../../deploy/compose/mvp.yaml)은 PostgreSQL+pgvector, Redis AOF, API, 긴급·분석·전달 큐 워커, DB outbox, 정책 재평가, Qwen 통합을 각각 실행한다. DB migration 완료 뒤 서비스가 시작된다. 원래 K8s 구성은 보존하고 수집을 실행하지 않는다.

일반 서버에서 학습/추론 라이브러리를 설치하거나 XGBoost를 호출하지 않는다. GPU의 기존 임베딩·Qwen API만 loopback SSH 터널로 연결한다. GPU나 인터넷 검색이 실패해도 공식 경보의 원문·긴급 큐·결정 규칙·앱 갱신은 독립적으로 작동한다. 모델의 설명 생성은 별도 통합 작업이며 단계를 결정하지 않는다.

API는 서버 `127.0.0.1:8000`, DB는 `127.0.0.1:15432`, Redis는 `127.0.0.1:16379`에만 연다. Linux host network용 구성이다. 공개 인터넷 서비스와 실제 HTTPS 인증을 제공하는 배포가 아니다.

## 개발자 접속

기존 SSH 접근 권한이 있는 컴퓨터에서 다음 연결을 유지한다.

```sh
ssh -N -L 127.0.0.1:18080:127.0.0.1:8000 inno-server-011
```

이 컴퓨터의 API 주소는 `http://127.0.0.1:18080`이다. `/health/live`는 프로세스, `/health/ready`는 DB 테이블·Redis 연결을 검사한다. GPU는 readiness 필수 조건에 넣지 않는다. `/docs`, `/openapi.json`에서 현재 계약을 볼 수 있다. 사용자 경로는 사용자 JWT, 내부 경로는 서비스 토큰으로 인증한다. 물리적 휴대폰은 자신의 loopback이 다르므로 개발 컴퓨터/단말의 별도 네트워크 연결이 필요하며 실제 단말 접속은 미검증이다.

## 계정과 시연

서버에서 계정을 발급한다. `--scenario`는 사용할 시연 사건 범위와 같아야 한다. 사용자 JWT는 기본 24시간 유효하며 파일에만 저장한다. 내부 서비스 토큰·JWT 서명키·GPU 토큰은 앱에 전달하지 않는다.

```sh
cd /home1/ncloud/bonghwajigi
sudo docker compose --env-file /home1/ncloud/.config/bonghwajigi/general.env \
  -f deploy/compose/mvp.yaml exec -T api python tools/mvp_accounts.py \
  --scenario demo --user user-a --mobility independent --output /accounts/user-a.json
```

합성 상황 3명(독립 이동·느린 이동·타인 도움 필요)의 통합 시연:

```sh
sudo docker compose --env-file /home1/ncloud/.config/bonghwajigi/general.env \
  -f deploy/compose/mvp.yaml exec -T api python tools/mvp_demo.py
```

기존 GPU가 준비됐고 학습 자원을 사용하는 작업과 충돌하지 않는 때에 `python tools/mvp_analysis_demo.py`를 같은 방식으로 실행하면 임베딩 인덱싱 → 저장 문서·인터넷 검색 → Qwen 통합을 점검한다. 실제 예측 호출은 포함하지 않는다.

각 실행은 새 시나리오를 만들고 `/accounts`에 사용자별 계정 파일과 비밀값 없는 보고서를 권한 600으로 만든다. 기존 파일을 덮어쓰지 않는다. 호스트 위치는 `/home1/ncloud/.config/bonghwajigi/accounts`이며 컨테이너 사용자 UID 10001 소유다. 관리자만 필요한 사용자 파일을 안전하게 전달한다. 파일을 채팅·Git·일반 로그에 복사하지 않는다. 위치/현재 상태 유효기간은 5분이므로 앱에서 최신 위치를 보내야 하며 오래된 시연은 확인 중으로 바뀐다.

시연은 실제 HTTP → DB outbox → Redis → 분리 워커 → 사용자 조회를 사용한다. H2 개인화, 긴급 경보 즉시 원문, 정정·해제, 조력자·통제 경로 변경, 확인 없는 자동 하향 방지, 위치 삭제·복원, 사용자 격리, cursor 갱신, 모의 전송을 확인한다. 합성 발령은 실제 기관 경보가 아니다. [앱 API 사용법](mvp-app-api.md)과 [정책 문서](response-policy.md)를 함께 따른다.

## 지속 실행과 복구

`bonghwajigi-general.service`가 Docker Compose를 부팅 시 시작한다. 컨테이너는 비정상 종료와 Docker 재시작 뒤 다시 실행된다. `bonghwajigi-general-gpu-tunnel.service`는 별도 재접속하고 API 시작을 막지 않는다.

```sh
sudo systemctl status bonghwajigi-general.service bonghwajigi-general-gpu-tunnel.service
sudo systemctl restart bonghwajigi-general.service
sudo docker compose --env-file /home1/ncloud/.config/bonghwajigi/general.env \
  -f deploy/compose/mvp.yaml ps
```

`logs --tail 100 <서비스>`로 확인한다. 비밀 환경을 펼치는 `config` 출력이나 전체 inspect 결과를 공유하지 않는다. readiness 실패 시 DB·Redis 및 migration 상태를 확인한다. GPU 접속 실패 시 터널과 기존 GPU 서비스 상태만 확인하고 진행 중인 학습을 중단하지 않는다. 실패한 분석/통합은 내부 API의 retry 경로로 재시도할 수 있다. 긴급/전달 작업은 DB outbox가 회수한다. 네트워크 중단 시 정확히 한 번 전송을 보장하지 않으므로 앱은 리소스 ID/revision으로 중복을 제거한다.

DB/Redis 데이터는 이름 있는 볼륨에 유지한다. 정상 재시작은 볼륨을 삭제하지 않는다. `down -v`, Docker 전체 정리, DB 초기화는 수행하지 않는다. 운영 백업은 DB dump와 비공개 설정을 따로 암호화 보관해야 하며 이번 시연에는 외부 백업 저장소가 없다. 시연 토큰/개인정보는 필요가 끝나면 관리자 삭제 절차가 필요하다.

## 비공개 설정과 GPU 연결

사용자는 기존 GPU API 토큰을 일반 서버 비공개 설정으로 복사하고 API 포트 전용 SSH 키를 등록하도록 명시적으로 허용했다. `/home1/ncloud/.config/bonghwajigi/general.env`는 권한 600, 디렉터리는 700이다. DB/내부 인증/JWT 서명키는 별도 생성하며 기존 설정이 있으면 재발급하지 않는다. Git에는 값이 없다.

전용 개인키는 일반 서버 `.ssh/bonghwajigi-gpu-api`의 권한 600으로만 보관한다. GPU authorized_keys는 강제 `/bin/false`, PTY/에이전트 제한, `permitopen="127.0.0.1:8001"`로 제한한다. 기존 검증된 GPU 호스트 공개키를 별도 known_hosts에 고정하고 StrictHostKeyChecking을 사용한다. 터널은 일반 서버 `127.0.0.1:18001` → GPU `127.0.0.1:8001`이다. 기존 GPU 서비스/학습 설정은 바꾸지 않는다.

키의 `from`은 일반 서버 주소에 한정한다. GPU의 `/etc/ssh/sshd_config.d/80-bonghwajigi-general-api.conf`에 [전용 제한](../../../deploy/ssh/gpu-api-only.conf)을 적용해 일반 서버에서 오는 연결만 로컬 API 포워딩을 허용하고 원격·Unix socket 포워딩을 막았다. SSH 구문 검사 후 reload했으며 기존 연결은 유지됐다. API 외 포트, 원격 포워딩, 임의 원격 명령이 거부되는 것을 실제 검사했다. 다른 출발지의 개발자/학습 SSH 설정은 바꾸지 않았다.

## 남은 외부 연결 조건

- Firebase 프로젝트·서버 자격 파일·테스트 FCM 토큰이 없어 발신기는 simulation이다. `simulated`는 실제 발신/단말 수신이 아니다. 제공자 어댑터·재시도·만료·토큰 회전 검사는 구현했다.
- 실제 예측 연결은 사용자 지시로 제외했다. 모든 앱 예측은 unavailable/null이다.
- 도메인/HTTPS, 외부 로그인, 실제 모바일 기기, 실측 경계/도로 경로, 실제 K8s 수집은 검증하지 않았다. 기본 관련성은 공급된 시연 구역과 최신 GPS/정확도를 사용한다.
- 서버 음성과 3D는 제외한다. 119 신고를 자동으로 보내지 않는다. 단말의 TTS·지도 표시·전화/문자 화면 연결은 앱 소관이다.

## Verified Team Policies

No verified Team Policy Snapshot is active.

## Active Workflow Memory

No active workflow memory recorded.
