# Previous Results

## 1. 두 서버와 K8s 상태 점검 및 V2 실행 작업 등록

# 실행 결과

V2를 정본으로 실행 계획을 신규 Job 5개와 Task 24개에 등록했다. A0는 이번 점검 및 등록이고 후속 23개는 PENDING이며 Queue 또는 Worker를 시작하지 않았다. 기존 초기 문서화 Job과 HeoNey RUNNING Task는 변경하지 않았다. 앱팀에는 API 계약만 제공하고 앱 구현은 제외하도록 Job과 Task 계약에 명시했다.

클러스터는 노드 6대 Ready, API readyz 통과, 집계 시 Running 86개와 Succeeded 17개로 실행 중 준비되지 않은 컨테이너가 없었다. 모든 PVC 12개가 Bound였고 노드 압박 조건은 False였다. 마스터의 DNS nameserver 수 제한 경고는 A2 후속 점검에 포함했다. 단일 시점 사용량은 CPU 1~6%, 메모리 38~58%였다.

사용자의 명시적인 두 서버 로그인 승인을 받고 내부 상태 조회를 완료했다. GPU 서버는 4 vCPU, 약 47.05 GiB 메모리, NVIDIA L4 1대이며 GPU 메모리 사용 0 MiB, 드라이버 초기화와 장치 1대 인식에 성공했다. 일반 서버는 2 vCPU, 약 7.76 GiB 메모리이며 실패 서비스가 없다. 서버 간 SSH 포트는 양방향 연결됐다. 두 SSH 세션은 종료했다.

GPU 서버는 mlnx_interface_mgr@eth0와 nvidia-fabricmanager 실패로 시스템 상태가 degraded다. 부팅 당시 설정 파일 누락 및 NVSwitch 조회 실패 기록을 확인했으며 서비스 필요 여부와 영향은 A2에 연결했다. 두 서버의 기본 Python 환경에 주요 모델 패키지가 확인되지 않아 실행 환경 준비와 벤치마크를 D3에 연결했다. K8s에서 제공 서버로의 연결과 미래 API 포트는 미검증이며 A2의 후속 범위로 유지한다. 비밀번호 전송 승인 대기는 해소됐다.

## 산출물

- docs/V2/04-execution-backlog.md
- docs/V2/05-infrastructure-status.md
- V2 기준 원문 3개와 이를 필수 입력으로 참조하는 Loom 계약

## 검증

- loom validate --strict: 6 Jobs, 26 Tasks, 26 Task definitions 정합성 통과.
- 신규 Job 5개 및 Task 24개 실제 ID와 계획 매핑 일치.
- 모든 후속 Task가 PENDING이며 선행 조건 일치, 의존 그래프 순환 없음.
- 각 Task의 설명, 산출물, 완료 기준, 범위, 검증 항목 존재.
- 새 문서의 상대 경로 링크 검사 통과.
- 기존 HeoNey Task는 RUNNING 그대로 유지.
- 첫 등록 커밋의 284개 파일은 .loom 및 docs/V2 범위 안에 있었으며 문서 및 비밀정보 대입 패턴 검사를 통과했다.
- 서버 보고서 갱신 후 Loom strict, 작업 ID 및 의존관계, 23개 PENDING 유지, 새 문서 링크와 git diff --check 재검증 통과. 서버 자원의 바이트→GiB 환산도 재확인했다.

## 다음 행동

이번 Task의 검증과 커밋 후 완료 처리한다. 다음 준비 작업은 A1 범위 확정과 A2 종단간 환경 검증이다. 실제 데이터 수집, 모델 학습과 배포는 실행하지 않았으며 후속 23개 Task는 PENDING으로 유지한다.

## 3. 서버 간 통신과 클러스터 자원 및 운영 조건 검증

# 실행 결과

A2 환경 검증을 develop에서 수행하고 검증 결과와 미해결 운영 조건을 정리했다. 두 로컬 브랜치를 충돌 없이 fast-forward로 동기화하고 Loom required_branch를 develop으로 변경했다. 검증 완료는 전체 서비스가 준비됐다는 판정과 구분한다.

- 클러스터 6대 Ready, 실행 중 미준비 컨테이너 없음. 관찰한 컨테이너의 재시작 수 증가 없음.
- 6개 노드와 5개 워커 파드에서 제공 서버 두 대의 TCP 22 연결은 모두 실패했다. 사용자가 서로 다른 VPN이므로 예상된 상태라고 확인했다. A3에서 환경 간 연결 방법을 정하고 실제 API 인증과 전송을 시험해야 한다.
- 워커 5대의 일반 파드에서 내부 서비스 주소 응답 및 공공 도메인 3개의 DNS/TCP 443 성공. worker-04 파드에서 세 도메인의 TLS 인증서 검증과 HTTP 응답 확인.
- 마스터 DNSConfigForming의 원인은 resolver nameserver 4개와 적용 제한 3개로 확인했다. 최근 DNS 오류 표본은 0건이며 설정은 변경하지 않았다.
- 워커 합산 CPU 요청 여유 약 5.19 CPU, 최대 단일 워커 여유 1.375 CPU. 두 NFS 기반 파일시스템 available은 약 275.52/461.59 GiB이며 PVC별 합산 금지.
- GPU CUDA 컨텍스트 생성, 1 MiB 할당·쓰기·읽기 대조·반납 성공. Fabric Manager는 단일 L4에서 기본 CUDA 실패의 원인으로 관찰되지 않았고, Mellanox 보조 스크립트는 실제 netplan 구성과 기존 ifupdown 탐지 방식의 불일치로 실패하는 상태와 부합했다.
- 일반 서버는 A0에서 내부 조회를 완료했지만 이번 세션의 재인증은 성공하지 못했다. 현재 내부 재측정으로 보고하지 않는다. GPU→일반 서버 TCP 22는 성공했다. 인증정보는 저장하지 않았다.
- C4/D3/E2/A4는 계약 형식 검사만 통과했다. 실제 모델·명세·구현이 없으므로 기능 검증을 실행하지 않았고 미착수 사유를 각 Job 메모에 기록했다.

## 산출물

- docs/V2/delivery/environment-readiness.md
- docs/V2/delivery/environment-readiness-evidence.json
- docs/V2/04-execution-backlog.md 및 05-infrastructure-status.md의 후속 결과 연결

## 검증 근거

기존 파드의 제한된 네트워크 진단, 노드 경로 및 resolver 조회, node describe의 할당 요청량, kubelet 읽기 전용 파일시스템 통계, CUDA 드라이버 API 검사, 관찰 전후 노드와 파드 상태를 대조했다. 실제 내부 IP와 인증정보를 제외한 구조화된 근거를 보존했다. 외부 공개 문서의 서비스 필요성 설명은 실측 구성과 구분해 링크했다.

추가 로컬 검증: develop 브랜치와 Loom 정책 일치, 문서 링크, JSON 근거 개수 및 CPU 여유 합산값, 검증 대상 4개 PENDING 유지, git diff --check 및 loom validate --strict(6 Jobs/26 Tasks) 통과.

## 남은 조건과 다음 행동

A3에서 서로 다른 VPN 간 전송 경로와 실제 API 인증을 구성하고 검증해야 한다. 일반 서버 변경 전 정확한 자격 증명으로 재로그인 확인이 필요하다. 원본·학습 자료 보존 정책과 PVC 쓰기·복구, 모델 실행 환경 및 처리량은 후속 작업이다. 실패 서비스와 DNS 설정을 이번에 수정하지 않았다. 전체 기능 구현을 검증 요청에 포함된 것으로 확대하지 않았다.
