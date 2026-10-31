# 산불 MVP 일반 서버 운영과 접속

Loom `task-20261031-132925-mvp-1d561841`. 확정 단계는 **1 경고 → 2 대피 → 3 위급**이다. 일반 서버의 사설망 시연 배포이며 실제 예측 연결·실제 단말 푸시·HTTPS 도메인은 제외한다. 앱 저장소와 진행 중인 학습은 변경하지 않는다. 배포 검증 결과는 [검증 기록](mvp-server-evidence.json)에 기록한다.

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

## 남은 외부 연결 조건

- Firebase 프로젝트·서버 자격 파일·테스트 FCM 토큰이 없어 발신기는 simulation이다. `simulated`는 실제 발신/단말 수신이 아니다. 제공자 어댑터·재시도·만료·토큰 회전 검사는 구현했다.
- 실제 예측 연결은 사용자 지시로 제외했다. 모든 앱 예측은 unavailable/null이다.
- 도메인/HTTPS, 외부 로그인, 실제 모바일 기기, 실측 경계/도로 경로, 실제 K8s 수집은 검증하지 않았다. 기본 관련성은 공급된 시연 구역과 최신 GPS/정확도를 사용한다.
- 서버 음성과 3D는 제외한다. 119 신고를 자동으로 보내지 않는다. 단말의 TTS·지도 표시·전화/문자 화면 연결은 앱 소관이다.
