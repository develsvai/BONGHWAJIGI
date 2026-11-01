# Previous Results

9 older recorded result(s) were omitted. Promote durable context to Job Notes or explicit Context References.

## 13. 현재 저장소 변경을 점검·체크포인트 커밋하고 develop 원격과 동기화

# 저장소 변경 점검과 동기화

사용자의 현재 변경 전체 커밋·원격 동기화 지시를 실행한다. 대상은 BONGHWAJIGI의 develop이며 BONGHAWJIGI_APP은 조회·수정하지 않았다.

## 점검한 변경

- 국내 산불 공개 자료 수집·구축, GOES 시간별 관측 실험·고정 모델 평가, 기상청 FF 수집과 관련 테스트·설정·보고서, 학습 의존성 및 Loom 진행 기록이다.
- 학습 실험 Task task-20261031-111807-task-9a960503은 RUNNING으로 보존한다. 이번 커밋은 현재 파일의 체크포인트이며 국내 예측 검증이나 운영 적용 완료를 뜻하지 않는다.
- 초기 파일 점검은 변경·추가 파일 83개 약 1.17 MB, 최대 단일 파일 약 142 KB였다. JSON/JSONL 형식과 비밀키·토큰·서명 URL 패턴을 검사했고 발견 사항이 없었다. 로컬 .env.analysis, 원시 자료, 실행 결과 및 가상환경은 Git 제외를 유지한다.
- 원격 fetch 결과 로컬 전용 커밋 16개, 원격 전용 커밋 3개였다. 원격의 실제 파일 추가는 docs/V3/01-planning-baseline.md 한 개다. 양쪽 이력을 보존하는 merge로 통합한다.

## 검증

- 학습 테스트: 29 passed.
- 서버 테스트: 35 passed, DB 연결 설정이 없는 22 skipped. 기존 Starlette/httpx deprecation 경고 1개. 이번 검증에서 DB 테스트·GPU 학습·원격 모델 서비스는 실행하지 않았다.
- 서버 65개 파일과 학습 20개 파일의 Ruff 정적 검사·포맷 검사 통과. kma_download.py의 표현식 줄바꿈만 정리했다.
- 앱 API 계약: 25 API, 67 스키마, 48 HTTP 예제, 푸시 예제 1개, 오류 거부 4개 통과.
- 학습 uv lock --check --offline 통과, 71개 패키지 확인. bash 구문, git diff --check, Loom strict(6 Jobs/41 Tasks/41 definitions) 통과.

## 동기화 결과

- 체크포인트 00bfa9c: 현재 코드·설정·실험 보고서와 두 작업의 Loom 기록 총 83개 파일을 보존했다. 학습 Task는 계속 RUNNING이다.
- 병합 0659235: 원격 develop의 세 커밋을 충돌 없이 통합했다. 원격 V3 기획 문서를 원문대로 보존했으며 소스 코드 충돌이나 삭제는 없었다.
- git push origin HEAD:refs/heads/develop 성공. 원격 develop이 6dc2ddc에서 0659235로 갱신됐고 로컬 추적 참조도 같은 커밋이다. 강제 push는 하지 않았다.
- 병합 직후 git status는 작업 파일 변경 없이 develop의 기존 로컬 커밋 18개가 원격보다 앞선 상태였다. 정상 push로 해당 이력을 반영했다.
- 병합 후 Loom strict(6 Jobs/41 Tasks/41 definitions), git diff --check, 원격 이력의 HEAD 포함 관계 확인을 통과했다. 병합은 문서 한 개만 추가하므로 이미 통과한 코드 테스트를 불필요하게 반복하지 않았다.

이 결과와 Task 완료 기록도 커밋·push하고 마지막 원격 SHA와 깨끗한 작업 트리를 다시 확인한다. GPU 서버나 학습 서비스는 이번 작업에서 변경하지 않았다. 이후 병행 학습에서 생기는 변경은 다음 체크포인트 대상이다.

## 14. 일반 서버에 산불 MVP를 상시 배포하고 예측 제외 통합 시연 검증

# 산불 MVP 일반 서버 배포 완료

일반 서버 inno-server-011에 실행 커밋 654a9ef의 Docker 이미지를 배포하고 상시 실행/부팅 등록을 완료했다. API·긴급·분석·전달·outbox·정책·Qwen 통합 7개 프로세스, PostgreSQL/pgvector·Redis 2개, 정상 완료된 migration 1개다. 실제 예측 연결은 사용자 지시로 제외하며 앱 예측은 unavailable/null이다. 앱 저장소와 진행 중인 training 작업은 수정하지 않았다.

## 실제 검증

- 사용자 확정 명칭은 1 경고, 2 대피, 3 위급이다. 합성 사용자 3명으로 H2 이동 여건별 차이, 긴급 큐 공식 대피 원문/위치 대상, 조력자 도착, 대체 경로 없는 차단, 공식 정정·해제, 자동 하향 방지와 확인 후 하향, 위치 삭제/복원 재평가를 확인했다. 실제 재난 발령이 아닌 합성 입력이다.
- 긴급 경로는 Qwen을 기다리지 않는다. 일반 서버 GPU 터널만 끊고 전체 합성 시연을 다시 실행해 동일 흐름이 통과했다. 기존 GPU 모델 서비스와 학습은 중단하지 않았다.
- 실제 GPU 임베딩 1024차원, 인터넷 검색 성공/5개 결과, 실제 Qwen 통합 완료. 입력 876/출력 257토큰, 모델 시간 10355.72ms다. 생성 요약은 미검토이고 개인 단계는 고정 규칙만 사용한다.
- 일반 서버 전체 서비스 정지/재시작 후 해당 시나리오 계정 3개·입력 30개·개인 정책 3개·전달 기록 17개·변경 36개·긴급 작업 3개가 보존됐다. 입력 본문 SHA256 일치, 정책 ID 보존 및 revision 비감소를 확인했다. migration bde1925b1429.
- 재시작 이후 전달은 simulated 12개/superseded 5개이며 pending 없음. 긴급·분석·전달 큐 잔여 0개다. 실제 푸시 발송/단말 수신을 뜻하지 않는다.
- 개발 컴퓨터에서 SSH 사설망을 통해 readiness 200, 무인증 사용자 조회 401, 실행 OpenAPI 0.2.0-mvp(사용자 21개 경로/28개 동작)를 확인했다. 사용자 간 다른 리소스 접근은 404다.
- 승인된 전용 SSH 키는 일반 서버 출발과 GPU 8001 API 포트만 허용한다. 다른 포트·원격 포워딩·임의 명령의 거부를 실제 검사했다. 일반 서버 설정/개인키는 600이며 값은 Git/로그에 없다.

## 검증과 산출물

- 실제 PostgreSQL 포함 서버 테스트 82 passed, 기존 Starlette/httpx 경고 1개. Ruff check/format, 실행 OpenAPI 구조, 기존 25 API/67스키마/48HTTP예제/4오류 거부, Alembic check, Compose config 통과. 워커 오류 표식 0개.
- docs/V2/delivery/mvp-server-runbook.md: 실제 접속·계정·시연·지속 실행·복구·비공개 설정·제외 기능.
- docs/V2/delivery/mvp-server-evidence.json: 정상/GPU 미연결 합성 시연, 모델 지표, 재시작 및 사설망 검사 근거.
- deploy/compose/mvp.yaml, deploy/systemd/bonghwajigi-general*.service, deploy/ssh/gpu-api-only.conf: 상시 배포 구성.
- tools/mvp_provision.py, tools/mvp_demo.py, tools/mvp_analysis_demo.py: 비공개 준비와 재실행 가능한 시연.

## 범위와 다음 연결

사용자가 Firebase와 HTTPS 도메인이 아직 없다고 답했으므로 모의 발신/SSH 사설망 개발 접속까지 완료했다. 실제 단말/FCM/공개 HTTPS/외부 로그인 제공자/실제 도로 경로는 미검증이다. 실제 예측 연결·실제 K8s 수집·3D·서버 음성·자동 119 신고는 제외했다. 실제 Firebase 자격 파일/기기와 도메인이 정해지면 실제 전달 및 단말 통합을 검증해야 한다. 현재 위치·상태는 5분마다 만료되므로 앱에서 최신 자료를 보내야 한다.

서버와 터널은 계속 실행한다. 진행 중인 다른 채팅의 학습 파일/전역 문서 등록 변경을 보존하며, 이번 구현과 Task 기록만 커밋한다.
