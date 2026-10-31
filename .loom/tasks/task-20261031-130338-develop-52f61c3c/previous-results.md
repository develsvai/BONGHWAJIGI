# Previous Results

7 older recorded result(s) were omitted. Promote durable context to Job Notes or explicit Context References.

## 11. 시나리오 수신에서 분석 큐·임베딩 검색·Qwen 전달 직전까지 연결

# 실행 결과

사용자가 요청한 시나리오 수신 → PostgreSQL/outbox → Redis 분석 큐 → 인터넷 뉴스 검색·실제 GPU 임베딩 → pgvector 검색 → Qwen 전달 직전 자료의 흐름을 구현했다. 추가 검색 질문에 사용자가 인터넷 검색도 연결하도록 선택해 Google News RSS와 저장 자료를 함께 검색한다.

입력과 outbox를 같은 트랜잭션에 저장하고 동일 ID·본문은 같은 job으로 반환하며 충돌은 409로 거부한다. 분석 워커는 문서와 질의를 임베딩하고 scenario·시각·유효기간·모델 revision으로 검색을 제한한다. 결과는 출처·origin·시각·매체·확인 상태·검색 점수와 함께 ready_for_qwen으로 저장한다. Qwen 생성은 호출하지 않는다.

## 실제 검증

- 별도 로컬 PostgreSQL 16/pgvector와 Redis 7.4를 실행하고 migration 적용 및 Alembic check를 통과했다.
- localhost API·실제 Redis/Celery 워커·outbox·SSH 터널의 기존 L4 임베딩과 인터넷 검색을 연결했다.
- 마지막 시연(2026-10-31 19:13 KST): 인터넷 뉴스 5건 검색, 검색 근거 5개, 상태 ready_for_qwen, 같은 이벤트 재전송은 같은 job ID. qwen_invoked=false.
- 27개 테스트 통과. 실제 DB에서 인증·멱등 충돌·시나리오 격리·outbox 실패/복구·중복 전달·미래/만료 자료·모델 revision·웹 장애 대체·벡터 계약을 검증했다.
- 원래 25개 앱 API/67 스키마/48 HTTP 예제/4개 오류 거부 검사도 통과했다. 내부 분석 경로는 앱 API 계약과 구분했다.
- Ruff check와 실행 도구 format, Compose 구성·시나리오 파일 검사 통과. CPU 개발 환경에 GPU 모델 라이브러리는 설치하지 않았다.
- 실행 도구 serve_analysis.py로 세 프로세스 시작과 Ctrl+C 정리를 확인했다. 검색어가 HTTP 클라이언트 INFO 로그에 출력되지 않도록 분석 워커 로거를 조정했다.

## 운영과 남은 범위

코드·실행·API·결과 계약은 docs/V2/delivery/analysis-retrieval-flow.md와 evidence JSON에 기록했다. .env.analysis는 권한 600 및 Git 제외를 확인했다. 저장된 실제 뉴스 원문/설정/인증 값은 커밋하지 않는다.

실제 K8s 수집·일반 서버 배포·Qwen 사건 통합·XGBoost 추론·개인 정책/알림은 수행하지 않았다. 웹 검색은 뉴스 제목·짧은 설명이며 기사 본문 수집과 자료 품질 검증을 뜻하지 않는다. 실제 프로세스 강제 종료·장기 부하·원격 CI는 미검증이다.

같은 workspace에서 별도 XGBoost 준비 Task와 training/ 변경이 진행 중인 것을 확인했다. 해당 Job/Task/파일을 수정하거나 함께 커밋하지 않고 보존한다. 공용 이벤트 기록은 이번 Task의 항목만 부분 스테이징한다.

최종 Task boundary strict와 workspace strict(6 Jobs/35 Tasks/35 definitions), git diff --check를 통과했다. 새 API/워커/outbox 실행기는 종료했고, 검증 DB·Redis는 볼륨을 보존해 정리한다.

## 12. 재난 경보를 포함한 Qwen3 사건 통합 실행과 추론 직전 결과 문서화

# 실행 결과

사용자 직접 지시에 따라 공식 경보 발령 기록을 포함하는 과거 영덕 산불 시나리오를 실제 DB/outbox·Redis/Celery·GPU 임베딩·인터넷 검색·Qwen3 생성으로 실행하고 추론 직전 자료를 문서로 제공한다. 이전 analysis-demo에는 실제 경보가 없었다는 사실을 정정했다.

최종 실행은 2026-10-31 19:40:47 KST다. 공식 발령 기록 1건과 공식 행동요령·지역 뉴스 등 자료 5개를 결합했다. Qwen3-4B-Instruct-2507 고정 revision, 입력 1021/출력 334토큰, 모델 시간 13404.69ms다. 실제 모델 요약과 근거 3개, 생성 요청/응답 원문, 출처·게시/수집 시각·공식 사이트 HTML 해시·검색 결과·추론 전 JSON을 docs/V2/delivery/qwen-integration/에 보관했다.

경보는 정책브리핑의 과거 전국 심각 발령 사실을 검토해 정규화한 기록이다. 직접 수신한 재난문자 원본이나 현재 경보가 아니다. 공식 등급·시각·대상·짧은 원문을 별도 유지하며 생성 모델이 변경하거나 검색 순위가 누락시킬 수 없게 했다. 공식 긴급 경로를 Qwen 뒤에 연결하거나 경보를 발송하지 않았다.

현재 NDWS 학습 계약의 20개 수치 입력과 격자 정렬 자료가 없어 모두 null이고 추론 gate는 blocked다. 미국 자료 모델의 국내 적용은 검증되지 않았다. XGBoost 학습·추론·개인 단계·정책·알림은 실행하지 않았다. 다른 채팅의 training/ 작업과 C Job metadata는 보존했다.

## 검증

- 실제 로컬 PostgreSQL/pgvector·Redis/Celery·수신 API와 기존 L4 임베딩/Qwen API 및 인터넷을 연결했다.
- 공식 정책브리핑·안전한TV HTTP 200, 본문 표식과 HTML SHA256 기록. 현재 수집한 과거 게시물의 발표 시각 cutoff이며 당시 수집 가능성 백테스트는 아니다.
- 실제 생성 결과의 JSON·출처 ID·인용 원문 일치, 고정 revision과 실제 서버 tokenizer의 전체 예산 검사를 통과했다.
- 신규 15개와 기존 27개를 합친 42개 테스트 통과. 미래/다른 scenario/근거 없는 경보, 임의 수치 피처, 없는 출처와 인용, 잘린 JSON·토큰 한도·revision 오류 거부를 포함한다.
- Ruff check/format, git diff --check, 기존 25 API·67 스키마·48 HTTP fixture·4 오류 거부 검사 통과.
- 로컬 API/워커/outbox 시연 프로세스는 종료했다. 검증 DB/Redis와 터널도 산출물 보존 후 정리한다. 기존 GPU 모델 서비스를 변경하거나 중단하지 않았다.

사람이 읽는 최종 문서는 docs/V2/delivery/qwen-integration-result.md다. 구현은 수동 CLI 시연 도구이며 자동 후속 워커·일반 서버 배포는 수행하지 않았다. 모델 요약은 미검토이고 인용 일치가 의미·정책 승인을 뜻하지 않는다.
