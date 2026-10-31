# 두 서버 SSH 접속 운영 기록

확인일: 2026-10-31 17:42~17:43 KST. Loom Task: `task-20261031-084138-ssh-b8d79a00`.

## 접속 방법

이 Mac의 `/Users/hongyongjae/.ssh/config`에 아래 별칭을 추가하고 두 서버에 실제 로그인했다. 접속 장치는 기존 Tailnet에 연결되어 있고 해당 서버의 TCP 22 접근이 허용되어야 한다.

```sh
ssh inno-gpu-011
ssh inno-server-011
```

`ssh bonghwajigi-gpu`, `ssh bonghwajigi-server`도 각각 같은 서버로 연결한다. 계정은 모두 `ncloud`, 포트는 `22`다. 현재 인증은 비밀번호 입력 방식이다. 비밀번호는 로그인 프롬프트에만 전달했으며 SSH 설정·저장소·작업 기록에 보관하지 않았다.

| 기본 별칭 | 보조 별칭 | Tailscale IPv4 | 설계상 책임 |
| --- | --- | --- | --- |
| `inno-gpu-011` | `bonghwajigi-gpu` | `100.65.45.63` | Qwen 생성·임베딩 API, 별도 일정의 XGBoost GPU 학습 |
| `inno-server-011` | `bonghwajigi-server` | `100.116.5.9` | API·DB·긴급/분석 큐·개인별 정책·알림·XGBoost CPU 추론 |

K8s는 자료 수집을 담당한다. 역할은 [서버 배치도](../02_실시간_서버_배치도.md)와 [구현 스택](implementation-stack.md)을 따르며, 이 접속 검증이 모델이나 서비스 배포 완료를 의미하지 않는다.

## 로컬 설정과 백업

기존 `bastion`, `tinypilot`, `station`, `nas` 설정을 보존했다. 두 신규 Host 블록에는 각각 대상 주소와 계정, `ConnectTimeout 10`, `ServerAliveInterval 30`, `ServerAliveCountMax 3`, `StrictHostKeyChecking yes`를 설정했다. SSH 키를 새로 만들거나 원격 인증 설정을 바꾸지 않았다.

기존 config는 root 소유였다. 사용자 소유 `.ssh` 디렉터리 안에 백업을 만들고 원자적으로 교체해 현재 config를 사용자 소유, 권한 `600`으로 맞췄다. 설정·known_hosts 및 두 백업의 권한을 모두 `600`으로 확인했다.

- 설정 백업: `/Users/hongyongjae/.ssh/config.backup-20261031T084237Z`
- 호스트 키 백업: `/Users/hongyongjae/.ssh/known_hosts.backup-20261031T084237Z`

두 서버의 현재 ED25519 공개 키가 이전 VPN 접속에서 확인해 둔 키와 일치했다. GPU의 Tailnet 주소는 기존 known_hosts에 있었으며 일반 서버의 Tailnet 주소만 대조 후 추가했다. 호스트 키 확인을 끄지 않고 두 실제 로그인을 수행했다.

확인한 공개 키 지문: `SHA256:Zm5aAv5DJ/EnKiObKSadOxA5nKuXgToCGhNiyhVhAjY`.

## 실제 로그인 결과

두 SSH 명령 모두 종료 코드 `0`이었다. 원격에서 호스트명·현재 계정·OS·자원을 읽기 전용으로 조회했다. GPU의 `nvidia-smi` 조회도 종료 코드 `0`이다.

| 확인 항목 | GPU 서버 | 일반 서버 |
| --- | --- | --- |
| 확인 시각 KST | 17:43:08 | 17:43:19 |
| 실제 호스트명 | `inno-gpu-011` | `inno-server-011` |
| 실제 계정 | `ncloud` | `ncloud` |
| OS | Ubuntu 24.04.1 LTS | Ubuntu 24.04.1 LTS |
| 커널 | `6.8.0-136-generic` | `6.8.0-136-generic` |
| vCPU | 4 | 2 |
| 전체 메모리 | 47.05 GiB | 7.76 GiB |
| 조회 시 사용 가능 메모리 | 45.72 GiB | 7.25 GiB |
| 루트 디스크 전체 / 여유 | 98.31 / 77.42 GiB | 98.31 / 90.39 GiB |
| Python | 3.12.3 | 3.12.3 |
| GPU | NVIDIA L4, 23,034 MiB | 이번 조회 대상 아님 |
| NVIDIA 드라이버 | 580.159.04 | 이번 조회 대상 아님 |

`ssh -G`로 기본·보조 별칭 네 개의 주소·계정·포트·엄격한 키 검사를 확인했다. 기존 별칭 네 개는 설정 전후에 동일한 `-F` 조건으로 유효 설정 전체를 비교해 일치했다.

## 이후 접근 시 참고

접속이 되지 않으면 먼저 현재 장치의 Tailnet 연결과 대상 서버의 온라인 상태, TCP 22 접근 권한을 확인한다. 호스트 키 불일치가 나타나면 관리 중인 서버 키와 다시 대조한다. 기존 키를 무조건 삭제하거나 검사를 끄지 않는다.

기존 [Tailscale 연결 기록](tailnet-connectivity.md)의 접근 범위와 장치 키 만료 조건을 함께 따른다. 일반 수집 파드의 전용 연결 경로와 실제 API 포트·TLS·인증은 A3의 후속 구현 대상이다. 이번에는 로컬 관리 접속만 설정했으며 모델 설치·학습·서비스 배포는 수행하지 않았다.
