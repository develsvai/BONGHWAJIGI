# 문제와 처리

- 기본 sandbox에서 SSH/로컬 Docker·DB 접근이 제한돼 기존 사용자 지시 범위로 권한 검토를 거쳐 실행했다. 자동 승인 검토 거절은 없었다.
- SSH는 비밀번호 인증이 필요해 기존 설정의 숨겨진 입력 프롬프트로 접속했다. 비밀번호·서비스 토큰은 파일/명령행/산출물에 추가하지 않았다. 짧은 ControlPersist 연결이 종료돼 실제 검증용 터널을 다시 열었다.
- 첫 실제 생성은 과거 뉴스의 대피 표현을 요약에서 권고형으로 남겼다. 과거 보고체와 권고형 금지 지시를 추가한 뒤 새 생성으로 확인했다. 첫 결과는 gitignore 대상 data/artifacts/qwen-integration-attempt-1, 최종 결과는 docs/V2/delivery/qwen-integration에 있다.
- JSON 구문을 임의 복구하거나 모델 요약을 사람이 수정해 모델 출력으로 표시하지 않는다. 불완전·근거 불일치·모델 버전 불일치 시 실패로 처리한다.
- 테스트는 기존 Starlette TestClient의 httpx 관련 deprecation 경고 1개만 남고 42개 모두 통과했다. 의존성 교체는 이번 범위가 아니다.
