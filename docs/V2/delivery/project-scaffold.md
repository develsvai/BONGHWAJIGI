# 서버 프로젝트 스캐폴딩

기준일: 2026-10-31. Loom: `task-20261031-084830-python-03ca0991`.

후속 변경: [GPU 모델 준비 Task](gpu-model-readiness.md)에서 실제 모델 로딩·인증 API·입력 제한·직렬 실행을 추가했다. 아래 미준비 설명은 기본 로컬 설정에 해당하며 GPU 서버의 활성화된 모델 서비스는 별도 준비 상태 200을 제공한다. 일반 API·시나리오 DB/큐 적재는 계속 미구현 상태다.

[구현 스택](implementation-stack.md)과 [서버 배치도](../02_실시간_서버_배치도.md)를 Python 3.12 프로젝트 구조로 옮겼다. 이번 산출물은 로컬 개발 기반이며 실제 기관 수집·사용자 API·정책·예측·알림이나 원격 배포를 완료한 상태가 아니다. 기존 A3의 실제 연결·복구 검증은 PENDING으로 남는다.

사용자의 작업 중 추가 지시를 우선한다. **MVP 입력은 실제 K8s 수집이 아니라 수동 확보 자료의 시나리오 재생**이다. K8s 구성은 유지하며 자료 확보 → 시나리오 JSONL → 일반 서버 이벤트 수신 API → DB/outbox → 긴급·분석 큐를 목표 경로로 삼는다. 수신 초안 `/internal/v1/scenario-events`는 현재 인증 후에도 503이며 DB 적재를 가장하지 않는다. `ingestion.replay --check`는 입력 계약 검사만 수행한다. [자료 안내](../../../data/scenarios/README.md)를 따른다.

## 패키지와 실행 환경

루트 `pyproject.toml`과 `uv.lock`으로 하나의 `src/bonghwajigi` 패키지를 관리하고, 설치하는 extra와 가상환경을 실행 위치별로 나눈다. 공통 import나 API 시작 과정에서 torch·Transformers를 불러오지 않는다.

| 경로 | 역할과 현재 상태 |
| --- | --- |
| `common` | 환경변수·생존/준비 상태 확인 |
| `contracts`, `domain` | 공통 자료·업무 모델 경계. 내부 모델 요청 초안 외 DTO는 B2/E1에서 구현 |
| `api` | 일반 서버 FastAPI factory. 현재 health만 제공 |
| `ingestion` | K8s 수집·재생 진입점. `--check`만 제공 |
| `events`, `spatial` | 사건 통합·정정/해제·좌표·발령 대상의 후속 구현 위치 |
| `policy`, `retrieval` | 검토된 지침·사용자 상태 적용, 출처가 있는 문서 검색의 후속 구현 위치 |
| `notifications` | PushGateway·전송 이력의 후속 구현 위치 |
| `workers` | 긴급·분석·전달 전용 Celery 앱과 실패를 명시하는 미구현 작업 |
| `gpu_api` | 별도 FastAPI factory. 모델 미준비·인증 경계를 제공 |
| `ml` | XGBoost 피처·학습·평가·CPU 추론 위치. 현재 `--check`만 제공 |
| `db`, `migrations` | SQLAlchemy Base와 Alembic. 업무 테이블·revision은 아직 없음 |

CPU 개발 환경은 다음처럼 설치한다. 기본 `dev` 그룹과 추가 `api-contract` 그룹이 정적 검사·테스트·기존 OpenAPI 검사를 제공한다.

```sh
cp .env.example .env
uv sync --frozen --extra server --extra collector --group api-contract
```

| 환경 | 의존성 선택 | 별도 가상환경 예시 |
| --- | --- | --- |
| 일반 서버 API/워커 | `--extra server --no-dev` | `.venv` |
| 수집기 | `--extra collector --no-dev` | `.venv-collector` |
| GPU 생성/임베딩 | `--extra gpu --no-dev` | `.venv-gpu` |
| XGBoost 학습 | `--extra ml --no-dev` | `.venv-ml` |
| 일반 서버 모델 추론 추가 | `--extra server --extra ml --no-dev` | `.venv` |

uv는 동기화 시 선택하지 않은 extra의 패키지를 제거할 수 있다. 개발 환경에서 여러 역할을 함께 확인한다면 필요한 extra를 매번 함께 지정한다. 별도 환경은 `UV_PROJECT_ENVIRONMENT=.venv-collector uv sync --frozen --extra collector --no-dev` 방식으로 선택한다.

GPU extra의 Linux x86_64 torch는 공식 CUDA 12.8 인덱스를 사용한다. 다른 플랫폼은 PyPI 해석 결과를 사용한다. GPU/ML 의존성도 잠금에 포함했지만 이번 실제 설치·실행 검증은 CPU 개발 환경만 수행한다. D3/C3에서 드라이버·CUDA·실제 모델 revision·실행 메모리를 확인한 뒤 해당 환경을 설치한다. XGBoost GPU 학습과 Qwen 서빙은 별도 시간에 실행한다. 잠금 파일에 CUDA 패키지가 있다고 로컬에 설치된 것은 아니다.

## 실행 및 미준비 상태

```sh
uv run --no-sync uvicorn bonghwajigi.api.app:create_app --factory --port 8000 --no-access-log
uv run --no-sync uvicorn bonghwajigi.gpu_api.app:create_app --factory --port 8001 --no-access-log
```

두 명령은 각각 다른 터미널에서 실행한다. 기본 바인딩은 localhost다. GPU API는 현재 모델을 로딩하지 않으므로 CPU 환경에서도 틀을 실행할 수 있다.

| 경로 | 현재 응답 |
| --- | --- |
| 양쪽 `GET /health/live` | 프로세스 생존을 나타내는 200 |
| 양쪽 `GET /health/ready` | 미구현 구성 요소를 표시하는 503 |
| GPU `POST /internal/v1/generate` | 서비스 토큰 미설정 503, 인증 실패 401, 인증 후에도 모델 미준비 503 |
| GPU `POST /internal/v1/embeddings` | 동일 인증 경계, 인증 후 임베딩 모델 미준비 503 |

내부 모델 경로·요청은 연결 준비용 초안이며 앱 `/v1` 계약과 별개다. 생성 요청의 문자 수와 출력 상한만 검사하며 실제 tokenizer의 전체 토큰 검사·모델 로딩·실행 직렬화·검색·생성은 D3에서 구현한다. 비어 있는 임베딩이나 모의 생성문을 성공 응답으로 돌려주지 않는다.

기존 [앱 OpenAPI 초안](api/openapi.yaml)은 그대로 유지했다. 아직 사용자 API를 붙이지 않았으므로 `/v1/home` 등은 404다. 자동 생성 `/docs`의 health·내부 초안과 기존 앱 API 전체 명세를 혼동하지 않는다. 실제 준비 상태는 DB·브로커·모델·업무 핸들러를 연결하고 검사한 뒤 변경한다.

```sh
uv run --no-sync python -m bonghwajigi.ingestion --check
uv run --no-sync python -m bonghwajigi.ml --check
```

위 명령은 외부 호출·학습 없이 `not_implemented`를 표시하고 0으로 종료한다. `--check` 없이 실행하면 미구현 이유와 종료 코드 2를 반환한다. 수집기 실행을 성공한 것처럼 기록하지 않는다.

## 워커와 DB

```sh
uv run --no-sync celery -A bonghwajigi.workers.urgent:app worker -Q urgent --concurrency=1
uv run --no-sync celery -A bonghwajigi.workers.analysis:app worker -Q analysis --concurrency=1
uv run --no-sync celery -A bonghwajigi.workers.delivery:app worker -Q delivery --concurrency=1
```

각 워커는 별도 프로세스다. 명시적으로 설정한 Redis 주소만 사용하며 큐 자동 생성은 끈다. 긴급 워커는 분석·GPU 모듈을 import하지 않는다. 실제 이벤트를 보내지 않는다. placeholder 작업은 `NotImplementedError`로 실패하며 저장·정책 적용·전송을 가장하지 않는다. outbox·멱등성·재전달 보장은 아직 구현하지 않았다.

Alembic은 `BONGHWA_DATABASE_URL`의 psycopg 연결을 사용한다. 업무 테이블이 없으므로 migration revision도 만들지 않았다. 후속 구현에서 모델 import를 `migrations/env.py`에 연결하고 revision을 생성·검토한다. `alembic upgrade head` 자체가 스키마 완성이나 DB 연결 성공을 뜻하지 않는다.

## 배치 템플릿

- `deploy/compose/general.yaml`: PostgreSQL 16/PostGIS/pgvector, Redis 7.4 AOF, API와 세 워커. DB·Redis·API 포트는 로컬에만 공개한다.
- `deploy/compose/gpu.yaml`: GPU 1대 접근을 사용하는 단일 API 프로세스, 별도 서비스 토큰과 모델 캐시 볼륨. 현재 API 코드는 모델을 로딩하지 않는다.
- `deploy/docker/Python.Dockerfile`: extra를 선택하는 Python 3.12 이미지. root가 아닌 사용자로 실행하고 `.env`, `.loom`, 가중치와 비밀 파일은 빌드 컨텍스트에서 제외한다.
- `deploy/docker/Postgres.Dockerfile`, `deploy/postgres/001-extensions.sql`: 개발 DB 확장 설치·초기화 초안. 실제 이미지 빌드와 확장 버전은 A3에서 검증한다. 초기화 SQL은 새 DB 볼륨에만 적용된다.
- `deploy/k8s`: 전용 namespace와 중지 상태의 설치 검사 Job. 이미지 주소는 자리표시자다. 실제 수집 Deployment·egress·서비스 인증·운영 적용은 후속 작업이다.

로컬 Compose 준비와 구성 검사는 아래와 같다. 실제 `up`은 로컬 컨테이너·볼륨을 생성한다. 이번 작업에서는 원격 서버나 K8s에 적용하지 않았다.

```sh
docker compose --env-file .env -f deploy/compose/general.yaml config --quiet
docker compose --env-file .env -f deploy/compose/general.yaml up --build
```

Compose healthcheck는 생존 검사만 사용한다. Docker의 healthy 표시가 업무 준비 완료를 뜻하지 않으며 실제 준비 여부는 `/health/ready`로 구분한다. 운영용 TLS·도메인·접근 정책·자격 주입과 이미지 digest 고정은 A3/E1의 후속 작업이다. SSH 비밀번호는 어떤 템플릿에도 넣지 않았다.

## 검증과 다음 구현

```sh
uv run --no-sync ruff check src tests migrations
uv run --no-sync ruff format --check src tests migrations
uv run --no-sync pytest
uv run --no-sync python tools/validate_app_api.py
```

CI도 CPU 환경에서 같은 검사를 실행한다. 테스트는 생존과 준비의 구분, 모델 인증 및 미준비 처리, 긴급 워커의 import 독립성, 미구현 수집·학습 명령의 실패 동작을 확인한다. 실제 DB·Redis 통신, 컨테이너 실행, CUDA·모델 성능과 원격 네트워크 복구는 별도 검증이다.

후속 구현은 B2의 자료 계약, A3의 시나리오 수신·DB/큐 연결, D4의 공식 원문 우선 처리, D3/C3의 모델 준비, E1/E2의 사용자 인증·API를 이 틀에 연결한다. 실제 K8s 수집과 파드 egress는 MVP 수집 실행의 선행 조건으로 삼지 않는다. 기존 A3/B3의 상시 수집 계약과 달라지는 범위는 사용자 추가 지시가 우선하며 Job 노트에 남긴다. D1의 대응 레벨·단계별 알림·임계값은 사용자 회의 결과를 계속 기다린다.

사용자는 스캐폴딩 완료 직후 GPU 서버의 두 Qwen 모델과 XGBoost 실행 준비를 직접 지시했다. 해당 원격 설치·실측은 별도 후속 Task에서 이어가며 이 스캐폴딩 결과와 구분한다.

의존성 구성 방식은 [uv PyTorch 연동](https://docs.astral.sh/uv/guides/integration/pytorch/), CUDA 인덱스는 [PyTorch 공식 배포](https://pytorch.org/get-started/previous-versions/), 큐 분리는 [Celery 공식 라우팅](https://docs.celeryq.dev/en/stable/userguide/routing.html)을 참조했다. 공식 문서의 지원 설명과 이 저장소의 실제 원격 실행 검증을 구분한다.
