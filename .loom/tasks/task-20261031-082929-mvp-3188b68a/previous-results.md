# Previous Results

1 older recorded result(s) were omitted. Promote durable context to Job Notes or explicit Context References.

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

## 6. 두 제공 서버를 기존 Tailscale 망에 연결하고 클러스터 통신 검증

# 결과

develop에서 두 제공 서버에 공식 Tailscale 1.104.4를 설치하고 기존 tail2dac17.ts.net 등록을 완료했다. GPU는 100.65.45.63, 일반 서버는 100.116.5.9이며 두 장치 모두 Running, Online, health 경고 없음, 서비스 active/enabled다.

사용자가 정확한 일반 서버 자격 증명을 제공해 로그인에 성공했다. 별도로 저장 직전 승인한 접근 규칙 1개를 추가했다. 기존 관리자 그룹, 클러스터 마스터와 두 서버를 출발지로 하고 두 서버 IPv4의 TCP 22만 허용한다. 기존 정책 4개를 유지했다.

## 검증 근거

- Tailnet IPv4로 두 서버에 실제 SSH 로그인해 hostname과 ncloud 사용자를 확인했다. 기존 VPN 접속에서 확인한 호스트키와 대조했다.
- 클러스터 마스터의 노드 네트워크에서 두 서버 TCP 22 각각 성공했다.
- 두 서버 상호 TCP 22와 OpenSSH 배너 수신이 성공했다.
- 노드·일반 파드 22건 검사에서 마스터 2건 성공, 워커 노드 10건 및 일반 파드 10건 실패를 기록했다.
- 기존 클러스터는 6대 Ready, 실행 파드 84개 모두 준비 상태다. 서버 기본 경로와 기관 DNS·HTTPS 동작을 유지했고 일반 서버 실패 서비스는 없다. GPU의 기존 실패 서비스 2개는 동일하다.
- 인증키와 비밀번호를 저장소·보고서에 기록하지 않았다. 실제 검사 근거와 운영 범위는 docs/V2/delivery/tailnet-connectivity.md 및 evidence JSON에 남겼다.

## 남은 조건과 다음 행동

이 Task의 두 서버 등록 및 기존 클러스터 연결 지점 검증은 완료했다. 일반 수집 파드는 전용 Tailscale egress 또는 사이드카와 프로젝트 접근 정책이 필요하다. A3에서 API 주소·포트·TLS·서비스 인증을 정한 뒤 실제 수집 파드 → 일반 서버, 일반 서버 → GPU API를 검증한다. SSH 검사로 미구현 API를 통과 처리하지 않는다.

장치 키는 조회 시 2027-04-29 만료이며 갱신 정책이 필요하다. 재부팅 자동 시작 설정만 확인했고 실제 재부팅은 하지 않았다. 기존 HeoNey 문서화 RUNNING Task와 다른 22개 PENDING Task는 실행하지 않았다.
