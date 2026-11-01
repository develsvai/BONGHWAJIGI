# Previous Results

2 older recorded result(s) were omitted. Promote durable context to Job Notes or explicit Context References.

## 6. 두 제공 서버를 기존 Tailscale 망에 연결하고 클러스터 통신 검증

# 결과

develop에서 두 제공 서버에 공식 Tailscale 1.104.4를 설치하고 기존 tail2dac17.ts.net 등록을 완료했다. GPU는 100.65.45.63, 일반 서버는 100.116.5.9이며 두 장치 모두 Running, Online, health 경고 없음, 서비스 active/enabled다.

사용자가 정확한 일반 서버 자격 증명을 제공해 로그인에 성공했다. 별도로 저장 직전 승인한 접근 규칙 1개를 추가했다. 기존 관리자 그룹, 클러스터 마스터와 두 서버를 출발지로 하고 두 서버 IPv4의 TCP 22만 허용한다. 기존 정책 4개를 유지했다.

## 검증 근거

- Tailnet IPv4로 두 서버에 실제 SSH 로그인해 hostname과 ncloud 사용자를 확인했다. 기존 VPN 접속에서 확인한 호스트키와 대조했다.
- 클러스터 마스터의 노드 네트워크에서 두 서버 TCP 22 각각 성공했다.
- 두 서버 상호 TCP 22와 OpenSSH 배너 수신이 성공했다.
- 노드·일반 파드 22건 검사에서 마스터 2건 성공, 워커 노드 10건 및 일반 파드 10건 실패를 기록했다.
- 기존 클러스터는 6대 Ready, 실행 파드 84개 모두 준비 상태다. 서버 기본 경로와 기관 DNS·HTTPS 동작을 유지했고 일반 서버 실패 서비스는 없다. GPU의 기존 실패 서비스 2개는 동일하다.
- 인증키와 비밀번호를 저장소·보고서에 기록하지 않았다. 실제 검사 근거와 운영 범위는 docs/V2/delivery/tailnet-connectivity.md 및 evidence JSON에 남겼다.

## 남은 조건과 다음 행동

이 Task의 두 서버 등록 및 기존 클러스터 연결 지점 검증은 완료했다. 일반 수집 파드는 전용 Tailscale egress 또는 사이드카와 프로젝트 접근 정책이 필요하다. A3에서 API 주소·포트·TLS·서비스 인증을 정한 뒤 실제 수집 파드 → 일반 서버, 일반 서버 → GPU API를 검증한다. SSH 검사로 미구현 API를 통과 처리하지 않는다.

장치 키는 조회 시 2027-04-29 만료이며 갱신 정책이 필요하다. 재부팅 자동 시작 설정만 확인했고 실제 재부팅은 하지 않았다. 기존 HeoNey 문서화 RUNNING Task와 다른 22개 PENDING Task는 실행하지 않았다.

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
