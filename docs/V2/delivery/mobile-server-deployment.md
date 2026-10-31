# 앱 실연동 서버 배포

2026-11-01 KST. 일반 서버에 앱 설치 계정·회전 세션과 migration을 배포했다. 등록은 사설망 simulation의 mobile-demo에만 켜며 새로운 고유 사용자 계정을 만든다. 실제 예측과 FCM 실발신은 제공하지 않는다.

## 구현과 로컬 검증

Compose 등록·시나리오·CORS 설정을 전달한다. 기타 보호 대상(other)을 프로필에 저장하고 준비 지침에 반영한다. 실제 PostgreSQL에서 migration/check와 서버 테스트93개가 통과했다.

## 접속

SSH localhost18080 → 일반 서버 loopback8000을 사용한다. 휴대폰 USB 검증은 아래 연결을 유지한다.

```sh
ssh -N -L 127.0.0.1:18080:127.0.0.1:8000 inno-server-011
adb reverse tcp:18080 tcp:18080
```

단말 API 주소는 `http://127.0.0.1:18080`이다. USB·SSH 연결이 유지되어야 한다. APK에 내부 서비스 토큰·JWT 서명키를 넣지 않는다. 설치 계정 등록→기기 등록→프로필·위치 순으로 호출한다.

Tailscale Serve는 처음 자동 승인 검토에서 지속 노출의 명시 승인 부족으로 거절됐다. 이후 사용자가 Tailnet 전용 HTTPS를 명시 승인해 `https://inno-server-011.tail2dac17.ts.net` → `http://127.0.0.1:8000`을 설정했다. 공개 Funnel은 사용하지 않는다. 서버 자신의 HTTPS 인증서 검증과 readiness200은 통과했다.

최초 외부 접속은 기존 PacketFilter가 목적지 TCP22만 허용해 시간 초과였다. 이후 사용자 승인을 받은 개발 Mac·휴대폰 두 출발지에서 일반 서버 TCP443만 허용하는 grant를 관리 화면에서 추가했다. 개발 Mac에서 정상 TLS 인증서 검증과 HTTPS readiness200을 확인했다. 다른 Tailnet 기기 전체로 접근을 넓히지 않았다. 서버 DNS 수용은 기존대로 off이며 바꾸지 않았다. 단말은 Tailscale이 연결되어 있어야 한다.

## 합성 자료

컨테이너에서 python tools/mobile_demo.py를 실행한다. 별도의 mobile-demo/mobile-fire 자료를24시간 유효하게 입력하고 긴급 큐가 합성 경보를 처리하도록 한다. 테스트 좌표는36.4,129.35,정확도10m다. --seed-only는 자료만 갱신한다. 실제 산불·공식 발령이 아니다. 신규 계정 등록·정책 단계·cursor·refresh·로그아웃 검증은 토큰을 메모리에서만 사용한다.

## 실제 배포 검증

[기계 판독 근거](mobile-server-evidence.json)에 실행 결과를 기록했다.

- 최종 실행 소스는 `dcbc62e`(이미지 `bonghwajigi-mvp:dcbc62e`), migration은 `f735a2ec901b`다. PostgreSQL/Redis 볼륨을 유지하고 기존 시나리오 계정9개·입력87개를 전후 확인했다.
- 기존 설정과 PostgreSQL dump는 서버 `/home1/ncloud/.config/bonghwajigi/backups/mobile-d8dc54a`에 권한600으로 보관했다. 새 설정도600이고 기존 자격은 바꾸지 않았다. GPU 서버와 학습 프로세스를 변경하거나 중단하지 않았다.
- API/긴급·분석·전달/정책·통합/outbox 7개 프로세스와 DB/Redis가 실행되고 일반 서버/GPU 터널 systemd가 active다.
- 합성 설치 계정 두 개로 등록, 기기, 프로필 기타 보호 대상과 준비 카드, 위치, 긴급 큐 원문, 경고→대피→위급, 검토된 정책 텍스트, cursor 갱신, 다른 사용자 자료404, refresh회전, 로그아웃 뒤 access/refresh401을 확인했다.
- 무인증 프로필401, OpenAPI0.2.0-mvp, 명시한 localhost8081 CORS 허용과 미등록 원점400을 확인했다.
- 최종 배포 뒤 개발 Mac의 Tailnet HTTPS에서 새로운 합성 계정으로 등록→기기/프로필/위치→공식 원문→경고/대피/위급→cursor→refresh→로그아웃을 다시 확인했다. TLS 검증을 유지했고 배포 OpenAPI 전체JSON이 앱 타입 생성 원본과 일치했다.

공식 경보 알림의 전송 ID도 인증 API와 일치시켰다. DB 내부 사건/경보 ID는 취소·만료·중복 검사에 보존하고 발신 직전 payload.resource_id를 해당 사용자의 HMAC 공개ID로 바꾼다. 두 사용자의 캡처 발신 결과가 각각 본인 API200·다른 사용자404이며 ID가 서로 다름을 실제 DB에서 확인했다. 실제 Firebase 단말 수신 검증과 구분한다.

기타 보호 대상은 이동 준비 시간을 늘리는 입력이므로 단계 검증에서는 카드 저장 확인 뒤 독립이동 프로필로 초기화했다. 기기 등록 없이 위치를 보내면404로 거부되는 것을 확인하고 앱과 같은 호출 순서로 검증했다. 시연 도구의 실패는 수정 후 재검증했다.

## 운영과 한계

자료가 만료되면 `python tools/mobile_demo.py --seed-only`로 합성 자료의 새 revision을 입력한다. 유효기간24시간은 합성 사건 자료에만 적용되며 사용자 위치·현재 상태의 기존5분 유효기간은 유지한다. APK가 전송한 최신 위치만 사용자 관련성 판단에 쓰며 신규 계정을 임의 테스트 좌표로 자동 이동시키지 않는다.

이 문서의 검증은 배포 API 결과다. 실제 휴대폰 화면·TTS·APK 설치 검증은 앱 작업에서 이어진다. 실제 재난·공식기관 발령·Firebase 단말 수신·실측 지도 경로·실제 예측 결과가 아니다. 사고 종료 근거가 없으므로 자료 최신성을 사건 종료로 해석하지 않는다.
