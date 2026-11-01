# Previous Results

3 older recorded result(s) were omitted. Promote durable context to Job Notes or explicit Context References.

## 7. 산불 MVP 구현 기술 스택과 서버별 배치 계약 고정

# 실행 결과

산불 MVP 구현 스택과 서버별 배치 기준을 `docs/V2/delivery/implementation-stack.md`에 고정했다. API·저장·공간/벡터 검색·큐·정책·수집·GPU 서빙·학습·배포·검증의 책임과 설치 전 조건을 구분했다.

- Python 3.12, uv, FastAPI/Pydantic 2/Uvicorn, SQLAlchemy 2.x/psycopg 3/Alembic을 기준으로 선정했다.
- PostgreSQL 16에 PostGIS와 pgvector를 함께 두고 Celery/Redis의 긴급·분석 워커를 분리한다.
- GPU는 Transformers/Sentence Transformers를 쓰는 단일 FastAPI 프로세스와 제한된 동시성으로 시작하며 XGBoost GPU 학습과 일반 서버 CPU 추론을 분리한다.
- 전경 갱신은 기존 long polling, 실제 푸시는 FCM HTTP v1 첫 어댑터와 모의 Sender 경계를 명시했다.
- A3는 이 Task와 문서를 선행 설계 및 필수 입력으로 참조한다. 관련 Job 5개의 노트에 기술 기준을 남겼다.
- 대응 레벨·레벨별 알림 방식은 사용자 회의 결과 대기로 유지했다. D1과 A3는 PENDING이며 다른 구현 Task 또는 Queue는 시작하지 않았다.

## 검증 근거

작업 시작 시 로컬 `bbf6233`과 원격 develop이 같고 미커밋 변경이 없음을 GitHub 비교와 로컬 상태로 확인했다. 기존 인프라 점검 문서와 API 계약을 대조하고 공식 기술 문서 13개를 참조했다.

- 새 문서의 내부 링크 누락 0개와 코드 펜스 균형을 검사했다.
- 전체 30개 Task의 선행 관계를 순회해 미존재 참조와 순환이 없음을 확인했다.
- A3의 선행 설계/필수 문서 연결과 D1·A3의 PENDING 보존을 확인했다.
- `loom task validate task-20261031-082929-mvp-3188b68a --strict`: OK.
- A3 boundary validation: OK.
- `loom validate --strict`: 6 Jobs, 30 Tasks, 30 Task definitions 정상.
- `git diff --check`: 통과.

## 남은 조건과 다음 행동

이 완료 범위는 기술 선정과 문서/계약 연결이다. 패치 잠금·컨테이너/모델 리비전, 실제 설치·CUDA·메모리·한국어 지연·복구 성능은 후속 구현에서 검증한다. 대응 정책 회의, 시연 지역·사례와 모델 정답, 인증·푸시 토큰·HTTPS 진입점은 미정 또는 미검증 상태다. A3 실행 조건이 충족되면 이 문서를 기준으로 실행 기반을 구현한다.

## 8. 두 서버 SSH 별칭 설정과 실제 관리 접속 확인

# 실행 결과

사용자의 직접 요청에 따라 이 Mac의 ~/.ssh/config에 inno-gpu-011 및 inno-server-011 별칭을 추가했다. 보조 별칭 bonghwajigi-gpu와 bonghwajigi-server도 제공한다. 기존 네 개 Host 항목과 연결 설정은 보존했다.

두 별칭으로 ncloud 계정의 실제 SSH 로그인이 성공했고 종료 코드 0이었다. GPU는 2026-10-31 17:43:08 KST, 일반 서버는 17:43:19 KST에 호스트명과 자원을 확인했다. GPU 서버의 L4 1대·4 vCPU·47.05 GiB와 일반 서버의 2 vCPU·7.76 GiB가 기존 환경 문서와 일치한다.

## 검증 근거

- 기존 VPN 접속에서 보관한 ED25519 키와 현재 두 서버의 공개 키가 일치했다. 일반 서버 Tailnet 주소만 known_hosts에 추가하고 엄격한 키 검사로 로그인했다.
- ssh -G로 기본·보조 별칭 네 개의 주소·계정·포트·StrictHostKeyChecking을 확인했다.
- 기존 네 별칭은 동일한 -F 조건으로 설정 전후 유효 설정 전체가 같았다.
- 로컬 config·known_hosts와 각각의 백업은 권한 600이다. config는 사용자 소유로 원자적으로 교체했다.
- 두 원격 조회 및 GPU nvidia-smi의 종료 코드가 모두 0이다. 실제 사양·시각·절차는 docs/V2/delivery/ssh-access.md에 기록했다.
- 비밀번호는 숨김 인증 입력에만 사용했으며 설정·저장소·작업 기록에 보관하지 않았다.
- loom task validate task-20261031-084138-ssh-b8d79a00 --strict: OK.
- loom validate --strict: 6 Jobs, 31 Tasks, 31 Task definitions 정상.
- git diff --check: 통과.

## 범위와 다음 행동

현재 비밀번호 입력 방식이며 원격 인증 설정은 변경하지 않았다. 서버 배치 역할을 기존 설계와 대조했고 모델 설치·학습·API 배포는 수행하지 않았다. 관리 SSH 연결 성공과 수집 파드의 API 연결 검증은 별개이며 후자는 A3에서 수행한다. 다른 구현 Task와 Queue는 시작하지 않았다.
