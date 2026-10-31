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
- Task count: `26`

## Task

- Title: 정책 근거 대화·사용자 확인 상태 제안과 합성 시연 경로 API 구현 및 배포
- Description: 사용자의 음성·텍스트 대화와 지도 경로 후속 요청에 필요한 서버 API를 구현한다. 텍스트 turn을 기존 정책과 Qwen에 연결하고 상태 제안은 사용자 확인 전 적용하지 않는다. mobile-fire 합성 경로를 서버 fixture로 제공하며 실제 안전 경로로 주장하지 않는다. 앱 구현과 최종 gitlink는 앱 담당자가 별도로 수행한다.
- Expected output: 대화 turn·상태 제안 응답 계약과 서버 구현; simulation 전용 route fixture/API; OpenAPI·회귀검증·일반서버 배포·운영문서
- Done condition: 인증·응답 소유권·revision·idempotency·만료·동시성 보호를 검증하고 Qwen 오류 시 정책 사실 기반으로 안전하게 처리한다. 제안은 자동DB반영되지 않으며 확정은 기존context API를 쓴다. mobile-demo 경로는 합성 표시되고 운영 route unavailable은 유지된다. 실서버 배포 검증과 normalpush가 완료된다.
- In scope: 서버 텍스트 대화와 검토 가능한 상태제안; 기존 사용자확인 context 적용; synthetic route fixture·API; 보안/회귀테스트; OpenAPI·문서·일반서버 배포·해당Loom기록
- Out of scope: 앱코드·앱gitlink변경; 실제GPS수집; 음성파일/STT/TTS서버; 실제검증안전경로·외부길찾기계약; 모델학습·GPU설정변경; 타채팅변경커밋; 비밀출력; 실제긴급연락
- Validation hint: PostgreSQL 기반 ownership/revision/expiry/idempotency/concurrency/context미변경 테스트; Qwen invalid/failure 제약; synthetic route 범위·운영 unavailable; OpenAPI; 일반서버 실모델 대화 검증; Ruff·pytest·Loomstrict
- Required docs: `docs/V2/delivery/app-integration-api.md`, `docs/V2/delivery/mobile-server-deployment.md`
- Memory refs: -
- Document outputs: `docs/V2/delivery/mobile-dialogue-and-route.md`
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

### required-doc: docs/V2/delivery/app-integration-api.md

- Path: `docs/V2/delivery/app-integration-api.md`
- Status: present

# 앱 통합 API 보완

2026-11-01 KST. 앱 목업 실연결 요청에 따른 후속 구현이다. 기존0.2.0-mvp와3단계를 유지하고 필요한 필드·세션 경로를 추가했다. 실제 예측·3D·도로 경로 생성·서버 STT/TTS·실제 FCM 발신은 제외한다.

## 설치 계정과 인증

- GET /v1/auth/config: 공개된 내부 시연 등록 가능 여부·동의 버전·안내.
- POST /v1/auth/installations: installation_id와 consent(version=internal-demo-v1, service/privacy/location=true)를 받아 시연용 새 익명 설치 계정과 세션을 발급한다. 기존 사용자 ID를 입력해 다른 계정을 가져올 수 없다.
- POST /v1/auth/refresh: refresh_token으로 access와 refresh를 함께 회전한다. 소비된 refresh를 다시 사용하면 해당 세션을 폐기한다. 만료·로그아웃·폐기 후에는 access와 refresh 모두 거부한다.
- POST /v1/me/logout: 기존 사용자 token_version을 올려 사용자의 이전 access와 refresh를 모두 무효화하고 단말 토큰을 해제한다.

등록은 BONGHWA_APP_REGISTRATION_ENABLED=true인 simulation에서만 열리며 기본은 off다. 운영 회원가입·외부 로그인 제공자가 아니다. BONGHWA_APP_REGISTRATION_SCENARIO의 기본은 mobile-demo이고 같은 시연 사건 범위에 새로운 고유 사용자를 만든다. IP 원문 대신 서버 키로 HMAC한 값으로 시간당 등록 상한(기본20개)을 적용한다. 프록시 X-Forwarded-For를 임의 신뢰하지 않는다.

access는 최대15분, refresh의 기본 절대 유효기간은7일이다. DB에는 refresh 비밀 부분의 SHA256만 보관한다. 앱은 SecureStore에 저장하며 서버 서비스 토큰·JWT 서명키를 받지 않는다. 설치 ID만으로 기존 세션이나 개인정보를 복원하지 않는다. 앱 재설치/자격 삭제 시 새 시연 계정을 만들 수 있다. 민감 데이터가 있는 계정의 복구·공개 서비스 가입·운영 보관기간은 이번 내부 시연 계정의 기능이 아니다.

## 프로필과 준비 지침

AppProfile에 display_name, age_band, emergency_contact, usual_place, building_floor, health_consent, health_notes를 추가했다. 기존 mobility/stairs/communication_preference/sensory_supports/dependents/helper_registered/vehicle_access를 유지한다. 선택 의료 메모는 동의가 있을 때만 저장하며 동의를 끄면 빈 메모를 보내야 한다. 동의 없이 값이 있으면422다. 입력 오류에는 요청 원문·토큰·메모를 되돌려주지 않는다. 철회와 프로필 삭제는 이전 프로필 멱등 응답에 보관된 메모도 지운다.

의료 메모·호칭·연락처·생활 장소를 Qwen이나 단계 결정에 자동 전달하지 않는다. 정책은 기존 정규화한 이동·보호 대상·확인 상태와 공식 근거로 결정한다. 계단 이용 어려움의 현재 상태 입력도 needs_time으로 정규화하도록 바로잡았다.

GET /v1/me/preparations는 별도의 준비 카드 계약이다. 승인된 DB 지침에서 기본 가방 카드와 이동 도움/보호 대상/물품 점검 중 하나를 선택해 최대2개, 출처·지침revision·profile_revision·유효시간·이유를 돌려준다. 긴급 actions를 앱이 임의로 준비 카드로 바꾸지 않는다. 기본 수칙은 별도의 avoid 항목에 승인된 회피 지침을 제공한다.

## 응답과 갱신

현재 명세: [실행 OpenAPI](api/mvp-openapi.json). 직접 수정하지 않은 앱 생성 타입은 이 명세 사본에서 생성한다. 새로운 등록/세션 및 홈·프로필·위치·공식경보·개인응답·준비/수칙의 출력 모델을 명시했다.

- Home: nearby_disasters, basic_rules, location, features, preparations, alerts.
- Profile/Location의 revision은 앱 문서 수정 버전이고 input_revision은 정책 입력 버전이다. 앱은 이 값을 정책 input_versions와 대조한다.
- Response: id, scenario_id, revision, evaluated_at, pending_update, error_code, content, user_context.
- content.personal_response는 서버의 level/number/label이고 content.actions는 서버의 승인된 행동이다. content.prediction은unavailable/null이다.
- user_context는 현재 상태의 revision·available/stale/unavailable·원자료다. 이를 AI 문서통합용 content.context와 혼동하지 않는다.
- content.assistant_utterance는 검토된 정책의 현재 질문 또는 행동 텍스트다. source=reviewed_policy_text이며 생성 모델의 미검토 요약을 안전 지침으로 바꾸지 않는다. 갱신 대기나 만료 시 발화는null이다. 단말 TTS로 읽을 수 있으며 서버 음성을 생성하지 않는다.
- GET /v1/me/updates는 cursor와 wait_seconds(0–25)를 사용한다. 기존 초안의 after 파라미터를 쓰지 않는다. 410은 전체 재동기화, 401은 세션 갱신 또는 재등록으로 처리한다.

## 배포·검증

마이그레이션f735a2ec901b가 app_sessions와 조회 인덱스를 추가한다. 기존 자료는 변경하지 않는다. 실제 일반 서버 배포 시 migration 뒤 등록을 사설망 시연에서만 켠다. APK의 USB 검증은 loopback 전용 경로로 연결하며 공개 인터넷에 무인증 등록을 노출하지 않는다. CORS는 BONGHWA_APP_CORS_ORIGINS의 명시된 원점만 허용한다.

실제 로컬 PostgreSQL에서 전체 서버 테스트91개, Alembic check, 변경 파일 Ruff가 통과했다. refresh회전/재사용폐기·만료·로그아웃, 등록off/live거부·동의검증·한도, 의료메모철회/삭제/오류 비노출, 준비카드, 현재 계단 상태→단계/발화 갱신을 검사했다. 기존 Starlette/httpx 경고1개가 있다. 합성0.2 응답을 캡처한 모의자료의 단계는 경고/대피/위급이며 실제 경보가 아니다.

서버 기능 구현과 로컬 검증 완료다. 앱 구현·일반 서버 재배포·휴대폰 통합 검증·APK 배포는 앱 실행 Job에서 이어간다. 현재 학습과 GPU 서비스를 변경하거나 중단하지 않았다.

### required-doc: docs/V2/delivery/mobile-server-deployment.md

- Path: `docs/V2/delivery/mobile-server-deployment.md`
- Status: present

# 앱 실연동 서버 배포

2026-11-01 KST. 일반 서버에 앱 설치 계정·회전 세션과 migration을 배포했다. 등록은 사설망 simulation의 mobile-demo에만 켜며 새로운 고유 사용자 계정을 만든다. 실제 예측과 FCM 실발신은 제공하지 않는다.

## 구현과 로컬 검증

Compose 등록·시나리오·CORS 설정을 전달한다. 기타 보호 대상(other)을 프로필에 저장하고 준비 지침에 반영한다. 실제 PostgreSQL에서 migration/check와 서버 테스트93개가 통과했다.

## 접속

SSH localhost18080 → 일반 서버 loopback8000을 사용한다. 휴대폰 USB 검증은 아래 연결을 유지한다.

```sh
ssh -N -L 127.0.0.1:18080:127.0.0.1:8000 inno-server-011
adb reverse tcp:18080 tcp:18080
```

단말 API 주소는 `http://127.0.0.1:18080`이다. USB·SSH 연결이 유지되어야 한다. APK에 내부 서비스 토큰·JWT 서명키를 넣지 않는다. 설치 계정 등록→기기 등록→프로필·위치 순으로 호출한다.

Tailscale Serve는 처음 자동 승인 검토에서 지속 노출의 명시 승인 부족으로 거절됐다. 이후 사용자가 Tailnet 전용 HTTPS를 명시 승인해 `https://inno-server-011.tail2dac17.ts.net` → `http://127.0.0.1:8000`을 설정했다. 공개 Funnel은 사용하지 않는다. 서버 자신의 HTTPS 인증서 검증과 readiness200은 통과했다.

최초 외부 접속은 기존 PacketFilter가 목적지 TCP22만 허용해 시간 초과였다. 이후 사용자 승인을 받은 개발 Mac·휴대폰 두 출발지에서 일반 서버 TCP443만 허용하는 grant를 관리 화면에서 추가했다. 개발 Mac에서 정상 TLS 인증서 검증과 HTTPS readiness200을 확인했다. 다른 Tailnet 기기 전체로 접근을 넓히지 않았다. 서버 DNS 수용은 기존대로 off이며 바꾸지 않았다. 단말은 Tailscale이 연결되어 있어야 한다.

## 합성 자료

컨테이너에서 python tools/mobile_demo.py를 실행한다. 별도의 mobile-demo/mobile-fire 자료를24시간 유효하게 입력하고 긴급 큐가 합성 경보를 처리하도록 한다. 테스트 좌표는36.4,129.35,정확도10m다. --seed-only는 자료만 갱신한다. 실제 산불·공식 발령이 아니다. 신규 계정 등록·정책 단계·cursor·refresh·로그아웃 검증은 토큰을 메모리에서만 사용한다.

## 실제 배포 검증

[기계 판독 근거](mobile-server-evidence.json)에 실행 결과를 기록했다.

- 최종 실행 소스는 `dcbc62e`(이미지 `bonghwajigi-mvp:dcbc62e`), migration은 `f735a2ec901b`다. PostgreSQL/Redis 볼륨을 유지하고 기존 시나리오 계정9개·입력87개를 전후 확인했다.
- 기존 설정과 PostgreSQL dump는 서버 `/home1/ncloud/.config/bonghwajigi/backups/mobile-d8dc54a`에 권한600으로 보관했다. 새 설정도600이고 기존 자격은 바꾸지 않았다. GPU 서버와 학습 프로세스를 변경하거나 중단하지 않았다.
- API/긴급·분석·전달/정책·통합/outbox 7개 프로세스와 DB/Redis가 실행되고 일반 서버/GPU 터널 systemd가 active다.
- 합성 설치 계정 두 개로 등록, 기기, 프로필 기타 보호 대상과 준비 카드, 위치, 긴급 큐 원문, 경고→대피→위급, 검토된 정책 텍스트, cursor 갱신, 다른 사용자 자료404, refresh회전, 로그아웃 뒤 access/refresh401을 확인했다.
- 무인증 프로필401, OpenAPI0.2.0-mvp, 명시한 localhost8081 CORS 허용과 미등록 원점400을 확인했다.
- 최종 배포 뒤 개발 Mac의 Tailnet HTTPS에서 새로운 합성 계정으로 등록→기기/프로필/위치→공식 원문→경고/대피/위급→cursor→refresh→로그아웃을 다시 확인했다. TLS 검증을 유지했고 배포 OpenAPI 전체JSON이 앱 타입 생성 원본과 일치했다.

공식 경보 알림의 전송 ID도 인증 API와 일치시켰다. DB 내부 사건/경보 ID는 취소·만료·중복 검사에 보존하고 발신 직전 payload.resource_id를 해당 사용자의 HMAC 공개ID로 바꾼다. 두 사용자의 캡처 발신 결과가 각각 본인 API200·다른 사용자404이며 ID가 서로 다름을 실제 DB에서 확인했다. 실제 Firebase 단말 수신 검증과 구분한다.

기타 보호 대상은 이동 준비 시간을 늘리는 입력이므로 단계 검증에서는 카드 저장 확인 뒤 독립이동 프로필로 초기화했다. 기기 등록 없이 위치를 보내면404로 거부되는 것을 확인하고 앱과 같은 호출 순서로 검증했다. 시연 도구의 실패는 수정 후 재검증했다.

## 운영과 한계

자료가 만료되면 `python tools/mobile_demo.py --seed-only`로 합성 자료의 새 revision을 입력한다. 유효기간24시간은 합성 사건 자료에만 적용되며 사용자 위치·현재 상태의 기존5분 유효기간은 유지한다. APK가 전송한 최신 위치만 사용자 관련성 판단에 쓰며 신규 계정을 임의 테스트 좌표로 자동 이동시키지 않는다.

이 문서의 검증은 배포 API 결과다. 실제 휴대폰 화면·TTS·APK 설치 검증은 앱 작업에서 이어진다. 실제 재난·공식기관 발령·Firebase 단말 수신·실측 지도 경로·실제 예측 결과가 아니다. 사고 종료 근거가 없으므로 자료 최신성을 사건 종료로 해석하지 않는다.

## Verified Team Policies

No verified Team Policy Snapshot is active.

## Active Workflow Memory

No active workflow memory recorded.
