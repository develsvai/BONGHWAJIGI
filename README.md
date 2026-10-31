# BONGHWAJIGI 봉화지기

여러 출처의 재난 정보를 모아 현재 위치와의 관련성을 평가하고, 사용자 상황에 맞는 행동과 대피 안내를 제공하는 공공 목적의 모바일 서비스입니다.

현재는 **산불 MVP의 서버 프로젝트 스캐폴딩** 단계입니다. 일반 서버(API·DB·큐·정책), GPU 서버(Qwen·임베딩·별도 XGBoost 학습), K8s(수집기)의 코드를 하나의 Python 3.12 패키지로 관리합니다. 3D와 서버 음성은 제외하며 대응 레벨·단계별 알림은 회의 결과를 기다립니다.

**MVP에서는 실제 K8s 수집을 실행하지 않습니다.** 임의로 확보한 자료·뉴스를 시나리오로 재생해 이벤트 수신 API에서 DB/outbox와 긴급·분석 큐로 연결합니다. K8s 구성은 후속 수집을 위해 유지합니다. 입력 초안과 자료 위치는 [시나리오 안내](data/scenarios/README.md)를 따릅니다.

기본 로컬 실행은 프로세스 상태 확인과 미준비 인터페이스를 제공합니다. 실제 수집·사용자 API·정책·예측·푸시는 아직 구현되지 않았습니다. GPU 서버에는 두 Qwen의 실제 서빙과 XGBoost CUDA 실행 검증을 완료했습니다. [모델 사용법과 결과](docs/V2/delivery/gpu-model-readiness.md)를 따릅니다. 모델 가중치나 GPU 라이브러리는 아래 CPU 개발 설치에 포함하지 않습니다.

## 로컬 시작

Python 3.12와 uv를 사용합니다. 프로젝트 루트에서 실행합니다.

```sh
cp .env.example .env
uv sync --frozen --extra server --extra collector --group api-contract
uv run --no-sync uvicorn bonghwajigi.api.app:create_app --factory --reload --port 8000 --no-access-log
```

GPU API 틀은 다른 터미널에서 실행합니다. 현재는 모델을 로딩하지 않으므로 GPU 없이 실행할 수 있습니다.

```sh
uv run --no-sync uvicorn bonghwajigi.gpu_api.app:create_app --factory --port 8001 --no-access-log
```

두 서버 모두 `/health/live`는 200, `/health/ready`는 미구현 상태를 알리는 503을 반환합니다. `/docs`에는 현재 구현된 상태 확인 및 내부 모델 초안만 표시됩니다. 앱 연동 계약 25개 API의 구현 완료를 뜻하지 않습니다.

## 코드와 검증

```text
src/bonghwajigi/
  common/                 설정·상태 확인
  contracts/ domain/      공통 계약·업무 모델 경계
  api/                    일반 서버 API
  ingestion/              K8s 기관 수집·재생
  events/ spatial/        사건 통합·공간 처리
  policy/ retrieval/      검토된 정책·근거 검색
  notifications/          알림 전달
  workers/                긴급·분석·전달 전용 프로세스
  gpu_api/                생성·임베딩 내부 API
  ml/                     피처·학습·평가·CPU 추론
  db/                     DB 모델·트랜잭션
migrations/               Alembic 기반
deploy/                   Docker·Compose·K8s 템플릿
tests/                    실행 및 미준비·의존성 경계 검증
```

```sh
uv run --no-sync ruff check src tests migrations
uv run --no-sync ruff format --check src tests migrations
uv run --no-sync pytest
uv run --no-sync python tools/validate_app_api.py
```

설치 그룹·워커·DB·배치 템플릿과 후속 구현 경계는 [스캐폴딩 안내](docs/V2/delivery/project-scaffold.md)에 정리했습니다. 서버 배포나 GPU 모델 설치는 별도 작업입니다.

## 설계 문서

- [현재 구현 스택](docs/V2/delivery/implementation-stack.md)
- [서버 배치도](docs/V2/02_실시간_서버_배치도.md)
- [앱 API 초안](docs/V2/delivery/app-api-contract.md)
- [관리 SSH 접속](docs/V2/delivery/ssh-access.md)

- [설계 문서 안내](docs/README.md)
- [서비스 목표와 사용자 시나리오](docs/product-and-scenarios.md)
- [데이터 수집과 대응 흐름](docs/architecture-and-data-flow.md)
- [AI 역할과 서버 구성](docs/ai-and-infrastructure.md)
- [결정 사항과 회의 대조](docs/decisions-and-meeting-review.md)
- [UI/UX 인계와 확인 항목](docs/ui-ux-handoff.md)

## 작업 기록

Loom workspace를 한국어로 초기화했습니다. 에이전트 작업 규칙은 [AGENTS.md](AGENTS.md)를 따릅니다. 현재 초기 작업 브랜치는 Loom 기본 정책에 맞춘 `develop`입니다.

```sh
loom status --json
loom resume --json
loom validate --strict
```

인증정보, 개인 위치 이력, 모델 가중치, 회의 녹음과 전체 전사는 저장소에 포함하지 않습니다.
