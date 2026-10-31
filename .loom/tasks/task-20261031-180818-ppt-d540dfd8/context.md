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
- Task count: `24`

## Task

- Title: 기술 스택 페이지를 기존 발표 스타일의 편집용 PPT로 제작
- Description: 첨부 ppt_8.webp의 기술 스택·직접 개발 범위·검증 내용을 앞서 만든 3장 아키텍처 PPT와 동일한 시각 스타일로 재구성한다.
- Expected output: 편집 가능한 1장 PPTX와 PNG 미리보기
- Done condition: 5개 기술 구성과 직접 개발·검증 내용을 포함하고 기존 PPT 스타일·한글·배치를 확인하며 파일 검증을 통과한다.
- In scope: 첨부 이미지 내용 재구성, 기존 PPT 스타일 재사용, PPTX·PNG 생성과 검증, Loom 기록
- Out of scope: 기존 3장 수정, 앱·서버·학습 구현과 배포, 검증 수치의 새 측정
- Validation hint: 1장·16:9·텍스트/도형 편집 가능성, 원본 내용과 스타일 비교, PPTX 패키지·레이아웃 검사
- Required docs: `docs/V2/delivery/presentation-architecture.md`
- Memory refs: -
- Document outputs: `docs/V2/delivery/tech-stack-slide.md`
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

### required-doc: docs/V2/delivery/presentation-architecture.md

- Path: `docs/V2/delivery/presentation-architecture.md`
- Status: present

# 봉화지기 발표용 아키텍처

기준: **2026-11-01 KST**. 사용자 제공 세로 배치도와 현재 서버 코드, 배포 검증 기록, 진행 중인 앱 구현을 대조한 발표용 자료다. 최신 서버 코드를 오늘 새로 배포하거나 단말 기능을 검증했다는 의미는 아니다.

## 발표 자료

16:9 비율의 **3200 × 1800 PNG 3장**이다. PowerPoint에는 원본 비율을 유지한 채 슬라이드 전체에 배치하면 된다. 편집용 PowerPoint의 글자와 도형은 개별 개체이며, SVG와 생성 스크립트도 함께 보관한다.

1. [전체 서비스 흐름](architecture-slides/output/01-overview.png): 자료 받기, 근거 정리하기, 나에게 맞추기, 안내 갱신하기의 4단계와 실행 위치.
2. [AI 모델별 역할](architecture-slides/output/02-ai-roles.png): 임베딩·Qwen의 실제 연결 흐름과 별도 XGBoost 연구의 필요성, 입력, 출력.
3. [긴급 알림과 개인별 안내 갱신](architecture-slides/output/03-alert-update.png): 공식 원문 우선 처리와 개인별 재평가의 반복 흐름.

[편집용 PowerPoint](architecture-slides/output/bonghwajigi-architecture.pptx) · [이미지·원본 묶음](architecture-slides/output/bonghwajigi-architecture.zip)

PowerPoint와 SVG는 Apple SD Gothic Neo를 지정했다. 글꼴이 없는 환경에서는 글꼴 대체가 발생할 수 있으므로 그대로 발표할 때는 PNG 사용을 권장한다. 글꼴 파일은 배포하지 않는다. 아이콘은 이 자료를 위해 직접 만든 도형이다.

## 기존 그림에서 달라진 부분

| 기존 그림의 표현 | 현재 구성에 맞춘 표현 |
| --- | --- |
| K8s 수집기가 상시 실행 | K8s 구성은 보존한다. MVP 데이터는 확보 자료와 합성·과거 재생 시나리오를 수신 API에 넣는다. |
| 일반 서버의 DB·큐를 한 덩어리로 표현 | 일반 서버 Docker Compose의 PostgreSQL+pgvector와 Redis/Celery, DB outbox, 긴급·분석·전달·정책·통합 실행기를 사용한다. 개발 컴퓨터의 별도 테스트 DB도 존재한다. |
| 임베딩 모델이 추가 검색 | 임베딩 모델은 문서를 벡터로 바꾼다. 일반 서버의 pgvector가 유사 근거를 검색하고, Google News RSS 어댑터가 인터넷 뉴스의 제목·설명·링크·시각을 추가한다. |
| 사건 통합에 위치·프로필까지 모두 포함하는 듯한 연결 | 자료 요약과 사용자별 판단을 구분한다. Qwen의 자동 통합 입력에는 관측·검색 근거를 넣으며, 개인 위치·프로필을 자동으로 외부 검색어나 Qwen 입력에 넣지 않는다. |
| Qwen 정리 후 XGBoost 추론으로 이어지는 필수 직렬 경로 | 두 Qwen 모델의 자료 분석은 연결돼 있다. 실제 XGBoost 예측은 서비스에 연결하지 않았다. Qwen 요약을 검증된 수치 모델 입력으로 자동 변환하지 않는다. |
| 일반 서버 CPU의 XGBoost 추론을 현재 실행처럼 표시 | 학습·평가 산출물은 별도 연구 경로다. 서비스의 실제 예측 상태는 `unavailable`, 확률은 `null`이다. |
| AI가 개인 대응 정책을 만드는 듯한 표현 | 서버가 검토된 시연 규칙과 DB 지침을 적용한다. 공식 경보, 환경 입력, 위치 관련성, 이동 능력, 확인된 현재 상태를 사용한다. Qwen 자유 문장과 미검증 확률로 단계를 정하지 않는다. |
| 알림 전송을 실제 단말 수신과 동일하게 표시 | 서버 변경 조회·전달 큐와 모의 발신은 구현했다. Firebase 자격·토큰 연결 전이라 실제 단말 푸시 수신은 완료로 표시하지 않는다. 앱 연동·실기기 검증도 진행 중이다. |
| 공식 경보와 개인 정책을 거친 하나의 안내 | 공식 원문은 긴급 전용 경로로 먼저 처리한다. 개인 정책과 GPU 완료를 기다리지 않는다. 개인 안내는 별도로 갱신한다. |
| 서버의 보충 설명을 음성 처리로 오해할 가능성 | 서버는 텍스트를 제공하고 앱이 기기 TTS로 읽는 구조다. 서버 STT/TTS는 범위에서 제외한다. |
| 지도·위치 판단을 경로 안전성으로 확대할 가능성 | 현재 관련성은 공급된 구역과 GPS 정확도·시각을 검사하는 수준이다. 3D는 제외하며 실제 지도 키·검증된 도로 경로 엔진은 미연결이다. |

## 각 모델의 필요성과 경계

| 모델 | 필요한 이유 | 현재 입력과 출력 | 적용 상태 |
| --- | --- | --- | --- |
| Qwen3-Embedding-0.6B | 표현이 다른 문서에서도 같은 사건의 관련 자료를 찾기 위해 | 문서·검색 질의를 1024차원 벡터로 변환. DB 검색 결과는 근거 문장·출처·유사도이며 유사도는 산불 확률이 아니다. | GPU API 실제 호출과 일반 서버 검색 연결 검증 기록 있음 |
| Qwen3-4B-Instruct-2507 | 여러 근거를 사람이 읽기 쉬운 사건 설명으로 정리하기 위해 | 관측·검색 문서에서 요약과 인용을 생성. 요약은 `not_reviewed` 참고 자료로 보관한다. | GPU 생성과 일반 서버 통합 연결 검증 기록 있음. 대응 단계·행동 결정에는 미사용 |
| XGBoost | 정형 관측의 변화와 위치 관계로 환경 노출·접근을 수치화할 후보를 연구하기 위해 | 기존 관측 기반 연구와 별도의 GOFER 접근 시간 AFT 초기 실험이 존재한다. 접근 시간·기간별 확률은 연구 산출물이며 국내 개인 피해 확률로 검증된 값이 아니다. | 서비스 미연결. 입력의 당시 가용성, 국내 독립 사건 검증과 확률 보정이 남음 |

최신 학습 작업에는 ELMFIRE 등 별도 연구 도구도 추가돼 있다. 이 자료의 3개 모델은 **MVP의 두 언어 모델과 수치 예측 후보의 역할**을 설명한다. 모든 연구 도구를 이미 운영 중인 서비스 구성으로 합쳐 그리지 않았다. 상세 연구 상태는 [학습 개선 기록](korea-wildfire-improvement.md)을 따른다.

## 안내는 어떻게 갱신하는가

- 공식 경보는 발령 구역·출처·시각·상태를 검사하고 원문과 정정·해제 이력을 보존한다. 관련 사용자에게 전달 작업을 만든다.
- 개인 안내는 **1 경고, 2 대피, 3 위급**이다. 자료 부족이나 만료는 확인 중으로 다루며 안전 또는 0%로 바꾸지 않는다.
- 프로필·위치·현재 상태 변경은 해당 사용자를, 사건·경보·지침 변경은 관련 사용자들을 재평가한다. 같은 단계에서도 행동이나 적용 버전이 달라지면 새 안내를 제공한다.
- 새 입력이 없을 때에도 만료를 점검한다. 내용이 같은 평가 결과를 무조건 새 알림으로 만들지 않는다. 하향에는 추가 조건이 필요하며 통신 중단·경보 취소만으로 개인 안전을 확정하지 않는다.
- 현재 Compose의 정책 실행 대기 간격은 1초, 주기 점검 간격은 10초다. 이 설정은 앱까지의 전달 지연 보장이 아니므로 발표 그림에 속도 수치로 제시하지 않았다.
- 119 연락은 사용자가 기기 전화·문자 화면에서 직접 실행한다. 자동 신고를 의미하지 않는다.

## 발표에서 쓸 쉬운 용어

| 개발 용어 | 발표용 표현 |
| --- | --- |
| 파이프라인 | 자료를 받아 안내로 바꾸는 처리 흐름 |
| 이벤트 수신 API | 자료를 받는 창구 |
| 큐·워커 | 작업을 나눠 처리하는 대기열과 실행기 |
| 임베딩 | 비슷한 내용을 찾기 위한 숫자 표현 |
| 벡터 검색 | 관련 근거 찾기 |
| 사건 통합 | 같은 산불의 자료 정리 |
| 개인별 대응 정책 | 나에게 맞는 행동 안내 |
| revision·cursor | 안내 버전과 변경 기록 |
| unavailable | 예측 불가 또는 확인할 자료 부족 |

## 대조 근거

시각화는 작업 트리의 실행 코드와 최신 상태 기록을 우선한다. 과거 단계별 보고서의 ‘아직 미구현’ 문구를 현재 상태로 그대로 옮기지 않았다.

- [서버 구성](../../../deploy/compose/mvp.yaml), [배포 운영 기록](mvp-server-runbook.md), [실제 배포 검증 자료](mvp-server-evidence.json). 마지막 완료된 배포 검증의 실행 커밋은 `654a9ef`다. 이번 문서 작업은 원격 상태를 새로 검사하거나 배포하지 않았다.
- [검색 파이프라인](../../../src/bonghwajigi/retrieval/pipeline.py), [인터넷 뉴스 검색](../../../src/bonghwajigi/retrieval/web_search.py), [Qwen 통합](../../../src/bonghwajigi/policy/integration.py).
- [정책 평가와 만료](../../../src/bonghwajigi/policy/service.py), [3단계 규칙](../../../src/bonghwajigi/policy/three_stage.py), [확정 정책 설명](response-policy.md).
- [긴급 처리](../../../src/bonghwajigi/events/urgent.py), [변경·알림 요청](../../../src/bonghwajigi/notifications/service.py), [사용자 API](../../../src/bonghwajigi/api/mobile.py).
- [GPU 모델 준비](gpu-model-readiness.md), [학습 개선과 접근 시간 초기 실험](korea-wildfire-improvement.md).

## 원본 재생성

`architecture-slides/source/build.mjs`는 같은 좌표 원본으로 편집 가능한 PowerPoint, SVG와 PNG를 생성한다. 도구 실행에 필요한 패키지는 Codex의 번들 `@oai/artifact-tool`을 사용한다. `finalize.mjs`는 3장·16:9·글꼴·패키지와 재가져오기를 검사해 별도 최종 파일을 만든다. 검증용 중간 파일은 Git 산출물에 포함하지 않는다.

## Verified Team Policies

No verified Team Policy Snapshot is active.

## Active Workflow Memory

No active workflow memory recorded.
