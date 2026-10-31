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
- Task count: `20`

## Task

- Title: 현행 산불 MVP 아키텍처를 발표용 3장 이미지로 정리
- Description: 사용자의 기존 다이어그램 대조와 발표용 이미지 작성 지시에 따라 현재 코드와 배포 근거를 확인하고 전체 4단계 흐름, AI 역할, 긴급 알림과 개인 안내 갱신을 3장으로 시각화한다.
- Expected output: 고해상도 16:9 PNG 3장, 편집 가능한 원본, 변경 비교와 근거 문서
- Done condition: 현재 구현·배포 확인 근거와 일치하고 미연결 기능을 표시하며 한국어 글자·연결선·배치를 실제 렌더링으로 확인한다.
- In scope: 기존 그림과 코드·배포 근거 읽기, 발표용 다이어그램 3장과 비교 설명, Loom 기록 및 산출물 커밋
- Out of scope: 실행 코드·학습·배포 변경, 진행 중 앱 구현 파일 변경, 실제 예측 연동, 신규 외부 자원 전송, 비밀값 포함
- Validation hint: 코드 경로 대조, 3장 전체 고해상도 시각 검사, 텍스트 범위·글꼴·슬라이드 수 검증, Loom strict
- Required docs: `docs/V2/delivery/mvp-server-runbook.md`, `docs/V2/delivery/response-policy.md`, `docs/V2/delivery/analysis-retrieval-flow.md`
- Memory refs: -
- Document outputs: `docs/V2/delivery/presentation-architecture.md`
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

### required-doc: docs/V2/delivery/response-policy.md

- Path: `docs/V2/delivery/response-policy.md`
- Status: present

# 산불 MVP의 확정 3단계 정책

2026-10-31 사용자 승인: 첨부 정책 초안과 회의 정리를 바탕으로 3단계를 채택하고, 후속 메시지로 **경고 < 대피 < 위급** 명칭을 확정했다. 정책 버전은 `wildfire-three-stage-v1`이다. 이번 구현은 시연 모드이며 실제 예측 모델 연결·자동 신고·실제 단말 발송을 포함하지 않는다.

| 단계 | 화면 명칭 | API enum | 행동 기준 |
| --- | --- | --- | --- |
| 1 | 경고 | `prepare` | 관련 산불에 대한 공식 안내 확인과 대피 준비 |
| 2 | 대피 | `act` | 지금 이동해야 하며 스스로 또는 지원을 받아 대피 실행 |
| 3 | 위급 | `request_assistance` | 대피가 필요한데 고립·이동 불가·조력자 부재로 긴급 지원 필요 |

평소에는 단계를 만들지 않는다. 자료 부족은 `unknown`, 도착 후 확인은 `information`이며 안전 판정을 뜻하지 않는다. `attention`은 이번 정책에서 사용하지 않는다. 공식 기관 등급은 원문대로 따로 보존한다.

## 판단과 개인화

| 환경 구간 | 독립 이동 | 준비·이동에 시간 필요 | 다른 사람의 이동 지원 필요 |
| --- | --- | --- | --- |
| H1 관련 산불 | 경고 | 경고 | 경고·조력자 연락 우선 |
| H2 접근 우려 | 경고 | 대피 | 대피·도움 확보, 미확보 시 지원 요청 안내 |
| H3 공식 대피 또는 현장 위험 | 대피 | 대피 | 실제 조력자가 곁에 있으면 대피, 없으면 위급 |
| H2 이상이며 이용 가능한 대체 경로도 없음 | 위급 | 위급 | 위급 |

환경 구간은 출처·검토 여부·유효 시각이 있는 내부 입력이다. 거리 수치·풍향만으로 모델이 임의 생성하지 않으며 확률은 판단에 사용하지 않는다. 경로가 모르면 막힘/열림으로 추정하지 않는다. 현재 2D 경로 엔진은 제공하지 않으며 검토된 경로 상태만 받는다.

사용자가 갇힘을 보고하거나 부상과 이동 불가를 보고하면 GPS 부재나 확인 질문으로 위급 안내를 지연하지 않는다. 연기·불꽃·두려움은 즉시 대피 안내의 근거이며 그 자체를 고립으로 간주하지 않는다. 조력자 등록과 현재 곁에 있음은 별개다. 고령·장애라는 이유만으로 일괄 위급 처리하지 않는다.

상향은 새 입력 즉시 재평가한다. 하향은 신선한 H1 자료와 사용자 확인, 또는 새로 확인된 이용 가능한 경로와 이동 지원 확보가 있어야 한다. 통신 중단·자료 만료는 해제 근거가 아니다. 공식 취소 역시 개인의 안전이나 귀가 가능성을 단정하지 않는다. 도착은 사용자 보고로만 처리한다.

## 기본 지침과 긴급 연락

국민안전24의 [산불 행동요령](https://www.safekorea.go.kr/safekorea-kor/acts/nacts/action-guide.do?category=forestFires&menuSn=4)을 확인해 국내 기본 안내 10개를 정규화했다. 해외 고립 행동·집 안/차량 생존 전술은 포함하지 않는다. 위치·인원 전달 문구는 신고를 돕는 서비스 문구이며 원문 인용으로 표시하지 않는다.

`POST /internal/v1/policy/scenarios/{scenario_id}/bootstrap-policy`로 지침과 고정 정책을 DB에 등록한다. 재호출은 중복으로 반환한다. 지침은 출처·검토 상태·revision·30일 유효 기간을 보존한다. `source.published_at`은 이 정규화한 지침 버전 게시 시각이고 원본 웹페이지의 최초 게시일은 미확인이다. 과거 성능 백테스트의 당시 가용 자료로 주장하지 않는다.

위급에서는 질문 없이 119 연결 수단을 제공한다. 모든 단계에서 119를 사용할 수 있고 최종 전화·문자 전송은 OS 화면에서 사용자가 실행한다. 서버는 신고를 보내거나 접수 완료를 표시하지 않는다. 앱 저장소는 변경하지 않는다.

## 수신·갱신·알림

`/internal/v1/scenario-events`의 urgent payload는 `incident_id`, `alert_id`, `incident`, `alert`다. 발령·정정·취소 revision을 DB/outbox와 긴급 Celery 큐에 저장한다. 긴급 실행기는 GPU나 분석 큐를 호출하지 않고 원문·시각·대상 관련성부터 저장한다. 중복 수신은 멱등, 오래된 revision은 superseded다.

공식 원문, 개인 정책, 기기 알림은 서로 다른 리소스다. 사용자별 변경 cursor는 같은 시나리오의 쓰기 순서를 잠금으로 직렬화해 누락을 방지한다. 알림은 DB outbox·독립 delivery 큐·임대·최대 5회 재시도·기기 revision·리소스 revision으로 재전달과 오래된 작업을 제어한다. 동일 revision은 중복 생성하지 않는다.

경고 최초 진입은 일반 알림, 대피는 높은 우선순위, 위급은 긴급 우선순위를 요청한다. 실제 단말의 소리·진동은 앱/OS 권한에 따른다. 같은 단계에서 행동이 바뀌면 갱신하고 같은 내용은 반복하지 않는다. 원문 취소는 기존 수신 대상에게 별도 갱신한다.

사용자 답변에 따라 이번 배포는 `push_provider=simulation`이다. `simulated`, FCM의 `provider_accepted`, 실제 앱의 `received_at`·`opened_at`을 구분한다. FCM HTTP v1 어댑터는 준비하지만 프로젝트·자격 파일·기기가 없어 실제 전송을 하지 않는다. 푸시 payload에는 정밀 위치·프로필·경보 원문을 넣지 않는다.

FCM 구현 근거: [HTTP v1 인증과 전송](https://firebase.google.com/docs/cloud-messaging/send/v1-api), [전송 API](https://firebase.google.com/docs/reference/fcm/rest/v1/projects.messages/send).

## 내부 추가 입력

- `PUT /incidents/{incident_id}/environment`: H1~H3, 출처, 사유, 관측·만료 시각.
- `PUT /incidents/{incident_id}/users/{user_id}/state`: 현재 이동 가능·부상·조력자·관측 위험·위치 유형·대피 진행 상태.
- `PUT /incidents/{incident_id}/users/{user_id}/route`: 이용 가능한 대피 경로의 open/blocked/unknown, 출처·사유·시각. 클라이언트가 검증된 경로로 임의 등록하는 API가 아니다.

기존 개인 계획 루프와 같은 revision·시나리오 격리를 유지한다. 재평가 대기나 만료 때는 이전 단계도 `last_known_response`로 옮겨 최신 판단과 구분한다.

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

## Verified Team Policies

No verified Team Policy Snapshot is active.

## Active Workflow Memory

No active workflow memory recorded.
