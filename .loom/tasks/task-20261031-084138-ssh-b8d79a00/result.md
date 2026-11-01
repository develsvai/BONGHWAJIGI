# 실행 결과

사용자의 직접 요청에 따라 이 Mac의 ~/.ssh/config에 inno-gpu-011 및 inno-server-011 별칭을 추가했다. 보조 별칭 bonghwajigi-gpu와 bonghwajigi-server도 제공한다. 기존 네 개 Host 항목과 연결 설정은 보존했다.

두 별칭으로 ncloud 계정의 실제 SSH 로그인이 성공했고 종료 코드 0이었다. GPU는 2026-10-31 17:43:08 KST, 일반 서버는 17:43:19 KST에 호스트명과 자원을 확인했다. GPU 서버의 L4 1대·4 vCPU·47.05 GiB와 일반 서버의 2 vCPU·7.76 GiB가 기존 환경 문서와 일치한다.

## 검증 근거

- 기존 VPN 접속에서 보관한 ED25519 키와 현재 두 서버의 공개 키가 일치했다. 일반 서버 Tailnet 주소만 known_hosts에 추가하고 엄격한 키 검사로 로그인했다.
- ssh -G로 기본·보조 별칭 네 개의 주소·계정·포트·StrictHostKeyChecking을 확인했다.
- 기존 네 별칭은 동일한 -F 조건으로 설정 전후 유효 설정 전체가 같았다.
- 로컬 config·known_hosts와 각각의 백업은 권한 600이다. config는 사용자 소유로 원자적으로 교체했다.
- 두 원격 조회 및 GPU nvidia-smi의 종료 코드가 모두 0이다. 실제 사양·시각·절차는 docs/V2/delivery/ssh-access.md에 기록했다.
- 비밀번호는 숨김 인증 입력에만 사용했으며 설정·저장소·작업 기록에 보관하지 않았다.
- loom task validate task-20261031-084138-ssh-b8d79a00 --strict: OK.
- loom validate --strict: 6 Jobs, 31 Tasks, 31 Task definitions 정상.
- git diff --check: 통과.

## 범위와 다음 행동

현재 비밀번호 입력 방식이며 원격 인증 설정은 변경하지 않았다. 서버 배치 역할을 기존 설계와 대조했고 모델 설치·학습·API 배포는 수행하지 않았다. 관리 SSH 연결 성공과 수집 파드의 API 연결 검증은 별개이며 후자는 A3에서 수행한다. 다른 구현 Task와 Queue는 시작하지 않았다.
