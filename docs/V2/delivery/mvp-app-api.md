# 산불 MVP 앱 API 실행 계약

2026-10-31, Loom Task `task-20261031-132925-api-181c0498`. 사용자 확정 단계는 **경고·대피·위급**이며 [정책 기준](response-policy.md)을 따른다. 실제 사설망 접속·계정 발급·배포 결과는 [서버 운영 문서](mvp-server-runbook.md)를 따른다. 앱 저장소는 변경하지 않았다.

## 버전과 인계

실행 계약은 **0.2.0-mvp**다. 종전 `api/openapi.yaml`의 0.1.0-draft는 구현 이전 화면 계약이며 그대로 보존했다. 현재 상태 입력·3단계·모의 전송·예측 제외를 반영한 실행 API는 [현재 OpenAPI](api/mvp-openapi.json)와 서버 `/openapi.json`이다. 0.1 응답 타입을 그대로 서버 완료본으로 사용하지 않는다.

모든 `/v1` 요청에 해당 사용자의 `Authorization: Bearer <access_token>`을 보낸다. 공통 응답은 `meta`와 `data`다. `meta`에는 schema_version, simulation, request_id, generated_at, data_status가 있다. 내부 `/internal/v1`은 다른 서비스 토큰을 사용하며 앱에 서비스 토큰이나 JWT 서명키를 넣지 않는다.

개인 안내는 `data.id`, `data.revision`, `data.pending_update`, `data.content`로 제공한다. `content.personal_response`에 level/number/label/policy_version, `content.actions`에 번호별 행동, `content.official_alerts`에 기관 원문이 있다. `content.prediction`은 항상 unavailable/null이고 실제 예측 모델을 호출하지 않는다. 현재와 과거 snapshot, 최종 확인과 갱신 대기를 구분한다.

## 앱 초기화와 갱신

1. 개발 계정의 사용자 JWT로 `GET /v1/app-config`를 확인한다. 서버 정책과 기능 상태를 따른다.
2. `PUT /v1/me/devices/{installation_id}`로 설치를 등록한다. 푸시 권한이 없어도 token=null로 설치 등록 후 위치를 보낼 수 있다. APNs 직결은 제공하지 않고 FCM 토큰만 받는다.
3. `GET/PUT /v1/me/profile`, `GET/PUT /v1/me/preferences`로 설정한다. 쓰기는 base_revision을 사용한다. 프로필은 전체 스냅샷이며 빠진 값은 unknown/빈 목록이다.
4. `PUT /v1/me/location`으로 fix_id·설치 ID·좌표·정확도·captured_at을 보낸다. 위치 유효기간은 5분이고 역순·미래·만료 관측을 거부한다. 지원 위도는 -85~85도다.
5. `GET /v1/home`, `/v1/disasters`, `/v1/me/alerts`를 조회한다. 원문은 Qwen이나 개인 정책 완료를 기다리지 않는다. 자료가 없거나 관련성이 불명확하면 안전하다고 표시하지 않는다.
6. 사건/경보의 response_id로 `GET /v1/me/responses/{response_id}`를 조회한다. 평가 대기 때 옛 행동·단계를 최신으로 쓰지 않고 `last_known_response`와 구분한다.
7. `GET /v1/me/updates?cursor=...&wait_seconds=25`로 전경 갱신한다. 변경 리소스를 다시 조회하고 같은 리소스의 낮은 revision을 버린다. cursor 만료(410)는 전체 동기화, 사용자 불일치/위조(400)는 cursor 초기화다. cursor를 access_token으로 쓸 수 없다.

`PUT /v1/me/profile`은 선택적인 `Idempotency-Key` 헤더를 지원한다. 위치는 fix_id가 멱등 키다. 같은 키의 다른 본문은 409다. 삭제한 위치를 옛 fix로 되살리지 않는다. DELETE 프로필/위치는 저장값과 관련 멱등 본문을 지우고 재평가를 요청한다.

## 현재 상태와 접근 제한

`PUT /v1/me/responses/{response_id}/context`는 base_revision·observed_at·confirmation=user_confirmed와 `state`를 받는다. state의 후보는 helper_present, can_move, injured, observed_hazard(unknown/none/smoke/flames/fear/trapped), location_type, evacuation_status, deescalation_confirmed다. 유효기간 5분인 현재 관측으로만 적용하고 사전 프로필을 덮어쓰지 않는다.

기존 overrides의 mobility와 alone_now도 받는다. 조력자가 단지 등록돼 있다는 사실을 곁에 있음으로 해석하지 않는다. 클라이언트는 route_status나 H구간을 공식 판단 값으로 등록할 수 없다. 해당 입력은 출처를 확인하는 내부 API 소관이다.

JWT는 고정 HS256, 별도 서명키, issuer/audience/만료/발급·유효 시각/사용자·시나리오·token_version을 검사한다. DB 계정이 비활성이거나 로그아웃한 토큰은 거부한다. 다른 사용자의 response ID와 경보 ID는 404이며 cursor도 사용자/시나리오에 묶인다. 로그인 제공자 연동은 제공하지 않고 이번 사설망 시연 계정은 관리 도구로 발급한다.

## 알림과 수신 확인

`GET /v1/me/deliveries`에서 모의 발신·재시도·실패·만료를 조회한다. 사용자 선택에 따라 현재 발신기는 simulation이다. 푸시 토큰은 응답과 로그에 출력하지 않는다. 토큰 회전·기기 해제 후 이전 기기 revision 작업을 전송하지 않는다. preferences.notifications_enabled=false는 백그라운드 알림만 끄고 전경 갱신은 유지한다.

`POST /v1/me/alerts/{alert_id}/receipts`는 alert_revision, installation_id, event(received/displayed/opened), occurred_at을 받는다. 중복을 저장 규칙으로 합치고 의미는 항상 client_reported_only다. 제공자 수락, 단말 보고, 사람이 열람한 기록, 119 접수는 서로 다르다.

`POST /v1/me/logout`은 사용자 토큰 버전을 바꾸고 모든 설치의 토큰을 지운다. 재로그인은 관리 도구로 새 계정 토큰을 발급받는다.

## 제공 경로와 제외 기능

| 경로 | 동작 |
| --- | --- |
| `/v1/app-config` | 3단계와 실제 기능 상태 |
| `/v1/me/profile`, `/preferences`, `/location` | 자기 자료 조회·수정, 프로필/위치 삭제 |
| `/v1/me/devices/{installation_id}` | 설치 등록·회전·해제 |
| `/v1/home`, `/v1/disasters` | 시나리오 범위의 관련 사건과 기본 지침. 관련 구역을 모르면 unknown |
| `/v1/me/alerts`, `/{alert_id}`, `/{alert_id}/receipts` | 독립 공식 원문·수신 보고 |
| `/v1/me/responses/{response_id}`, `/context`, `/history` | 최신 계획·현재 관측·과거 기록 |
| `/v1/me/updates`, `/v1/me/deliveries`, `/v1/me/logout` | 전경 갱신·전달 상태·로그아웃 |
| `/v1/safety-rules/wildfire` | DB의 검토된 국내 기본 수칙 |
| `/v1/me/responses/{response_id}/route` | 검증된 경로 도형이 없어 unavailable, route=null |
| `/support-drafts` | 서버 대기 없이 단말에서 작성해야 하므로 비활성(503) |
| `/voice-turns`와 하위 조회/삭제 | 서버 음성 제외, 비활성(503) |

서버는 텍스트를 제공한다. 단말 TTS·지도 표시·119 OS 화면은 앱 소관이다. 공식 통제 정보를 검토한 경로 상태와 실제 통행 가능한 경로 도형은 다르며 경로를 만들어 안전하다고 표시하지 않는다. 프로필의 반경·관심 행정구역 설정은 저장하지만 이번 관련성 판정은 입력된 사건/경보 구역을 사용한다. 영어 번역과 행정구역 경계 자료는 미확보이므로 한국어·시연 구역 기준을 표시한다.

## 시연 계정 발급

일반 서버의 비밀 설정이 준비된 뒤 관리자가 실행한다. 출력 파일은 Git 밖에 두고 토큰을 로그에 출력하지 않는다.

```sh
cd /home1/ncloud/bonghwajigi
sudo docker compose --env-file /home1/ncloud/.config/bonghwajigi/general.env \
  -f deploy/compose/mvp.yaml exec -T api python tools/mvp_accounts.py \
  --scenario demo --user user-a --mobility independent --output /accounts/user-a.json
```

사용자 토큰은 기본 24시간 후 만료된다. 계정 파일을 안전하게 앱 개발 환경에 전달하고 내부 토큰·서명키는 전달하지 않는다. 원격 배포 도구의 실제 경로와 사용법은 서버 문서를 따른다.
