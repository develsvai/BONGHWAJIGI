# 결과

일반 서버에 앱 설치/세션 API와 migration을 배포하고 mobile-demo 합성 사건·긴급 큐 원문을 준비했다. 사용자 등록부터 프로필·위치·현재상태→경고/대피/위급→화면변경 cursor→refresh/로그아웃까지 실제 API로 검증했다. 기존 계정9개와 입력87개는 보존됐고 GPU/학습은 변경하지 않았다.

## 검증

격리 로컬 PostgreSQL에서 .venv/bin/alembic upgrade head 및 .venv/bin/alembic check, .venv/bin/pytest -q 전체93개 통과. 변경 파일 ruff check 통과. 배포 서버 python tools/mobile_demo.py의 긴급 큐 완료·원문·3단계·타사용자404·토큰 회전/로그아웃401 검사 통과. /health/ready200와 OpenAPI0.2.0-mvp, 허용CORS/차단CORS 확인.

## 접속과 한계

SSH localhost18080 터널을 유지하며 휴대폰은 adb reverse로 연결할 수 있다. 승인된 두 단말→서버443 최소 grant 적용 뒤 개발 Mac에서 Tailscale Serve HTTPS/TLS200을 확인했다. 실제 단말 검증/APK는 앱Task에서 진행하며 실예측·실FCM·지도자격은 제공 완료로 표기하지 않는다.

상세: docs/V2/delivery/mobile-server-deployment.md 및 mobile-server-evidence.json.

공식 경보 발신 payload의 리소스ID를 API 공개ID와 일치시켰고 두 사용자 간 캡처sender→인증조회200/교차조회404 회귀를 추가했다. 실제 FCM 발신은 사용하지 않았다.

최종 실행 커밋 dcbc62e 배포 후 Mac→Tailnet HTTPS에서도 새 계정 등록·3단계 갱신·refresh·로그아웃을 통과했다. 배포 OpenAPI 전체JSON과 앱 생성 원본이 일치한다. 최종 네트워크 차단은 해결됐고 실제 휴대폰 UI/APK 검증은 앱 담당 작업에서 진행한다.
