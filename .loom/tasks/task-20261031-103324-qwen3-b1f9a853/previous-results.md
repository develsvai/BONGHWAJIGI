# Previous Results

6 older recorded result(s) were omitted. Promote durable context to Job Notes or explicit Context References.

## 10. GPU 서버에 두 Qwen 모델과 XGBoost를 설치하고 실제 사용 준비 검증

# 실행 결과

사용자의 직접 지시에 따라 inno-gpu-011의 /home1/ncloud/bonghwajigi에 격리된 GPU·ML 환경을 설치했다. 두 Qwen 모델의 고정 revision 가중치를 내려받고 실제 GPU에서 함께 로딩했다. XGBoost는 별도 환경에서 실제 합성 CUDA 학습·저장·CPU 재로딩을 검증했다.

GPU API와 입력 계약을 실제 실행 코드로 연결하고 단일 요청 실행, 입력+출력 4096토큰 제한, 서비스 인증, float32 단위 길이 임베딩을 구현했다. 모델 상주와 학습은 공통 파일 잠금으로 동시에 실행되지 않는다. 기본 로컬 GPU 비활성 상태와 일반 API의 미준비 상태는 유지했다.

## 실제 검증

- torch 2.11.0+cu128 / CUDA runtime 12.8, Transformers 4.57.6, Sentence Transformers 5.7.0, NVIDIA L4 확인.
- Qwen3-4B-Instruct-2507 revision cdbee75f17c01a7cc42f958dc650907174af0554 실제 한국어 생성. 입력 29/출력 9토큰, 약 845ms.
- Qwen3-Embedding-0.6B revision 97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3 실제 1024차원 문서·질의 벡터 생성. 문서 2개 약 124ms, 정규화 길이 1.0000000383/1.0000000101.
- 실제 모델 API 무인증 401, 토큰 한도 초과 422. 서빙 중 합성 학습 시도는 실패하고 산출물이 생성되지 않았다.
- 두 모델 호출 후 GPU 9134/23034 MiB. 설치 후 디스크 약 61.23 GiB 여유.
- XGBoost 3.4.1: cuda:0에서 합성 5000행/16피처/20회 학습 약 0.319초. 저장 후 CPU 재로딩 최대 절대 차이 1.19e-7.
- 사용자 서비스 active/enabled, Linger=yes, localhost 127.0.0.1:8001만 리스닝. 서비스 토큰 파일 600. 서비스 재시작 및 기존 SSH 종료 후 새 로그인에서도 ready=200 확인.
- 로컬 pytest 12 통과와 Ruff check 통과. 기존 CPU 환경에 GPU 라이브러리를 추가하지 않았다.

## 운영·한계

바로 사용할 서버 CLI, 모델 API, 학습 실행 방법과 정확한 환경 경로는 docs/V2/delivery/gpu-model-readiness.md 및 비밀정보가 없는 evidence JSON에 기록했다. 서비스 토큰은 서버에서 생성·보관했으며 SSH 비밀번호를 보관하지 않았다. 전역 Python·기존 서비스·공개 포트·Tailscale 정책·K8s를 변경하지 않았다.

이 결과는 모델 실행 준비다. 합성 부스터는 산불 실모델이 아니며 실제 예측·정책 임계값에 사용하지 않는다. 실제 자료 품질·최대 입력/배치·동시 부하·장기 운영·실제 재부팅은 검증하지 않았다. D3/C1~C5의 자료·품질 검증과 A3의 일반 서버 연결은 후속 작업이다.

최종 검증: Ruff format, 기존 API 25/67/48/4, GPU Compose config, Task boundary strict와 workspace strict(6 Jobs/33 Tasks), git diff --check 통과.

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
