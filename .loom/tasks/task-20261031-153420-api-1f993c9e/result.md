# 결과

사설망 simulation 설치 계정과15분 access·7일 refresh 회전/재사용 폐기·로그아웃을 구현했다. 프로필 전 항목·선택 의료 메모 동의/철회/삭제·입력 오류 원문 비노출, 개인별 별도 준비카드·회피지침, 현재 상태와 정책 입력 버전·서버 발화 계약을 추가했다. 계단 이용 어려움이 실제 정책에 반영되도록 수정했다. 새로운 출력 모델과 실제0.2 OpenAPI를 생성했다.

실제 PostgreSQL 전체91개 테스트·Alembic check·변경 파일Ruff 통과, 기존 Starlette/httpx 경고1개. 앱 화면·일반 서버 배포·실제 단말 통합은 이어지는 앱Job에서 진행한다. 기존 학습/GPU는 변경하지 않았다. 문서: docs/V2/delivery/app-integration-api.md.

## 검증

실행 명령: `.venv/bin/pytest -q` — 실제 PostgreSQL 포함91개 통과, 기존 경고1개. `.venv/bin/alembic upgrade head` 및 `.venv/bin/alembic check` — DB 구조 일치. `.venv/bin/ruff check`와 `.venv/bin/ruff format` — 변경 파일 통과. `.venv/bin/python tools/mvp_contract.py` — 현재 실행 OpenAPI 생성. `loom validate --strict`와 `git diff --check` 통과.
