# 두 서버 Tailscale 연결 및 검증

검증일: 2026-10-31 11:24~11:38 KST. 실행 브랜치: `develop`. Loom A5: `task-20261031-022438-tailscale-6dc57118`.

## 결과

두 서버에 공식 Tailscale 1.104.4를 설치하고 사용자 제공 인증키로 기존 `tail2dac17.ts.net`에 등록했다. 두 서버 모두 `Running`, `Online=true`, health 경고 없음이며 `tailscaled`는 active/enabled다. 사용자 승인 후 최소 SSH 접근 규칙을 추가했고 **노트북의 Tailnet 주소 SSH 로그인, 클러스터 마스터에서 두 서버 TCP 22, 두 서버 상호 SSH 배너 수신**을 확인했다.

| 대상 | Tailscale IPv4 | 등록 이름 | 기존 사설 주소 |
| --- | --- | --- | --- |
| GPU | `100.65.45.63` | `inno-gpu-011.tail2dac17.ts.net` | `10.1.2.16` |
| 일반 서버 | `100.116.5.9` | `inno-server-011.tail2dac17.ts.net` | `10.1.1.16` |
| 기존 클러스터 마스터 | `100.104.111.111` | `k8s-master` | `192.168.0.14` |

일반 서버는 사용자가 정확한 비밀번호를 제공한 뒤 로그인에 성공했다. [A2 보고서](environment-readiness.md)의 인증 미완료는 당시 결과이며 현재 미해결 항목이 아니다.

**일반 워커와 수집 파드의 API 통신은 아직 구성 전이다.** 현재 프로젝트 파드와 API가 없으며, 이번 작업은 두 서버 등록과 기존 클러스터 연결 지점의 관리 접속을 확보했다. SSH 성공을 데이터 수집·모델 API 연결 완료로 해석하지 않는다.

## 설치와 운영 설정

- Ubuntu 24.04용 공식 stable 패키지 저장소와 서명 키를 등록하고 `tailscale` 패키지만 설치했다. 기존 패키지 업그레이드나 무관한 서비스 재시작은 하지 않았다. [공식 설치 경로](https://pkgs.tailscale.com/stable/#ubuntu-noble)
- `--hostname`은 각 서버의 기존 이름, `--accept-dns=false`, `--accept-routes=false`로 등록했다. Exit node·서브넷 광고·Tailscale SSH는 활성화하지 않았다.
- 인증키는 숨김 입력 후 표준 입력으로 CLI에 전달했다. 인증키 파일, 저장소, 셸 이력에 남기지 않았고 명령 인자에는 키 값 대신 입력 경로를 사용했다. 정상 동작에 필요한 장치 상태는 Tailscale 서비스가 관리한다.
- 기본 경로는 GPU `10.1.2.1`, 일반 서버 `10.1.1.1`의 기존 eth0 경로다. 기관 도메인 DNS 해석과 KOSIS HTTPS 인증서 검증이 두 서버에서 통과했다.
- 재부팅 자동 시작 설정은 확인했다. 실제 재부팅 시험은 하지 않았다.
- 장치 키 만료는 조회 시 두 서버 모두 **2027-04-29 11:29 KST경**이다. 무기한 접속을 보장하지 않으며 만료 전 재인증 또는 운영 정책을 정해야 한다. 서버 삭제·재등록으로 IP가 바뀌면 아래 IP 기반 규칙도 갱신한다.

접속 명령은 다음과 같다. 실행하는 장치가 Tailnet에 연결되어 있고 허용된 출발지여야 한다. DNS 수용을 끈 서버에서는 등록 이름 대신 IPv4 주소를 사용한다. 최초 호스트키는 관리 중인 기존 서버 키와 대조한다.

```sh
ssh ncloud@100.65.45.63
ssh ncloud@100.116.5.9
```

## 접근 정책

처음에는 두 서버의 유효 `PacketFilter`가 빈 배열이었다. Tailscale 자체 ping은 DERP(tok)를 통해 약 67~69 ms로 응답했지만 실제 TCP 22는 시간 초과였다. 두 서버의 UFW는 inactive, INPUT 기본 정책은 ACCEPT, `tailscale0` 수신 허용 및 SSH 리스닝을 확인했다. Tailscale 진단 ping과 실제 서비스 통신을 구분해야 한다. [공식 TCP 진단](https://tailscale.com/docs/reference/troubleshooting/network-configuration/tcp-connection-two-devices)

사용자가 저장 직전 승인한 아래 grant **1개를 기존 정책에 추가**했다. 브라우저의 저장 완료 화면과 서버에 배포된 TCP 22 필터, 실제 통신으로 적용을 확인했다. 기존 4개 규칙은 유지했다.

```json
{
  "src": ["100.104.111.111", "100.65.45.63", "100.116.5.9", "group:admin"],
  "dst": ["100.65.45.63", "100.116.5.9"],
  "ip": ["tcp:22"]
}
```

기존 관리자 그룹과 마스터에서 두 서버를 관리하고 두 서버 사이 SSH 연결을 허용하는 범위다. 클러스터 API·전체 포트·공개 인터넷 접근을 추가하지 않았다. 이 규칙은 IPv4 목적지 기준이다. 기존 SSH 계정 인증은 계속 필요하다.

## 실제 검증

| 출발 → 목적지 | 검사 및 결과 |
| --- | --- |
| 노트북 → GPU Tailnet IPv4 | 기존 VPN 주소에서 확인한 호스트키와 대조 후 실제 SSH 로그인 성공. `inno-gpu-011`, `ncloud` 확인 |
| 노트북 → 일반 서버 Tailnet IPv4 | 동일한 호스트키 대조 후 실제 SSH 로그인 성공. `inno-server-011`, `ncloud` 확인 |
| 클러스터 마스터 → 두 서버 Tailnet IPv4 | 마스터의 hostNetwork Flannel 컨테이너에서 TCP 22 각각 성공 |
| 일반 서버 → GPU Tailnet IPv4 | TCP 22 성공, OpenSSH 배너 수신 |
| GPU → 일반 서버 Tailnet IPv4 | TCP 22 성공, OpenSSH 배너 수신 |
| 워커 5대의 노드 네트워크 → 두 서버 | TCP 22 총 10건 실패. 워커에 해당 Tailscale 호스트 경로가 구성되지 않음 |
| 워커 5대의 일반 파드 → 두 서버 | TCP 22 총 10건 실패. 별도 프로젝트 egress 경로와 허용 정책 필요 |
| 기존 cody-stat Tailscale 사이드카 → 두 서버 | 등록 직후 Tailscale 진단 ping 응답 확인. TCP는 정책 적용 전 실패했고, 이 타 서비스에는 신규 접근 권한을 부여하지 않음 |

노드·일반 파드 22건의 실제 실행 결과는 [검증 근거](tailnet-connectivity-evidence.json)에 기록했다. 호스트와 서비스 주소는 구분했다. 일반 파드 시험은 다른 애플리케이션의 데이터를 읽거나 변경하지 않는 제한된 포트 연결 검사다.

기존 클러스터는 6개 노드 Ready, 실행 중 파드 84개 및 준비되지 않은 컨테이너 없음으로 확인했다. 두 서버의 기존 SSH 세션도 유지됐다. 일반 서버의 실패 서비스는 없고 GPU의 기존 실패 서비스 2개는 A2와 동일하다. 이번 설치로 해결했다고 처리하지 않는다.

## 일반 파드의 후속 연결: A3

현재 클러스터는 마스터의 호스트 Tailscale과 일부 서비스별 userspace 사이드카를 사용한다. Tailscale Operator는 설치되어 있지 않다. 따라서 서버를 Tailnet에 추가해도 워커와 모든 파드에 자동으로 연결 경로가 생기지는 않는다.

A3의 서비스 실행 기반 구성에서 다음을 함께 수행한다.

1. BONGHWAJIGI 수집 파드용 전용 Tailscale egress 또는 사이드카를 구성한다. 다른 서비스의 Tailscale 사이드카를 공용 출구로 사용하지 않는다. Operator 방식을 채택한다면 별도의 설치·인증 구성이 필요하다. [공식 Kubernetes egress 설명](https://tailscale.com/docs/kubernetes-operator/egress)
2. 수집 파드 → 일반 서버 이벤트 API, 일반 서버 → GPU 모델 API의 주소·포트·TLS·서비스 인증을 정한다. 프로젝트 전용 신원과 실제 서비스 포트에 한정해 접근 규칙을 추가한다.
3. 실제 배치한 파드에서 API 요청·응답, 거부되는 출발지, 재시작 후 재연결을 검증한다. 마스터에서 성공한 SSH 시험으로 대체하지 않는다.
4. 키 만료, 장치 교체, egress 장애 시 재시도 및 복구 절차를 운영 문서에 연결한다.

이번 설정을 되돌려야 한다면 추가한 grant를 제거하고, 기존 VPN 접속을 확보한 상태에서 대상 서버의 `tailscale down`을 수행한다. 다른 장치·접근 규칙은 변경하지 않는다. 패키지 삭제와 장치 등록 제거는 별도 정리 단계다.
