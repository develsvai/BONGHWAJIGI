# BONGHWAJIGI 봉화지기

여러 출처의 재난 정보를 모아 현재 위치와의 관련성을 평가하고, 사용자 상황에 맞는 행동과 대피 안내를 제공하는 공공 목적의 모바일 서비스입니다.

현재는 **산불 3단계 MVP의 사설망 서버 구현**입니다. 일반 서버(API·DB·큐·정책), GPU 서버(Qwen·임베딩·별도 XGBoost 학습), K8s(수집기) 구성을 관리합니다. 사용자 확정 단계는 **1 경고 · 2 대피 · 3 위급**입니다. [서버 접속·운영](docs/V2/delivery/mvp-server-runbook.md), [앱 API 실행 계약](docs/V2/delivery/mvp-app-api.md), [정책 기준](docs/V2/delivery/response-policy.md)을 먼저 확인하세요.

**MVP에서는 실제 K8s 수집을 실행하지 않습니다.** 임의로 확보한 자료·뉴스를 시나리오로 재생해 이벤트 수신 API에서 DB/outbox와 긴급·분석 큐로 연결합니다. K8s 구성은 후속 수집을 위해 유지합니다. 입력 초안과 자료 위치는 [시나리오 안내](data/scenarios/README.md)를 따릅니다.

사용자 인증·프로필·위치·공식 경보·개인 정책·변경 조회와 모의 알림을 구현했습니다. 실제 예측 연결은 제외해 unavailable/null로 제공하고, Firebase 준비 전까지 실제 단말 푸시는 전송하지 않습니다. GPU 모델 사용법은 [모델 준비 결과](docs/V2/delivery/gpu-model-readiness.md)를 따릅니다. 모델 가중치나 GPU 라이브러리는 아래 CPU 개발 설치에 포함하지 않습니다.

분석 경로는 **시나리오 수신 → DB/outbox → Redis 분석 큐 → 인터넷 뉴스 검색·GPU 임베딩 → pgvector 검색 → Qwen 통합**입니다. [분석·검색 흐름](docs/V2/delivery/analysis-retrieval-flow.md)에 최초 구성과 검색 계약이 있습니다. 긴급 경보는 별도 큐에서 최신 위치와 구역을 대조해 모델을 기다리지 않고 원문과 알림을 생성합니다.

공식 경보의 과거 발령 기록을 포함한 이전 실제 모델 결과는 [경보 포함 Qwen3 통합 결과](docs/V2/delivery/qwen-integration-result.md)에 보관했습니다. 과거 자료와 합성 시연을 현재의 실제 경보로 표시하지 않습니다.

정책 루프는 새 관측·프로필·위치·현재 상태·공식 경보·지침 변경과 주기 만료를 반영해 사용자별 계획을 갱신합니다. 단계는 확정 규칙이 결정하고 Qwen은 자료 요약을 제공합니다. 자료가 부족하거나 오래되면 확인 중으로 바꾸고 옛 행동을 숨깁니다. 이번 서버의 실제 실행 범위와 제외 항목은 [배포 검증 기록](docs/V2/delivery/mvp-server-evidence.json)을 따릅니다.

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

기본 예시 설정은 기능이 비활성이므로 `/health/live`는 200, `/health/ready`는 503입니다. MVP 배포 설정에서는 DB migration·Redis 연결을 확인한 readiness가 200이며 `/docs`와 `/openapi.json`에 실행 API가 표시됩니다. GPU readiness는 모델을 실제 활성화한 서버에서만 준비 완료를 반환합니다.

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

최초 설치 그룹·워커·배치 틀은 [스캐폴딩 안내](docs/V2/delivery/project-scaffold.md)에 보존했습니다. 현재 일반 서버 배포는 `deploy/compose/mvp.yaml`과 운영 문서를 따릅니다.

모바일 앱은 `apps/mobile` 서브모듈에 검증된 커밋을 고정합니다. [초기화·배포 소스 확인](docs/V2/delivery/mobile-submodule-deployment.md)과 앱 저장소의 Android 빌드·검증 기록을 따릅니다.

## 설계 문서

- [현재 구현 스택](docs/V2/delivery/implementation-stack.md)
- [서버 배치도](docs/V2/02_실시간_서버_배치도.md)
- [현재 앱 API](docs/V2/delivery/mvp-app-api.md) · [이전 화면 API 초안](docs/V2/delivery/app-api-contract.md)
- [관리 SSH 접속](docs/V2/delivery/ssh-access.md)

- [설계 문서 안내](docs/README.md)
- [서비스 목표와 사용자 시나리오](docs/V1/product-and-scenarios.md)
- [데이터 수집과 대응 흐름](docs/V1/architecture-and-data-flow.md)
- [AI 역할과 서버 구성](docs/V1/ai-and-infrastructure.md)
- [결정 사항과 회의 대조](docs/V1/decisions-and-meeting-review.md)
- [UI/UX 인계와 확인 항목](docs/V1/ui-ux-handoff.md)

## 작업 기록

Loom workspace를 한국어로 초기화했습니다. 에이전트 작업 규칙은 [AGENTS.md](AGENTS.md)를 따릅니다. 현재 초기 작업 브랜치는 Loom 기본 정책에 맞춘 `develop`입니다.

```sh
loom status --json
loom resume --json
loom validate --strict
```

인증정보, 개인 위치 이력, 모델 가중치, 회의 녹음과 전체 전사는 저장소에 포함하지 않습니다.
