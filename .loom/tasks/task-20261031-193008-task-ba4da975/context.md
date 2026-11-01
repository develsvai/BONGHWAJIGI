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

- Title: V2 실행 기반과 통합 검증
- Goal: 산불 한 종류의 오늘 MVP 범위와 실행 기반을 고정하고 공식 경보 우선 전달·사용자별 텍스트 안내·변경 및 해제를 시간순 재생으로 통합 검증한다. 3D와 서버 음성을 제외하고 실제 성능과 모의 시연을 구분한다. 이 갱신은 사용자 지시에 따른 계약 재고정이며 구현 실행·Queue 등록은 포함하지 않는다. 기존 완료 이력과 Task ID를 보존한다.
- Branch: HeoNey
- Task count: `28`

## Task

- Title: 촬영 시나리오 자료 수집과 지역 행동요령·개인 준비 실파이프라인 검증
- Description: 사용자가 제공한 118초 A·B 산불 영상 계획을 바탕으로 출처 있는 재난·기상·지리 자료를 수집하고 실제 이벤트·큐·검색·통합·정책·알림 흐름을 검증하라고 직접 지시했다. 홈 오늘의 행동요령은 위치 지역 환경, 사전 준비는 공통 1칸과 프로필 맞춤 1칸을 제공한다. 시연 문구는 앱에서 정리하되 데이터 출처·원시 관측시각·재생 여부와 경로 검증 범위는 보존한다.
- Expected output: 출처와 재생 명세가 있는 A·B 데이터, 지역 홈 카드 API와 상태 질문/정책 연결, 반복 실행 도구, 일반 서버 배포와 실제 큐·모델·알림 검증 증거 및 앱 계약
- Done condition: 검증 가능한 자료로 같은 산불의 서로 다른 사용자 안내를 재현하고 프로필만으로 현재 동반·이동불가를 추정하지 않는다. 위치/기상 및 공통/개인 준비 카드가 근거와 만료에 맞춰 갱신되고 실제 파이프라인 결과·미제공 범위를 기록한다.
- In scope: 공식 산불·기상·지리 근거 수집; A/B 재생 데이터; 지역 행동요령·준비 API; 사건/상태 질문·정책; 일반 서버 배포와 큐/모델/알림 검사; 앱 계약·자료 출처 기록
- Out of scope: 실제 예측 모델 연결·학습 변경; Firebase 실제 푸시; 3D; 실제 GPS 공유; 실제119연락; 미검증 안전 경로 보장; 다른 채팅 연구 변경
- Validation hint: 출처·원시시간·재생 변환 검토, 실제 PostgreSQL 회귀 및 API 명세, 임베딩/Qwen 통합·공식 긴급큐/분석큐·개인 정책/앱알림 실서버 검증, Loom strict
- Required docs: `docs/V2/delivery/mvp-app-api.md`, `docs/V2/delivery/mvp-server-runbook.md`, `docs/V2/delivery/mobile-dialogue-and-route.md`
- Memory refs: -
- Document outputs: `docs/V2/delivery/filming-scenario-pipeline.md`
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

## 2026-10-31T00:24:09+00:00

사용자 지시 기준: V2를 설계 정본으로 삼고 HeoNey는 참고한다. 앱 구현은 앱팀 소관이며 우리 산출물은 서버와 앱 연동 API 명세이다. 이번 턴은 서버와 클러스터의 읽기 전용 점검 및 TODO의 Job Task 등록만 실행한다. 신규 구현 Task는 PENDING으로 두며 Queue Worker와 배포 학습을 시작하지 않는다. 사용자가 Job Task 분할을 직접 위임했으므로 통제 에이전트가 계약을 생성한다.

- Task: `task-20261031-002027-k8s-v2-a251b54e`
- Tags: `scope`, `user-direction`
## 2026-10-31T00:26:25+00:00

설계 기준은 docs/V2이며 HeoNey는 참고다. 앱 구현은 제외하고 앱팀에 API 명세를 제공한다. 이 등록은 작업 계약 고정이며 후속 구현 Task를 지금 실행하거나 Queue에 넣지 않는다. 기준 원문은 docs/V2/01, 02, 03 문서이고 실행 작업표는 docs/V2/04-execution-backlog.md이다. 등록 시 의존관계는 Job 경계를 넘어 적용한다.
- Tags: `v2`, `scope`, `backlog`
## 2026-10-31T00:42:26+00:00

사용자 질문 응답: 첨부 이미지의 계정 및 비밀번호를 GPU 서버와 일반 서버의 SSH 로그인에 사용하도록 두 서버 로그인 승인이라고 명시적으로 답했다. 상태 조회에만 사용하며 인증정보는 저장소나 보고서에 남기지 않는다. 기존 검토 대기 Task의 서버 조회를 재개한다.

- Task: `task-20261031-002027-k8s-v2-a251b54e`
- Tags: `user-approval`, `resume`
## 2026-10-31T00:50:01+00:00

승인 후 실제 서버 조회 완료: GPU 서버는 4 vCPU RAM 47.05 GiB 및 NVIDIA L4 1대, 드라이버 580.159.04, cuInit 성공이다. 일반 서버는 2 vCPU RAM 7.76 GiB, systemd running 및 실패 서비스 없음이다. 두 서버 사이 TCP 22는 양방향 접근 가능하다. GPU 서버는 부팅 시 Mellanox 설정 파일 누락과 NVSwitch 조회 실패 기록으로 systemd degraded이며 A2에서 실제 필요성과 조치 여부를 확인한다. K8s발 서버 API 통신과 실제 모델 성능은 별도 검증 대상이다.

- Task: `task-20261031-002627-task-5ce3742e`
- Tags: `infrastructure`, `verified`
## 2026-10-31T01:20:51+00:00

사용자가 현재 대화에서 검증 작업 전부 실행을 지시했다. 선행 완료된 A2 환경 검증을 지금 수행하고, 학습 모델과 구현 및 API가 필요한 C4 D3 E2 A4 검증은 선행 산출물 존재 여부와 실행 경계를 확인한다. 이 지시는 검증 작업 실행이며 미구현 기능 전체의 개발 지시로 확대하지 않는다.

- Task: `task-20261031-002627-task-5ce3742e`
- Tags: `user-request`, `validation`
## 2026-10-31T01:22:32+00:00

사용자가 검증을 계속하기 전에 develop과 HeoNey를 동기화하고 develop에서 실행하도록 지시했다. 원격 최신 상태 조회 결과 develop은 HeoNey의 조상이며 충돌 없는 fast-forward가 가능하다. 진행 중 A2 기록을 보존하고 실행 브랜치 정책을 develop으로 변경한 뒤 검증을 이어간다.

- Task: `task-20261031-002627-task-5ce3742e`
- Tags: `user-direction`, `branch`
## 2026-10-31T01:28:14+00:00

사용자 추가 설명: 클러스터와 제공 서버는 서로 아예 다른 VPN이므로 현재 직접 통신이 안 되는 것이 맞다. 6개 노드와 5개 워커 파드의 제공 서버 TCP 22 시험은 모두 시간 초과, 노드 경로는 일반 게이트웨이이며 제공 서버 대역 전용 경로는 확인되지 않았다. 장애로 단정하지 않고 A3 실행 기반 구성에서 명시적 연결 방식을 정해야 하는 설계 조건으로 기록한다. VPN/라우팅/방화벽 설정은 이번 검증에서 변경하지 않는다.

- Task: `task-20261031-002627-task-5ce3742e`
- Tags: `user-context`, `network-validation`
## 2026-10-31T01:30:16+00:00

검증 전부 실행 지시를 확인했다. 계약 형식 검증은 통과했지만 실제 검증에 필요한 선행 작업 B5, C5, D5, E2의 산출물이 아직 없어 기능 검증은 실행할 수 없다. 모델 또는 API가 완성된 것으로 간주하지 않고 PENDING 유지하며 선행 구현 완료 후 이 Task를 실행한다. 현황은 A2 환경 검증 보고서에 함께 정리한다.

- Task: `task-20261031-002631-task-df03e0e8`
- Tags: `validation`, `prerequisites`
## 2026-10-31T01:35:11+00:00

A2 결과: 클러스터와 제공 서버는 별도 VPN이며 6개 노드 및 5개 워커 파드에서 제공 서버 TCP 22 연결 실패가 실측됐다. A3에서는 허용된 전송 경로와 서비스 주소/포트/인증/TLS를 먼저 정하고 실제 수집 API까지 검증해야 한다. 단일 파드 요청 2 CPU는 현재 어느 워커에도 들어가지 않고 합산 요청 여유는 약 5.19 CPU다. DNS resolver의 4개 nameserver 정리와 GPU 보조 서비스 상태 관리도 검토한다. 일반 서버는 A0 로그인 성공 이후 이번 재인증을 못 했으므로 설치 전에 정확한 자격 증명 재확인이 필요하다. 보고서 docs/V2/delivery/environment-readiness.md 참조.

- Task: `task-20261031-002627-k8s-4bf877bd`
- Tags: `verification-result`, `readiness`
## 2026-10-31T02:38:53+00:00

A5에서 두 서버 Tailscale 1.104.4 설치와 기존 tailnet 등록 완료. 사용자 저장 직전 승인 후 관리자 그룹·마스터·두 서버에서 두 서버 IPv4 TCP 22만 허용하는 grant 1개를 추가했다. Tailnet SSH 실제 로그인, 마스터발 TCP 22 및 서버 상호 배너 수신이 성공했다. 일반 서버 재인증 문제는 해결됐다. 일반 워커와 파드는 경로가 없어 연결 실패하므로 A3에서 프로젝트 전용 egress와 실제 API 포트·인증·TLS를 구성하고 다시 검증한다. 비밀정보는 기록하지 않았다.

- Task: `task-20261031-022438-tailscale-6dc57118`
- Tags: `tailscale`, `verified`, `follow-up`
## 2026-10-31T08:01:46+00:00

# 2026-10-31-wildfire-mvp 작업 계약 재고정

사용자 지시: “오케 우선은 그거대로 loom에 타스크를 재고정 해”.

2026-10-31 KST 사용자 재고정: 오늘 MVP는 산불 한 종류이며 3D와 서버 STT/TTS·오디오 스트리밍을 제외하고 서버는 텍스트를 제공한다. 공식 경보는 출처·원문·발령 대상을 확인해 개인별 정책 계산과 GPU를 기다리지 않고 우선 전달한다. 일반 분석은 정형 파싱 또는 필요한 Qwen 문서 추출·저장 문서의 임베딩 검색, 사건 통합·위치 관련성·입력 검사, 영향 확률 또는 예측 불가, 검토된 개인별 정책 순서다. 공식 등급·환경 영향 확률·개인 대응 단계를 분리하고 정책은 검토·버전 관리하며 입력 변경 때 재적용한다. 실제 자료·과거 재생·합성 시나리오를 구분하고 실제 정답이 없으면 학습·추론 연결은 simulation으로 검증하며 실제 예측은 unavailable로 둔다. 이 지시는 작업 계약 재고정만 승인하며 구현 실행·Queue 등록·서버 설치·원격 push를 지금 승인한 것으로 취급하지 않는다. 오늘 범위는 이 계약과 Job 재고정 노트를 우선하고 기존 V2 문서는 배경 설계로 참조한다.

이 갱신은 재고정만 수행하며 Task 실행 또는 Queue 등록을 시작하지 않는다.

미정: 시연 지역·사례, 모델의 실제 정답 출처·격자·예측 기간, 개인 대응 단계 매핑, 2D 실제 경로 계산 채택 여부. 60분은 예시이며 실제 확정값이 아니다. 실제 정답 부족은 C4에서 실제 예측 보류로 판정한다.

착수 순서: A1 → B1 → B2 및 C1 → A3·D1·D6 → 수집/긴급 전달·개인 정책·모델 준비 → 안내 갱신 → E2·A4 통합 검증. 공식 원문 전달 D4는 개인 정책 D1/D2와 모델 준비를 선행 조건으로 삼지 않는다.

- A1 `task-20261031-002627-mvp-e821b0f7`: 산불 MVP의 지역·재생 사례·실제 및 모의 범위와 수용 기준 고정. 선행: A0. 현재 PENDING.
- A3 `task-20261031-002627-k8s-4bf877bd`: 산불 MVP의 수집·DB·긴급 및 분석 큐·모델 API 실행 기반 구성. 선행: A1, A2, A5, B2. 현재 PENDING.
- A4 `task-20261031-002631-task-df03e0e8`: 산불 사례 재생으로 공식 경보 우선·개인별 안내·갱신 및 장애 통합 시연 검증. 선행: B5, C5, D5, E2. 현재 PENDING.

구체적 완료 조건은 각 Task의 재고정 계약을 따른다. 기존 docs/V2/04-execution-backlog.md는 이전 계획이며 실제 계약 정본은 현재 Task와 이 노트다.
- Tags: `mvp`, `산불`, `2026-10-31`, `계약재고정`
## 2026-10-31T08:33:37+00:00

2026-10-31 구현 기술 스택 결정: docs/V2/delivery/implementation-stack.md; Task task-20261031-082929-mvp-3188b68a. Python 3.12 + FastAPI/Pydantic 2 + SQLAlchemy 2.x/psycopg 3/Alembic + PostgreSQL 16/PostGIS/pgvector + Celery/Redis + Transformers/Sentence Transformers + XGBoost. 일반 서버 API/정책/CPU 추론, GPU 서버 모델/별도 학습, K8s 수집으로 배치한다. A3는 기술 스택 결정 Task를 선행으로 받고 구현 문서를 필수 입력으로 참조한다. 실제 파드→일반 서버→GPU API와 DB·큐 복구를 검증한다. 이번 실행은 스택 문서와 계약 연결만 수행하며 다른 구현 Task·Queue·서버 설치는 시작하지 않는다.
- Tags: `기술스택`, `산불`, `MVP`
## 2026-10-31T08:44:47+00:00

사용자 직접 요청으로 로컬 ~/.ssh/config에 inno-gpu-011 및 inno-server-011 별칭을 추가하고 기존 항목을 보존했다. 두 Tailnet 주소의 호스트 키를 기존 기록과 대조하고 ncloud 실제 로그인을 재검증했다. GPU L4·47.05 GiB, 일반 서버 7.76 GiB가 기존 환경과 일치한다. 비밀번호는 저장하지 않았고 원격 인증·설치·배포는 변경하지 않았다. 이후 접속 절차와 결과는 docs/V2/delivery/ssh-access.md를 따른다.

- Task: `task-20261031-084138-ssh-b8d79a00`
- Tags: `ssh`, `서버접속`, `검증`
## 2026-10-31T08:57:38+00:00

사용자 추가 지시: K8s 구성은 보존하되 MVP에서는 실제 K8s 수집을 실행하지 않는다. 수동 확보한 특정 재난 자료·뉴스를 시나리오로 재생하고 이벤트 수신 API에서 DB/outbox와 긴급·분석 큐에 연결한다. 실제 파드 수집·egress는 MVP 시연의 선행 조건에서 제외한다. 스캐폴딩에 이 입력 경로를 반영한다. 이어서 사용자가 GPU 서버의 두 Qwen 모델과 XGBoost를 바로 사용할 수 있도록 설정을 직접 지시했으므로 스캐폴딩 완료 후 별도 Task로 설치와 실제 검증을 수행한다.

- Task: `task-20261031-084830-python-03ca0991`
- Tags: `사용자지시`, `MVP`, `시나리오`, `GPU후속`
## 2026-10-31T09:14:34+00:00

사용자 직접 지시에 따른 GPU 준비 완료: /home1/ncloud/bonghwajigi에서 두 Qwen 고정 revision의 실제 생성·1024차원 임베딩 API를 localhost 사용자 서비스로 실행한다. XGBoost 별도 환경의 합성 CUDA 학습·저장·CPU 재로딩 통과. 서빙과 학습은 GPU 잠금으로 분리했다. 운영 경로·사용법·한계는 docs/V2/delivery/gpu-model-readiness.md와 evidence JSON 참조. 산불 실모델·정책 품질·일반 서버 연결을 완료 처리하지 않는다. K8s 실제 수집은 MVP에서 제외하고 시나리오 입력 구조를 유지한다.

- Task: `task-20261031-085956-gpu-qwen-xgboost-9eea12a5`
- Tags: `GPU`, `모델준비`, `실제검증`, `시나리오`
## 2026-10-31T10:05:53+00:00

사용자 추가 검색 선택: 인터넷 검색도 함께 연결. 저장된 문서·뉴스·지침만 검색하는 범위를 넘어 인터넷 뉴스 검색을 분석 워커에 연결한다. 기본 구현은 API 키 없이 접근 가능한 Google News RSS의 제목·짧은 설명·출처·발표시각을 확보하고 임베딩 검색에 결합한다. 기사 본문 수집이나 Qwen 생성은 수행하지 않는다. 웹 자료는 미확인 상태와 검색 시각을 보존하고 정책 승인으로 간주하지 않는다.

- Task: `task-20261031-095141-qwen-9e2979ea`
- Tags: `사용자선택`, `인터넷검색`, `분석흐름`
## 2026-10-31T15:19:20+00:00

사전 보유 코드 없음이라는 사용자 답변을 코드에 한정해 보완했다. 기존 라이선스 명세와 설치·데이터 권리 증빙을 보존하고 공식 wheel36개, 자체 API52+4개, 원본URL54개를 병합했다. 패키지174개·직접 의존성·API·표·링크·인증정보·기존 세 절 보존 검사를 통과했다. 앱과 진행 중인 학습은 변경하지 않는다.

- Task: `task-20261031-151017-api-ae9488f7`
- Tags: `문서`, `라이선스`, `검증`
## 2026-10-31T15:19:58+00:00

외부 자원 명세 후속 병합 완료: 사전보유 코드만 해당없음으로 정정. 고정 wheel36, API52+4, URL54 추가; 기존 설치154/lock-only20 및 자료별 권리조건 보존. 검증 통과. 앱 구현·실제 연동·APK는 사용자의 새 직접 지시로 별도 계약에서 이어간다.

- Task: `task-20261031-151017-api-ae9488f7`
- Tags: `문서`, `검증`, `후속`
## 2026-10-31T15:26:14+00:00

사용자가 비교 경로가 동일함을 확인한 후 그냥 놔두라고 요청하여 통합·삭제를 취소했다. 기존 명세와 근거 파일의 수정·삭제는 수행하지 않았다.

- Task: `task-20261031-152411-task-f8241639`
- Tags: `사용자취소`, `문서유지`

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

### required-doc: docs/V2/delivery/mobile-dialogue-and-route.md

- Path: `docs/V2/delivery/mobile-dialogue-and-route.md`
- Status: present

# 앱 텍스트 대화와 합성 시연 경로

2026-11-01 KST. Loom `task-20261031-183001-api-e700828b`. 기존0.2.0-mvp 계약에 대화와 합성 경로를 추가한다. 단말이 음성을 텍스트로 변환하며 서버는 텍스트만 받는다. Qwen은 현재 검토된 정책의 행동을 선택하고 사용자가 말한 상태를 제안한다. 확인 전에는 프로필·위치·현재 상태·정책을 변경하지 않는다.

## 대화 계약

`POST /v1/me/responses/{response_id}/text-turns`는 다음 입력을 받는다.

```json
{
  "client_turn_id": "device-generated-unique-id",
  "text": "지금 계단 이용이 어려워요",
  "base_response_revision": 2,
  "base_context_revision": 0
}
```

응답의 `data`는 `TextTurnData`다. `turn_id`는 요청의 `client_turn_id`와 같으며 `response_id`, `response_revision`, `context_revision`, `valid_until`을 포함한다. `status`는 `processing` 또는 `complete`다. 완료 응답의 `assistant`는 `text`, `source`(`qwen_grounded` 또는 `reviewed_policy_fallback`), `action_ids`를 담는다. 상태를 추출했다면 `proposal`에 `requires_confirmation=true`, `base_revision`, 전체 `state`·`overrides`, 변경 필드별 `evidence`(`field`, `value`, 사용자 원문의 `quote`)를 담는다. 제안이 없으면 null이다.

앱은 사용자에게 제안을 보여 주고 확인받은 다음 기존 `PUT /v1/me/responses/{response_id}/context`로 `confirmation=user_confirmed`, 현재 `observed_at`, 제안의 `base_revision`·`state`·`overrides`, `proposal_turn_id=turn_id`를 보낸다. 서버가 동일 세션·유효기간·정책/context revision과 제안 내용 일치를 재확인한다. 직접 상태를 선택하는 기존 화면은 `proposal_turn_id` 없이 계속 사용할 수 있다. 정규화된 이전 이동 상태를 보존하도록 overrides.mobility에 `needs_time`·`requires_help`도 허용한다. 모델은 단계 하향 확인을 생성하지 않는다.

GPU 요청은 연결·쓰기3초, 읽기22초 제한을 사용한다. 정상 POST는 동기200이며 생성 실패·잘못된 JSON·존재하지 않는 행동ID·사용자 발언에 없는 근거가 나오면 검토된 정책 텍스트로 fallback한다. 모델의 자유 생성 문장을 새 대피 지시로 내보내지 않는다. 최종 텍스트는 승인된 행동과 정해진 확인 질문으로 구성한다. 호칭·연락처·의료 자유메모·생활 장소를 프롬프트에 넣지 않는다.

POST 응답을 놓치면 `GET /v1/me/responses/{response_id}/text-turns/{client_turn_id}`로 조회한다. 진행 중에는 `processing`, 완료되면 `complete`다. 생성 중 DB 트랜잭션·시나리오 잠금을 유지하지 않는다. 종료 직전에 세션과 정책 입력을 다시 확인하므로 중간 로그아웃·입력 변경의 결과를 게시하지 않는다.

| 상태/오류 | 앱 처리 |
| --- | --- |
| 같은 ID·같은 본문 | 여전히 유효한 완료 결과를 재사용; 모델 재호출 없음 |
| 409 `TURN_IN_PROGRESS` | 같은 turn ID로 GET 조회 |
| 409 `CONVERSATION_BUSY` | 다른 진행 turn 종료 후 새 요청 |
| 409 `REVISION_CONFLICT`, `RESPONSE_REFRESH_REQUIRED`, `TURN_SUPERSEDED` | 현재 응답·상태를 다시 조회하고 오래된 제안 폐기 |
| 409 `IDEMPOTENCY_CONFLICT`, `PROPOSAL_MISMATCH` | 같은 ID의 다른 본문 또는 변조된 제안 거부 |
| 410 `TURN_EXPIRED` | 오래된 turn·제안 폐기 후 새 입력 |
| 429 `TURN_RATE_LIMIT` | 사용자당10분20턴 상한; 새 요청을 잠시 중단 |
| 401 / 404 | 세션 갱신 또는 해당 사용자 자료 접근 거부 |

제안 유효기간은 정책 유효기한과2분 중 짧은 값이다. 이전 대화는 동일 사용자·세션·응답·revision의 최근3턴만, 각 발언/답변300자까지 참조한다. 저장은 사용자당10분 내20턴으로 제한하며 만료한 저장 행은 다음 대화 요청에서 정리한다. 만료 즉시 백그라운드 물리 삭제하는 보관 정책은 아니다. 원문·모델 출력·토큰을 서버 로그에 남기지 않는다.

## 합성 경로 계약

기존 `GET /v1/me/responses/{response_id}/route`의 `RouteData`는 `status`, `route`, `reason`을 제공한다. `settings.mode=simulation`, `mobile-demo/mobile-fire`, 사건 출처 `synthetic`, 사건·위치가 현재 유효하고 위치 정확도100m 이하·시연 시작점(36.4,129.35)에서200m 이내일 때만 `status=simulation`으로 시연 선을 반환한다. 다른 위치·만료·실제 자료·live 설정에서는 `unavailable`과 null을 유지한다.

`route`에는 `origin=synthetic`, `operational_use=false`, 표시용 `label`, `geometry`(GeoJSON LineString, 각 좌표는 `[경도, 위도]`), `start`·`destination`(name/latitude/longitude), `steps`(sequence/text/point), `bounds`, `valid_until`, `input_versions`가 있다. `valid_until`은 사건과 위치 만료 중 짧은 값이다. 좌표는 서버의 [시연 fixture](../../../src/bonghwajigi/policy/mobile_route.json)에서 제공한다. 앱이 임의의 선을 만들거나 Qwen이 경로를 생성하지 않는다.

이 선과 목적지는 실측 도로·통행 가능성·지정 대피소를 검증한 결과가 아니다. 앱은 시연 표시를 유지하고 실제 안전 경로나 이동 명령으로 표현하지 않는다. `route_geometry=false`는 실제 검증 경로를 제공하지 않는 기존 의미를 유지하며 별도 `simulation_route` 기능값을 추가했다. `voice_turns=false`, `server_audio=false`도 유지하고 `text_turns=true`를 추가했다.

## 검증과 배포

마이그레이션 `7c8e910ba402`는 대화 행과 사용자/시각 인덱스만 추가한다. 기존 DB 자료·GPU 모델·학습·위치 유효성 계약은 유지한다. readiness는 새 대화 테이블 존재도 확인한다.

로컬 PostgreSQL에서 마이그레이션과 Alembic check, 전체121개 서버 테스트를 통과했다. 사용자·실제 세션 간 격리, 세션 취소, revision, 멱등, 생성 중 동시 요청·입력 변경·로그아웃, 제안 비변경/사용자 확인, 내용 변조·만료, 잘못된 모델 출력·timeout fallback, 상태 보존, 대화 상한, 시연 경로 범위를 검증했다. 기존 Starlette/httpx 경고1개가 있다.

기존 일반 서버→GPU 연결로 합성 계단 어려움 발언을 시험하여 Qwen이2.66초에 `overrides.stairs=difficult`와 정확한 원문 근거를 반환했고 모델·revision이 일치했다. 이 사전 추론 확인은 새 API 배포 검증과 구분한다.

[OpenAPI](api/mvp-openapi.json), [합성 UI fixture](api/mvp-interaction-fixtures.json)를 앱 타입·모의 화면에 인계했다. UI fixture는 로컬 격리 API와 서버 경로 생성 함수에서 캡처했으며 모델의 상태 추출만 고정 테스트 응답이다. 실제 계정·토큰·개인 위치는 포함하지 않는다.

### 최종 일반 서버 검증

실행 소스 `414482274f9252056ac350c69d4687e7a1429d8b`, 이미지 `bonghwajigi-mvp:4144822`, migration `7c8e910ba402`를 배포했다. 기존 설정과 PostgreSQL dump는 `/home1/ncloud/.config/bonghwajigi/backups/mobile-4144822`에 보관했으며 설정·dump 권한은600이다. 다른 시나리오 계정9개·입력87개의 전후 개수와 DB/Redis 볼륨을 보존했다. GPU 서버·모델·학습 설정은 변경하지 않았다. API 및6개 worker와 PostgreSQL/Redis가 healthy이고 Alembic check는 추가 변경 없음이다. 배포된 dialogue.py SHA256은 로컬 실행 소스와 일치한다.

2026-11-01 03:53 KST, `https://inno-server-011.tail2dac17.ts.net`에서 TLS 인증서 검증을 유지하고 신규 합성 설치계정으로 전체 흐름을 확인했다. [익명 검증 근거](api/mobile-interaction-live-evidence.json)에 상태·revision·시간만 보존했으며 계정ID·토큰은 포함하지 않는다.

| 실제 요청 | 모델 결과와 적용 | API 검증 |
| --- | --- | --- |
| 계단 이용이 어려움 | Qwen2.15초, `overrides.stairs=difficult`; 확인 후 context0→1, 경고→대피 | 확인 전 context불변, 동일turn 재전송·GET 결과동일 |
| 갇혀 이동할 수 없음 | Qwen3.19초, `state.can_move=false` 포함; 확인 후 context1→2, 대피→위급 | 확인 후 이전turn409, 정책 revision2→3→4 |
| 시연 좌표36.4,129.35/정확도10m | 합성 LineString·목적지·3단계 표시자료 반환 | `origin=synthetic`, `operational_use=false`; 시연 시작점 밖 위치는 unavailable |

설치 등록→기기→프로필→위치→정책→텍스트turn→사용자 확인→정책 갱신→로그아웃을 검증했다. 배포 OpenAPI JSON 전체가 저장소 원본과 같으며 파일 SHA256은 `e9075d620d9d916d512328b380e35c9073f9e681fd8236a86cc083787a735671`이다. 첫 실모델 시험에서 선택적 question 키 생략을 발견해 none 기본값으로 보완했으며 상태·원문 근거·정책ID 검증은 유지했다. 휴대폰의 음성 인식·화면·APK 검증은 앱 작업에서 별도로 수행한다.

## Verified Team Policies

No verified Team Policy Snapshot is active.

## Active Workflow Memory

No active workflow memory recorded.
