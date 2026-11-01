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
- Task count: `12`

## Task

- Title: 재난 경보를 포함한 Qwen3 사건 통합 실행과 추론 직전 결과 문서화
- Description: 사용자 직접 지시: 기존 검색 묶음의 경보 포함 여부를 확인하고 경보·저장 자료·검색 근거를 Qwen3로 실제 통합한 뒤 XGBoost 입력 직전에서 멈춰 결과 문서를 제공한다. 이전 결과에는 실제 경보가 없었음을 명시하며 확보 가능한 공식 경보 또는 명확히 표시한 재생 자료를 사용한다.
- Expected output: 경보 포함 시나리오 입력, Qwen3 통합 및 근거 검증 도구, 실제 생성 원문과 검증된 추론 전 JSON, 사람이 읽는 결과 문서
- Done condition: 실제 Qwen3 모델을 호출해 출처가 연결된 통합 결과를 저장한다. 경보 원문과 모의·과거 구분을 보존하며 없는 수치와 개인 정보를 만들지 않고 입력 결측과 추론 가능 여부를 문서화한다. XGBoost 추론·대응 결정·알림을 실행하지 않는다. 검증 및 Loom 기록을 커밋한다.
- In scope: 공식 경보 자료 확인·재생, 기존 검색 결과와 사건 단위 결합, Qwen3 생성 클라이언트와 구조화 검증, 추론 입력 사전 검사, 실제 GPU 호출 및 결과 문서화
- Out of scope: XGBoost 학습·추론, 개인 정책·대응 레벨·알림, 실제 K8s 수집, 앱 저장소, 다른 채팅의 학습 작업 변경, 공개 포트·서비스 강제 중단
- Validation hint: 공식 경보 출처와 원문 보존, 사건·시각 격리, 모델 출력 근거 및 JSON 검증, 수치 날조 거부, 실제 Qwen3 호출·모델 버전·토큰 수 기록, XGBoost 미호출 확인, 기존 테스트 및 Loom strict
- Required docs: `docs/V2/delivery/analysis-retrieval-flow.md`, `docs/V2/delivery/gpu-model-readiness.md`
- Memory refs: -
- Document outputs: `docs/V2/delivery/qwen-integration-result.md`
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

### required-doc: docs/V2/delivery/gpu-model-readiness.md

- Path: `docs/V2/delivery/gpu-model-readiness.md`
- Status: present

# GPU 서버의 세 모델 실행 준비 결과

확인일: 2026-10-31 18:08~18:13 KST. Loom Task: `task-20261031-085956-gpu-qwen-xgboost-9eea12a5`.

두 Qwen 모델의 다운로드·동시 상주·실제 생성/임베딩과 XGBoost의 합성 CUDA 학습·저장·CPU 재로딩을 확인했다. 사용자 GPU 서비스는 localhost에서 실행 중이며 로그아웃 후 유지와 자동 시작을 설정했다. 실제 산불 모델의 정답·목표·성능이나 개인 대응 정책을 준비한 결과는 아니다.

## 설치 위치와 버전

대상은 `inno-gpu-011`, 계정은 `ncloud`, 프로젝트는 `/home1/ncloud/bonghwajigi`다. 기존 전역 Python과 다른 서비스는 변경하지 않고 새 사용자 환경에 설치했다.

| 환경 | 경로·주요 버전 |
| --- | --- |
| 공통 Python | 서버 기존 Python 3.12.3 |
| GPU 서빙 | `.venv-gpu`: torch 2.11.0+cu128, Transformers 4.57.6, Sentence Transformers 5.7.0 |
| XGBoost | `.venv-ml`: XGBoost 3.4.1, 별도 NumPy/pandas/PyArrow/scikit-learn |
| 의존성 정본 | 저장소의 `pyproject.toml`, `uv.lock` |
| 모델 캐시 | `/home1/ncloud/bonghwajigi/models/hub` |
| 설치 정보 | 서버 `model-manifest.json` |
| 서비스 설정 | `~/.config/bonghwajigi/gpu.env`, 권한 600 |

서비스 토큰은 서버에서 새로 생성했고 출력하거나 저장소에 복사하지 않았다. SSH 비밀번호도 보관하지 않았다. 공식 uv 설치 주소가 403으로 차단돼 공식 PyPI의 uv 0.11.10 wheel SHA256을 대조한 후 사용자 `~/.local/bin/uv`에 설치했다.

| 모델 | 고정 revision |
| --- | --- |
| `Qwen/Qwen3-4B-Instruct-2507` | `cdbee75f17c01a7cc42f958dc650907174af0554` |
| `Qwen/Qwen3-Embedding-0.6B` | `97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3` |

두 모델은 캐시의 고정 revision을 BF16으로 로딩한다. 실행 중 자동 다운로드는 하지 않는다. Qwen은 사실 정리·설명 도구이며 검토되지 않은 출력을 개인 대응 정책으로 승인하지 않는다.

## 바로 사용하기

```sh
ssh inno-gpu-011
cd /home1/ncloud/bonghwajigi
.venv-gpu/bin/python tools/gpu_client.py ready
.venv-gpu/bin/python tools/gpu_client.py generate --text "한국어로 모델 준비 상태를 한 문장으로 써줘."
.venv-gpu/bin/python tools/gpu_client.py embed --text "임베딩할 문서"
.venv-gpu/bin/python tools/gpu_client.py embed --input-type query --text "찾을 자료에 대한 질문"
```

클라이언트는 서버 설정 파일에서 토큰을 읽어 localhost API를 호출하며 토큰을 출력하지 않는다. `/internal/v1/generate`와 `/internal/v1/embeddings`는 Bearer 서비스 토큰이 필요하다. 일반 서버에서 이 API를 호출하는 서비스 경로·인증 주입은 A3에서 연결한다. 이번에는 공개 포트나 Tailnet 규칙을 변경하지 않았다.

- 입력+출력 합계 4096토큰, 생성 출력 최대 512토큰이다. 초과 입력은 잘라 쓰지 않고 422로 거부한다.
- 임베딩은 요청당 최대 8문서, 문서당 4096토큰 이내다. 1024차원 float32 벡터를 반환하고 단위 길이로 정규화한다. 질의에는 검색 지시 접두사를 적용한다.
- 한 프로세스에 두 모델을 한 번씩 올리고 GPU 요청을 직렬 실행한다. 다른 요청이 점유 중이면 최대 2초 대기 후 503/Retry-After를 반환한다.
- `/health/live`는 프로세스 상태, `/health/ready`는 두 모델의 로딩 상태다. 현재 GPU 서버의 ready는 200이며 기본 로컬 스캐폴딩은 `BONGHWA_GPU_ENABLED=false`라 503을 유지한다.
- 모델 오류를 확률 0이나 안전 판정으로 바꾸지 않는다. 입력과 인증 토큰은 접근 로그에 남기지 않는다.

## 서비스 관리와 XGBoost

```sh
systemctl --user status bonghwajigi-gpu.service
systemctl --user restart bonghwajigi-gpu.service
journalctl --user -u bonghwajigi-gpu.service -n 30 --no-pager
```

사용자 서비스는 `active/enabled`, `Linger=yes`이고 `127.0.0.1:8001`에만 바인딩한다. 기존 관리 SSH 연결을 종료하고 새 로그인에서 준비 상태 200을 재확인했다. 새 서비스의 코드 재시작도 검증했다. 실제 서버 재부팅 시험은 수행하지 않았다.

XGBoost는 설치·CUDA 실행 준비가 끝났다. 실데이터 학습 전에 C1의 예측 목표·정답·피처 계약과 C4의 평가 기준이 필요하다. 생성 모델의 학습 또는 파인튜닝은 수행하지 않았다.

새 합성 CUDA 검사를 실행하려면 모델 서비스를 내린 뒤 새 산출물 디렉터리를 지정한다. 검사가 끝나면 서비스를 다시 시작한다.

```sh
cd /home1/ncloud/bonghwajigi
systemctl --user stop bonghwajigi-gpu.service
.venv-ml/bin/python -m bonghwajigi.ml.cuda_check --output data/artifacts/cuda-check-new
systemctl --user start bonghwajigi-gpu.service
```

서빙과 학습은 같은 사용자 GPU 잠금 파일을 사용한다. 서빙 중 위 검사를 실행하면 학습 전에 거부되며 산출물도 생성하지 않는다. 잠금은 이 프로젝트의 실행기끼리 조율하는 장치이며 외부 CUDA 프로그램을 통제하는 GPU 격리 기능은 아니다.

검증용 `simulation-booster.ubj`는 `data/artifacts/cuda-check-20261031T090759Z/`에 있다. 합성 실행 검사 전용이며 산불 영향 확률 API에 사용하지 않는다.

## 실제 측정

[검증 근거 JSON](gpu-model-evidence.json)에 인증정보 없이 결과를 보관했다.

| 항목 | 결과 |
| --- | --- |
| Qwen 한국어 생성 | 입력 29 / 출력 9토큰, 약 845ms, `모델 준비 완료되었습니다.` |
| 문서 임베딩 | 2문서 × 1024차원, 약 124ms |
| 문서 벡터 길이 | 1.0000000383 / 1.0000000101 |
| 질의 임베딩 | 1024차원, 약 32ms |
| 무인증 요청 | 401 |
| 전체 토큰 상한 초과 | 422 |
| 두 모델 호출 후 GPU 메모리 | 9,134 / 23,034 MiB |
| 서빙 중 XGBoost 학습 시도 | 잠금으로 거부, 산출물 생성 없음 |
| XGBoost 합성 CUDA 학습 | `cuda:0`, 5000행 × 16피처, 20회, 약 0.319초 |
| 저장 후 CPU 재추론 최대 절대 차이 | 약 1.19 × 10⁻⁷ |
| 설치 후 잔여 디스크 | 약 61.23 GiB |

PyTorch CUDA runtime은 12.8이며 실제 L4 사용을 확인했다. 설치된 XGBoost wheel은 CUDA 13.3 빌드이고 같은 드라이버 580.159.04에서 실제 작은 학습이 통과했다. 다른 CUDA 기능·대규모 학습 조합까지 검증한 것은 아니다.

위 지연은 짧은 설치 검사 요청의 한 번 측정이다. 4096토큰·최대 배치·동시 사용자·한국어 문서 품질·장시간 운영 성능을 보장하지 않는다. 실제 자료의 검색 적합성·추출 품질·정책 설명 검증은 D3에서 이어간다. 공식 긴급 원문 경로는 이 모델 API를 기다리지 않아야 한다.

## Verified Team Policies

No verified Team Policy Snapshot is active.

## Active Workflow Memory

No active workflow memory recorded.
