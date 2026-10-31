# Previous Results

5 older recorded result(s) were omitted. Promote durable context to Job Notes or explicit Context References.

## 9. 설계에 맞춘 Python 서버·수집기·모델 프로젝트 스캐폴딩 구성

# 실행 결과

확정된 스택을 Python 3.12 src 패키지, 설치 extra, uv.lock, 일반·GPU API factory, 공통 설정·내부 인증, 긴급/분석/전달 Celery 앱, DB/Alembic 기반과 Docker/Compose/K8s 초안으로 구성했다. 실제 업무 기능을 완료한 것처럼 표시하지 않는다.

작업 중 사용자 지시를 반영해 MVP는 실제 K8s 수집 없이 수동 확보 자료를 시나리오로 재생하도록 구조를 잡았다. simulation 전용 이벤트 수신 입력과 미준비 경로, JSONL 검사 진입점 및 data/scenarios 안내를 추가했다. K8s 구성은 중지 상태 검사 Job으로 보존했다. 실제 DB/outbox·큐 적재와 재생 전송은 후속 구현이다.

## 검증

- uv lock: 138 패키지 잠금, offline --check 통과. CPU 개발 환경에 69 패키지 설치. torch/Transformers/XGBoost는 설치되지 않음을 확인했다.
- Ruff check 통과, format 검사 대상 33개 Python 파일.
- pytest: 10개 통과. 생존/준비 구분, 미구현 앱 API, 서비스 인증, 모델 미준비, simulation 전용 수신, 긴급 워커의 분석·GPU import 독립성, CLI 미구현 종료를 검증했다.
- 로컬 Uvicorn을 두 프로세스로 실제 실행해 API/GPU API 각각 live=200, ready=503 확인 후 종료했다.
- 기존 OpenAPI 검사: 25 API, 67 스키마, 48 HTTP 예제와 4개 오류 거부 검사 통과.
- 일반·GPU Compose config 통과, K8s YAML 두 파일 구문 확인. 실제 컨테이너·K8s에는 적용하지 않았다.
- Alembic offline SQL과 wheel 빌드 통과. 업무 테이블·migration revision이 없는 현재 상태를 유지했다.

## 다음 작업과 한계

CPU 개발·스캐폴딩만 검증했다. 실제 DB·브로커 통신, outbox·멱등성·업무 핸들러, 수집·모델·정책·알림·운영 인증과 컨테이너 빌드는 미검증이다. Starlette TestClient의 httpx 전환 관련 의존성 경고 1개가 있었고 테스트 실패는 없다.

사용자가 스캐폴딩 완료 직후 GPU 서버의 세 모델 실행 준비를 직접 지시했다. 이 Task 완료 후 별도 Task로 두 Qwen의 실제 로딩·샘플 추론과 XGBoost CUDA 준비를 실행한다. 산불 정답·학습 목표와 대응 레벨은 임의로 확정하지 않는다.

최종 Task boundary strict 및 workspace strict(6 Jobs/32 Tasks)와 git diff --check를 통과했다.

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
