# 앱 실연동 서버 배포

2026-11-01 KST. 배포 준비와 실제 검증을 기록한다. 등록은 사설망 simulation의 mobile-demo에만 켜며 새로운 고유 사용자 계정을 만든다. 실제 예측과 FCM 실발신은 제공하지 않는다.

## 구현과 로컬 검증

Compose 등록·시나리오·CORS 설정을 전달한다. 기타 보호 대상(other)을 프로필에 저장하고 준비 지침에 반영한다. 실제 PostgreSQL에서 migration/check와 서버 테스트92개가 통과했다.

## 접속

SSH localhost18080 → 일반 서버 loopback8000을 사용한다. 휴대폰 USB 검증은 adb reverse tcp:18080 tcp:18080으로 연결한다. Tailscale Serve는 자동 승인 검토에서 지속 노출의 명시 승인 부족으로 거절되어 실행하지 않았다.

## 합성 자료

컨테이너에서 python tools/mobile_demo.py를 실행한다. 별도의 mobile-demo/mobile-fire 자료를24시간 유효하게 입력하고 긴급 큐가 합성 경보를 처리하도록 한다. 테스트 좌표는36.4,129.35,정확도10m다. --seed-only는 자료만 갱신한다. 실제 산불·공식 발령이 아니다. 신규 계정 등록·정책 단계·cursor·refresh·로그아웃 검증은 토큰을 메모리에서만 사용한다.

실제 배포 검증 결과는 완료 후 아래에 추가한다.
