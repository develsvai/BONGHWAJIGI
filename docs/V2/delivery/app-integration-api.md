# 앱 통합 API 보완

2026-11-01 KST. 앱 목업 실연결 요청에 따른 후속 구현이다. 기존0.2.0-mvp와3단계를 유지하고 필요한 필드·세션 경로를 추가했다. 실제 예측·3D·도로 경로 생성·서버 STT/TTS·실제 FCM 발신은 제외한다.

## 설치 계정과 인증

- GET /v1/auth/config: 공개된 내부 시연 등록 가능 여부·동의 버전·안내.
- POST /v1/auth/installations: installation_id와 consent(version=internal-demo-v1, service/privacy/location=true)를 받아 시연용 새 익명 설치 계정과 세션을 발급한다. 기존 사용자 ID를 입력해 다른 계정을 가져올 수 없다.
- POST /v1/auth/refresh: refresh_token으로 access와 refresh를 함께 회전한다. 소비된 refresh를 다시 사용하면 해당 세션을 폐기한다. 만료·로그아웃·폐기 후에는 access와 refresh 모두 거부한다.
- POST /v1/me/logout: 기존 사용자 token_version을 올려 사용자의 이전 access와 refresh를 모두 무효화하고 단말 토큰을 해제한다.

등록은 BONGHWA_APP_REGISTRATION_ENABLED=true인 simulation에서만 열리며 기본은 off다. 운영 회원가입·외부 로그인 제공자가 아니다. BONGHWA_APP_REGISTRATION_SCENARIO의 기본은 mobile-demo이고 같은 시연 사건 범위에 새로운 고유 사용자를 만든다. IP 원문 대신 서버 키로 HMAC한 값으로 시간당 등록 상한(기본20개)을 적용한다. 프록시 X-Forwarded-For를 임의 신뢰하지 않는다.

access는 최대15분, refresh의 기본 절대 유효기간은7일이다. DB에는 refresh 비밀 부분의 SHA256만 보관한다. 앱은 SecureStore에 저장하며 서버 서비스 토큰·JWT 서명키를 받지 않는다. 설치 ID만으로 기존 세션이나 개인정보를 복원하지 않는다. 앱 재설치/자격 삭제 시 새 시연 계정을 만들 수 있다. 민감 데이터가 있는 계정의 복구·공개 서비스 가입·운영 보관기간은 이번 내부 시연 계정의 기능이 아니다.

## 프로필과 준비 지침

AppProfile에 display_name, age_band, emergency_contact, usual_place, building_floor, health_consent, health_notes를 추가했다. 기존 mobility/stairs/communication_preference/sensory_supports/dependents/helper_registered/vehicle_access를 유지한다. 선택 의료 메모는 동의가 있을 때만 저장하며 동의를 끄면 빈 메모를 보내야 한다. 동의 없이 값이 있으면422다. 입력 오류에는 요청 원문·토큰·메모를 되돌려주지 않는다. 철회와 프로필 삭제는 이전 프로필 멱등 응답에 보관된 메모도 지운다.

의료 메모·호칭·연락처·생활 장소를 Qwen이나 단계 결정에 자동 전달하지 않는다. 정책은 기존 정규화한 이동·보호 대상·확인 상태와 공식 근거로 결정한다. 계단 이용 어려움의 현재 상태 입력도 needs_time으로 정규화하도록 바로잡았다.

GET /v1/me/preparations는 별도의 준비 카드 계약이다. 승인된 DB 지침에서 기본 가방 카드와 이동 도움/보호 대상/물품 점검 중 하나를 선택해 최대2개, 출처·지침revision·profile_revision·유효시간·이유를 돌려준다. 긴급 actions를 앱이 임의로 준비 카드로 바꾸지 않는다. 기본 수칙은 별도의 avoid 항목에 승인된 회피 지침을 제공한다.

## 응답과 갱신

현재 명세: [실행 OpenAPI](api/mvp-openapi.json). 직접 수정하지 않은 앱 생성 타입은 이 명세 사본에서 생성한다. 새로운 등록/세션 및 홈·프로필·위치·공식경보·개인응답·준비/수칙의 출력 모델을 명시했다.

- Home: nearby_disasters, basic_rules, location, features, preparations, alerts.
- Profile/Location의 revision은 앱 문서 수정 버전이고 input_revision은 정책 입력 버전이다. 앱은 이 값을 정책 input_versions와 대조한다.
- Response: id, scenario_id, revision, evaluated_at, pending_update, error_code, content, user_context.
- content.personal_response는 서버의 level/number/label이고 content.actions는 서버의 승인된 행동이다. content.prediction은unavailable/null이다.
- user_context는 현재 상태의 revision·available/stale/unavailable·원자료다. 이를 AI 문서통합용 content.context와 혼동하지 않는다.
- content.assistant_utterance는 검토된 정책의 현재 질문 또는 행동 텍스트다. source=reviewed_policy_text이며 생성 모델의 미검토 요약을 안전 지침으로 바꾸지 않는다. 갱신 대기나 만료 시 발화는null이다. 단말 TTS로 읽을 수 있으며 서버 음성을 생성하지 않는다.
- GET /v1/me/updates는 cursor와 wait_seconds(0–25)를 사용한다. 기존 초안의 after 파라미터를 쓰지 않는다. 410은 전체 재동기화, 401은 세션 갱신 또는 재등록으로 처리한다.

## 배포·검증

마이그레이션f735a2ec901b가 app_sessions와 조회 인덱스를 추가한다. 기존 자료는 변경하지 않는다. 실제 일반 서버 배포 시 migration 뒤 등록을 사설망 시연에서만 켠다. APK의 USB 검증은 loopback 전용 경로로 연결하며 공개 인터넷에 무인증 등록을 노출하지 않는다. CORS는 BONGHWA_APP_CORS_ORIGINS의 명시된 원점만 허용한다.

실제 로컬 PostgreSQL에서 전체 서버 테스트91개, Alembic check, 변경 파일 Ruff가 통과했다. refresh회전/재사용폐기·만료·로그아웃, 등록off/live거부·동의검증·한도, 의료메모철회/삭제/오류 비노출, 준비카드, 현재 계단 상태→단계/발화 갱신을 검사했다. 기존 Starlette/httpx 경고1개가 있다. 합성0.2 응답을 캡처한 모의자료의 단계는 경고/대피/위급이며 실제 경보가 아니다.

서버 기능 구현과 로컬 검증 완료다. 앱 구현·일반 서버 재배포·휴대폰 통합 검증·APK 배포는 앱 실행 Job에서 이어간다. 현재 학습과 GPU 서비스를 변경하거나 중단하지 않았다.
