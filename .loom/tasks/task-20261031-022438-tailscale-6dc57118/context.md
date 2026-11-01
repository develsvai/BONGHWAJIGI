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
- Goal: V2를 설계 기준으로 MVP 범위와 실행 환경을 고정하고, 다중 출처 수집부터 개인별 안내까지 통합 검증한다. HeoNey는 참고이며 앱 구현은 제외하고 API 명세를 제공한다.
- Branch: HeoNey
- Task count: `6`

## Task

- Title: 두 제공 서버를 기존 Tailscale 망에 연결하고 클러스터 통신 검증
- Description: 사용자가 제공한 인증키로 두 서버에 Tailscale을 설정하고 기존 클러스터 tailnet과 연결하도록 직접 지시했다. develop에서 설치 등록과 실제 통신을 확인하고 접속 주소와 운영 방법을 기록한다.
- Expected output: 두 서버의 Tailscale 등록 및 연결 결과, 클러스터에서의 실제 통신 근거, docs/V2/delivery/tailnet-connectivity.md
- Done condition: 두 서버가 의도한 tailnet에 연결되고 기존 클러스터의 Tailscale 연결 지점에서 두 서버로 통신이 검증되며 일반 파드의 접근 경로와 남은 서비스 포트 조건이 구분되어 기록된다.
- In scope: 두 서버의 Tailscale 공식 패키지 설치와 사용자 제공 키 인증; 기존 클러스터 Tailscale 구성 조회; 필요한 최소 연결 구성; 노드 및 파드 통신 시험; 문서 및 Loom 기록과 로컬 커밋
- Out of scope: 모델 및 앱 기능 구현; 무관한 서비스 재시작; 기존 전체 네트워크 기본 경로 변경; 공개 인터넷 서비스 개방; 인증키 또는 비밀번호의 저장소 기록; 무관한 계정이나 비밀정보 조회
- Validation hint: Tailscale 상태와 tailnet 일치, 양방향 SSH 포트 및 클러스터 접근 시험, 기존 경로와 서비스 정상 유지, 키 비노출 확인, Loom strict 검증
- Required docs: `docs/V2/delivery/environment-readiness.md`
- Memory refs: -
- Document outputs: `docs/V2/delivery/tailnet-connectivity.md`
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

## Context References

No explicit context references recorded for this job.

## Required Documents and Memory

### required-doc: docs/V2/delivery/environment-readiness.md

- Path: `docs/V2/delivery/environment-readiness.md`
- Status: present

# 실행 환경 검증 결과

검증일: 2026-10-31, 한국 시간 10:20~10:32. 실행 브랜치: `develop`. Loom Task: `task-20261031-002627-task-5ce3742e` (A2).

## 판정

환경 검증과 미해결 조건 정리는 완료했다. **현재 배치안의 전체 통신이 준비됐다는 뜻은 아니다.** 클러스터의 수집·소규모 평가용 자원과 외부 기관 접속, GPU의 기본 CUDA 동작은 확인했다. 클러스터와 제공 서버 사이의 전송 경로는 별도로 구성해야 한다.

사용자가 두 환경은 서로 다른 VPN이며 직접 접속되지 않는 것이 맞다고 확인했다. 따라서 아래 연결 실패는 고장으로 단정하지 않고, A3에서 해결해야 할 연결 설계 조건으로 분류한다.

| 검증 항목 | 결과 | 의미 및 다음 조건 |
| --- | --- | --- |
| K8s 노드·파드·API 상태 | 통과 | 6대 Ready, 실행 중 준비되지 않은 컨테이너 없음, API readyz 정상 |
| 노드 및 파드 → 제공 서버 | 연결 실패 확인 | 6개 노드와 5개 워커의 일반 파드에서 두 서버 TCP 22 모두 시간 초과. 서로 다른 VPN 간 경로 필요 |
| 파드 → 기관 도메인 | 통과 | 5개 워커에서 3개 도메인 DNS·TCP 443 성공. 1개 파드에서 TLS 검증과 HTTP 응답 확인 |
| 내부 서비스 DNS | 통과 | 5개 워커 파드에서 Kubernetes 서비스의 실제 주소 응답 확인 |
| 마스터 DNS 경고 | 원인 확인, 정리 필요 | 노드 resolver에 DNS 서버 4개, kubelet 경고에서 3개만 적용. 이번 시험에서 DNS 장애는 관찰되지 않음 |
| GPU 드라이버·메모리 | 통과 | CUDA 컨텍스트 생성, 1 MiB 할당·쓰기·읽기 대조·반납 성공 |
| GPU 실패 서비스 2개 | 원인 및 현재 영향 조사 | 기본 CUDA 및 현재 네트워크 동작은 정상. 서비스 상태 정리는 별도 변경 작업 |
| 일반 서버 재접속 | 이번 세션 인증 미완료 | 이미지 자격 증명의 판독·인증에 실패해 내부 재조회는 못 함. 09:48 A0 실측과 현재 GPU→일반 서버 TCP 연결 결과를 구분하여 사용 |
| 모델·API·통합 기능 | 검증 대상 미구현 | 학습 결과, 공통 데이터 계약, 대응 정책, API와 통합 구현이 아직 없음 |

이번에 설치, 배포, 서비스 재시작, VPN·DNS·방화벽 변경은 하지 않았다. 기존 파드에서는 제한된 네트워크 진단만 실행했으며, 애플리케이션 데이터·Secret·환경변수를 조회하지 않았다. SSH 세션은 모두 종료했다.

## 브랜치 동기화

원격 최신 상태 조회 당시 `develop`은 `HeoNey`의 조상이었고, `HeoNey`에만 6개 커밋이 있었다. 진행 중 검증 기록과 사용자 브랜치 지시를 커밋한 뒤 `develop`을 fast-forward했다. 검증 재개 시 두 로컬 브랜치는 `f59e0c3`으로 같았다. Loom의 `required_branch`도 CLI로 `develop`으로 변경했다.

이후 검증은 `develop`에서 수행했다. 기존 이력은 보존했고 강제 갱신이나 원격 push는 수행하지 않았다. Job에 남아 있는 과거 `HeoNey` 기록은 생성 당시 이력이며 현재 실행 정책은 `develop`이다.

## 통신 방향과 확인 범위

| 출발 → 목적지 | 시험 | 결과 |
| --- | --- | --- |
| 클러스터 6개 노드 → 일반·GPU 서버 | 각 서버 TCP 22, 3초 연결 제한 | 12건 모두 실패. 표본 재검사에서 시간 초과 원문 확인 |
| 워커 5대의 일반 파드 → 일반·GPU 서버 | 각 서버 TCP 22, 3초 연결 제한 | 10건 모두 실패 |
| GPU → 일반 서버 | TCP 22 | 성공, 단일 측정 약 2 ms |
| 제공 서버 상호 SSH 포트 | A0의 09시대 양방향 검사 | 양방향 성공. 이번 A2에서 일반 서버발 재검사는 못 했음 |
| 5개 워커 파드 → 기관 도메인 | DNS·TCP 443 | `apis.data.go.kr`, `kosis.kr`, `apihub.kma.go.kr` 모두 성공 |
| worker-04 파드 → 위 3개 HTTPS 루트 | 인증서 검증을 유지한 HTTP 요청 | TLS 검증값 모두 0. 응답은 순서대로 400 / 302 / 200 |
| GPU → 기관·패키지 도메인 | TLS 핸드셰이크 | 위 기관 3개 및 `huggingface.co`, `pypi.org` 성공 |

기관 루트 URL의 400·302 응답도 HTTPS 서버까지 도달했다는 근거다. 실제 데이터 API의 인증·쿼터·샘플 확보 성공을 뜻하지 않으며 그것은 B1의 범위다. 설치나 모델 다운로드는 하지 않았다.

노드의 제공 서버 목적지 경로는 일반 LAN 게이트웨이였다. 마스터에는 Tailscale 경로가 있으나 조회된 라우팅 테이블에서 제공 서버 대역의 전용 경로는 확인되지 않았다. 워커에서도 해당 대역 또는 별도 터널 경로가 확인되지 않았다. 일반 파드는 각 노드의 CNI 게이트웨이를 사용한다. 노트북의 VPN 연결이 자동으로 이 경로를 제공하지는 않는다.

A3에서는 두 환경 사이의 허용된 전송 경로, 목적지 서비스 주소·포트, 인증과 TLS를 먼저 확정해야 한다. 경로가 준비된 뒤 **실제 수집 파드 → 일반 서버 이벤트 API**, **일반 서버 → GPU API**를 다시 시험한다. 현재 API는 배포되지 않았으므로 SSH 포트 검사로 API 통신을 통과 처리하지 않는다.

일반 서버의 이번 SSH 인증 실패는 클러스터의 VPN 분리와 별개의 결과다. 이전 A0에서 로그인하여 확인한 사양·디스크 값은 [직전 점검 보고서](../05-infrastructure-status.md)에 남아 있다. 이번 인증 실패를 비밀번호 변경이나 서버 장애로 단정하지 않는다. 일반 서버 설치·변경 작업 전에는 정확한 자격 증명으로 재접속을 확인해야 한다.

## 클러스터 배치 용량

다음 값은 10:24경 `kubectl describe node`의 요청 자원 집계와 kubelet 파일시스템 통계다. 메모리 여유는 **할당 가능량에서 이미 예약된 요청량을 뺀 값**이며 실제 남은 RAM과 다르다.

| 워커 | 기존 CPU 요청 | CPU 요청 추가 여유 | 메모리 요청 추가 여유 | 노드 디스크 available |
| --- | ---: | ---: | ---: | ---: |
| worker-01 | 1,225m | 775m | 약 5.37 GiB | 약 53.67 GiB |
| worker-02 | 1,000m | 1,000m | 약 6.26 GiB | 약 58.79 GiB |
| worker-03 | 1,050m | 950m | 약 6.17 GiB | 약 64.55 GiB |
| worker-04 | 625m | 1,375m | 약 6.45 GiB | 약 68.70 GiB |
| worker-05 | 910m | 1,090m | 약 6.24 GiB | 약 66.95 GiB |

워커 합산 CPU 요청 여유는 약 5.19 CPU다. 그러나 단일 파드는 한 노드에 배치되므로, 현재 요청량 기준으로 2 CPU를 요청하는 단일 파드는 어느 워커에도 들어가지 않는다. 500m CPU·512 MiB 수준의 작은 수집 파드는 요청량만 비교하면 다섯 워커 모두 후보가 된다. 실제 배치에는 affinity·네트워크 정책·스토리지 및 이후 자원 변동을 함께 확인해야 한다.

워커의 실제 사용량은 CPU 약 2~4%, 메모리 약 38~54%였다. CPU limits 합계는 노드별 약 117~350%로 이미 초과 할당되어 있다. 따라서 요청 여유를 모든 작업의 동시 최대 처리량으로 해석하지 않는다. 큰 전처리·평가 작업은 동시성을 제한하고 A3에서 실제 requests/limits를 정한다.

마스터에는 control-plane `NoSchedule` taint가 있어 일반 프로젝트 작업의 여유 용량 계산에서 제외했다. 프로젝트 네임스페이스는 아직 없고 기존 portfolio 전용 ResourceQuota/LimitRange를 이 프로젝트의 제한으로 해석하지 않았다.

## 스토리지

PVC 12개는 NFS 기반이다. 여러 PVC에서 같은 수치가 관찰된 것은 공유된 기반 파일시스템을 보고하기 때문이며 합산하면 안 된다.

| 저장소 | 관찰된 기반 파일시스템 용량 | available | 정책 |
| --- | ---: | ---: | --- |
| nfs-storage | 약 294.73 GiB | 약 275.52 GiB | Retain, 삭제 시 보관 설정 |
| nfs-bulk | 약 491.08 GiB | 약 461.59 GiB | Delete, archiveOnDelete=false |
| local-path | 노드별 위 표 참고 | 노드별로 다름 | 기본 클래스, WaitForFirstConsumer, Delete |

클래스별 수치는 마운트된 PVC의 kubelet 통계와 PV의 NFS 기반 경로를 대조했다. PVC 선언 크기를 넘는 공간의 사용 권한이나 개별 quota를 보장하지 않는다. I/O 부하 시험과 새 PVC 생성·쓰기·복구는 수행하지 않았다. 중요한 학습 자료 및 원본 보관은 A3에서 보존 정책·백업·복구를 명시하고 사용할 클래스를 선택한다.

GPU 서버의 루트 파일시스템은 이번 재조회에서 available 약 77.52 GiB, inode 사용률 4%였다. 일반 서버의 available 약 90.50 GiB는 09:48 A0 측정값으로 이번 재측정값이 아니다.

## DNS 경고와 과거 재시작

마스터의 kubelet `resolvConf`는 `/run/systemd/resolve/resolv.conf`를 가리키고, 해당 파일에는 Tailscale IPv4·IPv6와 공용 DNS 두 개로 총 네 개의 nameserver가 있었다. `DNSConfigForming` 이벤트는 세 개만 적용하고 나머지를 생략했다고 보고했다. 두 CoreDNS 파드는 마스터에 있고 `dnsPolicy: Default`, Corefile은 `/etc/resolv.conf`로 외부 질의를 전달한다.

Kubernetes 공식 문서도 nameserver 수 제한과 노드 resolver 설정을 DNS 점검 항목으로 설명한다. 이번 원인 확인은 그 설명과 실제 파일·이벤트를 대조한 결과다. [Kubernetes DNS 진단 문서](https://kubernetes.io/docs/tasks/administer-cluster/dns-debugging-resolution/)

다섯 워커 파드에서 내부 Kubernetes 서비스 주소 응답, 기관 도메인 DNS 및 TCP 연결이 모두 성공했다. 검사 시점의 CoreDNS 최근 5분 로그 표본은 각각 655줄·1,316줄이었고 `[ERROR]` 또는 `SERVFAIL`은 0건이었다. 이는 단일 검사 구간의 결과이며 향후 DNS 전환·장애 시 정상 동작을 보장하지 않는다. resolver 정리 시 Tailscale 이름 해석을 유지해야 하므로 이번에는 변경하지 않았다.

높은 재시작 횟수는 현재 반복 장애와 구분했다. Harbor DB의 마지막 종료는 8월 5일 UTC, 주요 MetalLB 및 node exporter는 6월 3일 UTC였다. 이번 관찰 전후 재시작 수가 있는 컨테이너들의 횟수 변화는 없었고 종료 시점에도 실행 중 미준비 컨테이너가 없었다.

## GPU 실패 서비스와 실제 동작

### CUDA 검사

NVIDIA 드라이버 API로 아래를 실행했고 모두 반환값 0이었다.

1. 초기화 및 장치 1대 조회.
2. CUDA 컨텍스트 생성.
3. 장치 메모리 1 MiB 할당.
4. 지정한 바이트 패턴 쓰기 및 16바이트를 호스트로 읽어 일치 확인.
5. 할당 메모리 반납 및 컨텍스트 종료.

종료 후 GPU 메모리 사용량 0 MiB, 사용률 0%였다. 이 검사는 기본 드라이버·메모리 경로 검사이며 모델 추론, 연산 커널 성능, 장시간 안정성 또는 Qwen 동시 처리량 시험은 아니다.

### nvidia-fabricmanager

실측 PCI 장치와 토폴로지에는 L4 한 대만 확인됐고 NVLink 연결은 표시되지 않았다. Fabric Manager는 masked/failed 상태지만 위 CUDA 검사는 통과했다. NVIDIA 문서에서 Fabric Manager는 NVSwitch 기반 시스템의 fabric을 관리하며, 단일 GPU 구성에서는 필요하지 않다고 설명한다. 이를 실측 구성과 대조하면 이 상태를 단일 L4의 기본 CUDA 사용 불가로 볼 근거는 없다. [NVIDIA Fabric Manager](https://docs.nvidia.com/hgx-platforms/fabric-manager-user-guide/index.html), [NVIDIA 단일 GPU 전제 조건 설명](https://docs.nvidia.com/vss/latest/prerequisites.html)

서비스의 실패 기록을 지우거나 unmask·재시작하지 않았다. 이미지 기본 구성의 정리는 A3에서 필요성을 검토한다.

### mlnx_interface_mgr@eth0

현재 eth0은 Mellanox mlx5 드라이버를 사용하며 systemd-networkd와 netplan이 DHCP로 구성한 `routable (configured)` 상태였다. 일반 서버 TCP 연결과 외부 TLS 연결도 성공했다.

설치된 `/bin/mlnx_interface_mgr.sh`는 `/sbin/ifup`이 없을 때만 netplan 경로로 분기한다. 이 서버는 ifup과 netplan이 함께 있고 `/etc/network/interfaces`는 없어, 기존 ifupdown 설정을 찾다가 실패한 로그와 일치한다. 따라서 현재 관찰된 실패는 실제 링크 단절보다 관리 방식 불일치와 부합한다. 드라이버·패키지 제거, 네트워크 재시작 및 설정 수정은 수행하지 않았다.

## 다른 검증 Task의 실행 조건

아래 네 작업 모두 Loom 계약 형식 검사는 통과했지만 실제 검증 입력이 아직 없다. 계약 검증의 OK를 기능 검증 통과로 취급하지 않았다. 실행 지시와 미착수 사유는 각 Job의 해당 Task 메모에 기록했다.

| Task | 실제 검증에 필요한 선행 산출물 | 이번 상태 |
| --- | --- | --- |
| C4 모델 독립 평가·확률 보정 | C3 학습 결과와 분리된 평가 자료 | PENDING, 모델과 평가 입력 없음 |
| D3 Qwen 추출·설명·성능 검증 | B2 데이터 계약, D1 대응 정책, A2 환경 결과 | PENDING, 데이터 계약·정책 및 모델 실행 환경 없음 |
| E2 API 계약 호환 검증 | E1 OpenAPI, D5 안내 갱신 구현, D6 선택 기능 결정 | PENDING, 명세 및 구현 없음 |
| A4 과거 재난 통합 수용 검증 | B5 관련성, C5 모델 운영, D5 갱신, E2 계약 결과 | PENDING, 통합 대상 없음 |

검증만 요청받은 이번 작업에서 미구현 전체 서비스를 새로 개발하거나 모의 결과를 실제 검증으로 대체하지 않았다. 다음 실행은 A1 범위 확정과 B1 실제 데이터 확보를 거쳐 필요한 구현·계약을 준비하는 순서다. A3에서는 서로 다른 VPN 간 전송 방법을 먼저 확정한다.

## 근거와 재검증

- [직전 상태 보고서](../05-infrastructure-status.md): A0의 서버 로그인·사양 및 클러스터 상태.
- [전체 작업 계약](../04-execution-backlog.md): Task ID, 산출물, 완료 기준과 의존관계.
- [구조화된 검증 결과](environment-readiness-evidence.json): 자격 증명과 실제 내부 IP를 제외한 검사 집계.
- 재검증 방법: 기존 노드·파드의 읽기 전용 경로 조회 및 목적지 TCP 검사, DNS 실제 응답 대조, 인증서 검증을 유지한 HTTPS 요청, 노드 요청량과 kubelet 통계 비교, GPU 드라이버 메모리 검사.
- 전체 서비스 준비 완료 판정에는 연결 경로 구성 후 실제 API 인증·통신, 일반 서버 재로그인, 런타임 설치, 모델 성능, 저장소 쓰기·복구와 종단간 시연 결과가 추가로 필요하다.

## Verified Team Policies

No verified Team Policy Snapshot is active.

## Active Workflow Memory

No active workflow memory recorded.
