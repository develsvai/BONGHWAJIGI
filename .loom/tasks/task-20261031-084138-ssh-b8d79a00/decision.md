# 결정 기록

- 사용자가 지정한 서버 이름을 기본 SSH 별칭으로 삼고 프로젝트 보조 별칭을 추가했다. 기존 Tailnet IPv4에 직접 연결하며 ProxyJump는 추가하지 않았다.
- 기존 설정과 known_hosts를 각각 권한 600의 파일로 백업했다. root 소유 config는 사용자 소유 디렉터리에서 안전하게 원자 교체해 사용자 소유·600으로 맞췄다.
- 기존에 확인한 호스트 키와 현재 키를 대조하고 StrictHostKeyChecking yes를 적용했다. 비밀번호는 OpenSSH 설정에 저장하지 않고 인증 프롬프트에만 전달했다.
- 지속 접근에 필요한 별칭과 절차를 문서화했다. 사용자 요청 범위를 넘어 SSH 키 생성·원격 authorized_keys·서비스 설치·네트워크 정책은 변경하지 않았다.
- 적용할 Verified Team Policy Snapshot은 없다. 직접 실행 요청과 기존 A Job의 관리 접속 후속 작업 범위에 따라 실행했다.
