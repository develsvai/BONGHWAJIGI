# 확인과 해결

- Docker 소켓의 기본 sandbox 접근이 제한돼 사용자 지시 범위의 로컬 검증으로 권한 검토를 거쳐 실행했다. 기존 컨테이너는 유지하고 별도 localhost DB/Redis 프로젝트를 만들었다.
- 웹 도구에서 RSS 문서를 열 수 없었지만 실제 HTTP 클라이언트로 200 응답을 확인했고 최종 워커에서 실제 뉴스 검색이 통과했다.
- Alembic 자동 생성은 pgvector import와 확장 준비가 빠져 있어 검토 후 명시적으로 추가했다. 모델과 DB 차이 없음도 확인했다.
- 초기 정적 검사·테스트의 긴 줄·누락 timedelta import를 수정했다. 최종 27개 검사와 Ruff는 통과했다. 실패한 패치는 적용되지 않았고 올바른 문맥으로 다시 반영했다.
- 최초 워커의 HTTPX INFO 로그에 검색 URL이 출력돼 httpx/httpcore 로그 수준을 조정했다. 최종 실행에서는 원문 검색어를 INFO에 출력하지 않았다.
- Starlette TestClient의 httpx 전환 관련 의존성 경고 1개는 남아 있으나 테스트 실패는 없다. 실제 원격 CI·프로세스 강제 종료·대규모 품질/부하 검증은 범위 밖이다.
- 다른 XGBoost Task의 metadata 및 training/ 변경을 발견해 자신의 Task 경계만 스테이징한다. 다른 작업을 되돌리거나 완료 처리하지 않는다.
