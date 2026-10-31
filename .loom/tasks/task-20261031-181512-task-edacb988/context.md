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
- Task count: `25`

## Task

- Title: 네이버 실지도 검증 앱 버전을 서브모듈에 고정하고 외부 자원 문서 갱신
- Description: 사용자가 승인한 네이버 지도 앱 연결·APK 검증이 완료되면 최종 앱 원격SHA를 apps/mobile에 고정하고 메인 배포 출처 및 지도 자원·라이선스 범위를 갱신한다. 앱 담당자가최종QA와SHA를제공하기전에는pin을확정하지않는다.
- Expected output: 검증된 지도 APK 앱 gitlink; 업데이트된 배포 출처와 네이버 지도 자원 문서; 재귀clone/API/manifest 원격 검증 기록
- Done condition: 최종 앱 원격SHA와APK manifest를대조해gitlink를고정하고 새checkout의소스검사와메인정상push가통과한다. 지도상태는실제검증근거대로갱신하고타채팅license/training/presentation변경을보존한다.
- In scope: 앱소스 읽기검토; main submodule pin; mobile-submodule-deployment.md 및 external-resources-and-licenses.md의네이버지도부분; 해당Loom기록과normalpush
- Out of scope: 앱코드수정;지도키/Secret수집·출력;실제GPS·서버API·GPU·학습변경;타채팅변경커밋;forcepush
- Validation hint: 원격앱SHA존재;manifest실행SHA와APK해시;실지도QA근거;gitlink160000;freshrecursiveclone및sourcechecker;공식라이선스출처;gitdiffcheck;Loomstrict
- Required docs: `docs/V2/delivery/mobile-submodule-deployment.md`
- Memory refs: -
- Document outputs: `docs/V2/delivery/mobile-submodule-deployment.md`, `docs/V2/delivery/external-resources-and-licenses.md`
- Document output exceptions: -
- Source proposal: `-`
- Status: PENDING
- Assigned agent: -

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

### required-doc: docs/V2/delivery/mobile-submodule-deployment.md

- Path: `docs/V2/delivery/mobile-submodule-deployment.md`
- Status: present

# 앱 서브모듈과 배포 소스 확인

2026-11-01 KST. 앱 저장소를 `apps/mobile`의 Git 서브모듈로 연결한다. 정본 원격은 사용자가 지정한 `https://github.com/duswls98952/BONGHWAJIGI_APP.git`이다. 일반 서버와 앱은 각각의 커밋을 갖고 메인 저장소가 검증된 앱 커밋을 고정한다.

APK 실행 소스는 `0716c49d501fe5e066537b673698e07fcbd48ff6`이며 APK SHA256은 `fe6892591e5224f5b982d53ce0536425f4a44290182477b865b922a63b2ad5e9`이다. 메인 gitlink는 단말 검증 문서가 포함된 `ed91b1ce78554e339e9a95bbc49a4028cc957178`에 고정한다. 두 커밋 사이에는 문서와 검증 기록만 추가됐다. [앱 APK 배포·단말 검증 문서](../../../apps/mobile/docs/10-android-delivery.md)와 [빌드 manifest](../../../apps/mobile/docs/validation/android-build.json)에서 산출물 근거를 확인한다.

## 초기화와 소스 확인

새 컴퓨터에서는 다음 명령으로 서브모듈까지 받는다.

```sh
git clone --recurse-submodules --branch develop https://github.com/develsvai/BONGHWAJIGI.git
cd BONGHWAJIGI
python3 tools/check_mobile_source.py
```

기존 checkout에서는 메인 커밋을 정상 갱신한 다음 실행한다. 작업 중인 소스가 있다면 먼저 해당 작업을 보존한다.

```sh
git submodule sync --recursive
git submodule update --init --recursive
git submodule status apps/mobile
python3 tools/check_mobile_source.py
```

검사 도구는 메인 HEAD의 `160000` gitlink, 앱 checkout SHA, 앱 미커밋 변경 유무, 서버·앱 OpenAPI의 일치를 확인한다. 정상이라면 메인/앱 SHA, API/lockfile 해시와 Node·Expo·React Native 버전을 출력한다. 서브모듈에서 임의 `git pull`이나 `update --remote`로 최신 브랜치를 받으면 메인에서 검증한 SHA와 달라질 수 있다.

## 앱 빌드와 결과물

앱의 Node 요구 범위는 `package.json`을 따른다. 현재 Node24와 lockfile을 사용한다.

```sh
cd apps/mobile
npm ci
npm run check
```

Android SDK·JDK·서명키·공개 API 주소를 준비한 APK 빌드와 단말 검증은 [앱 배포 문서](../../../apps/mobile/docs/10-android-delivery.md)를 따른다. 서버 서비스 토큰·JWT 서명키·GPU 토큰·Firebase 비밀키를 앱 환경에 넣지 않는다. 서명 자격은 Git 밖의 비공개 파일로 관리한다. APK 바이너리와 서명키를 gitlink에 추가하지 않는다.

앱 결과물에는 실제 빌드에 사용한 앱 소스 SHA, API 주소, 앱 버전, 서명 인증서 지문, APK SHA256을 함께 남긴다. `check_mobile_source.py` 출력은 소스 일치 근거이며 APK 설치나 단말 기능 검증을 대신하지 않는다.

앱 API는 [일반 서버 배포 문서](mobile-server-deployment.md)의 Tailnet HTTPS를 사용한다. 현재 실행 서버 소스는 `959ab56`이며 [단말 시계 보정 배포](mobile-location-clock-skew.md)를 포함한다. 승인된 단말의 Tailscale 연결이 필요하다. Firebase·네이버 지도 자격과 실제 예측 연결은 별도 준비 조건이다.

## 실기기 연결 근거

사용자는 설치된 APK에서 1·2·3단계 갱신을 확인했다. 음성 재확인에서는 휴대폰이 무음이었다고 설명하고 무음 해제 뒤 정상 청취를 최종 확인했다. 같은 합성 계정의 서버 DB를 2026-10-31 17:44:16 UTC에 읽기 대조하여 다음 정책 이력을 확인했다. 계정 식별자·토큰·개인 위치는 이 문서에 포함하지 않는다.

| 서버 정책 revision | 단계 | 평가 시각 UTC |
| --- | --- | --- |
| 2 | 경고 (`prepare`) | 2026-10-31 17:43:08.895844 |
| 3 | 대피 (`act`) | 2026-10-31 17:43:26.102004 |
| 4 | 위급 (`request_assistance`) | 2026-10-31 17:43:34.242662 |

위치 입력 revision1, 현재 상태 revision2가 저장됐다. 음성 출력은 사용자의 단말 청취 확인에 근거하며 서버는 안내 텍스트를 제공한다. 위 이력은 합성 시나리오의 실서버 연결 검증이다.

## 새 checkout 재현 검증

메인 커밋 `eaeef8756cd066518fb50bc634ff2a701c78a9f5`를 `origin/develop`에 정상 push한 뒤 별도 디렉터리에 실제 GitHub 원격을 `git clone --recurse-submodules --single-branch --branch develop`으로 받았다. `apps/mobile`이 `ed91b1ce78554e339e9a95bbc49a4028cc957178`로 자동 초기화됐고 메인과 앱 작업 트리가 모두 clean이었다.

`python3 tools/check_mobile_source.py`가 원본 checkout과 새 clone에서 모두 통과했다. API 계약 SHA256은 `323536c7322fcfea70d0853633731de09b19a37479370769a41e7a9e42b72062`, 앱 package-lock SHA256은 `08b60136671bfe60a1a9c04480da64e1d9b27c49a9107867219f4d390b2dbf65`다. 이후 메인 커밋은 이 검증 결과와 Loom 완료 기록을 추가한다.

## 다음 앱 버전 고정

앱 변경은 앱 저장소에서 구현·검증·커밋·원격 push를 끝낸 뒤 새 SHA를 메인 저장소에 반영한다. 서브모듈의 로컬 미커밋 내용을 메인 커밋이 저장해 주지 않는다.

```sh
git -C apps/mobile fetch origin develop
git -C apps/mobile checkout --detach VERIFIED_APP_COMMIT
git add apps/mobile
git diff --cached --submodule=log
```

`VERIFIED_APP_COMMIT`은 검증하고 원격에 게시한 전체 SHA로 바꾼다. 메인 커밋 이후 소스 검사와 새로운 checkout의 재귀 초기화를 확인하고 메인 `develop`을 일반 push한다. 서버 Python 이미지 빌드에서는 `.dockerignore`가 `apps/mobile`을 제외하므로 앱 의존성·빌드 산출물을 서버 이미지에 넣지 않는다.

## Verified Team Policies

No verified Team Policy Snapshot is active.

## Active Workflow Memory

No active workflow memory recorded.
