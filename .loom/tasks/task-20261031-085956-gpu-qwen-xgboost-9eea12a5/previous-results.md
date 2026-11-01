# Previous Results

4 older recorded result(s) were omitted. Promote durable context to Job Notes or explicit Context References.

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
