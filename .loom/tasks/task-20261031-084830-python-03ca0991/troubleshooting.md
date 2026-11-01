# 확인 및 해결

- 초기 Task 실행 명령에 잘못된 임시 ID가 들어가 Not found로 종료됐다. 생성된 실제 ID로 실행했으며 잘못된 상태 변경은 없다.
- 기본 uv 캐시는 sandbox에서 쓰기 제한이었다. 캐시를 /private/tmp/bonghwajigi-uv-cache로 지정하고 필요한 패키지만 설치했다.
- 첫 Ruff 검사에서 긴 한 줄을 발견해 format으로 수정했고 최종 정적 검사는 통과했다.
- 최신 Starlette TestClient는 httpx 대신 httpx2 사용을 안내하는 deprecation warning을 낸다. 현재 10개 테스트와 실제 Uvicorn HTTP 검증은 통과했다. 의존성을 경고 없이 변경하는 별도 확대는 하지 않았다.
- 원격 서버, 실제 K8s 및 DB를 변경하지 않았다. 모델 설치는 사용자의 후속 직접 지시에 따라 새 Task로 진행한다.
