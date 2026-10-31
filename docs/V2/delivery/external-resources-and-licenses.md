# 봉화지기 외부 자원 활용 내역과 라이선스

최종 작성일: **2026-11-01 KST**. 구현·수집·설치 기록 기준: **2026-10-31**. 발표 지침의 **구분 · 명칭 · 용도 · 라이선스** 형식으로 작성한 서버·GPU·학습 자원 명세다. 최초 서버 조사에서는 앱을 제외했다. 2026-11-01 Android 지도 연결 후속 작업에서 확인한 네이버 지도 자원은 마지막 절에 추가했다. 앱의 나머지 폰트·이미지·단말 SDK 전체를 조사한 목록은 아니다.

`BONGHWAJIGI`의 코드·배포 설정·시연 기록·데이터 출처·두 잠금 파일 및 로컬/GPU 가상환경의 배포 메타데이터를 대조했다. 아래에서 **사용**은 실제 호출·설치·실험 근거가 있는 항목, **구성**은 코드/설정만 있는 항목, **조사**는 카탈로그·문서·샘플을 살펴본 항목이다. 설치는 해당 기능의 실제 실행과 다르며, 데이터 다운로드는 학습 사용과 다르다.

라이선스는 패키지 코드, 모델 가중치, 데이터, 호스팅/API 약관을 구분한다. 공개 URL·무료 다운로드·API 승인만으로 재배포나 상업적 이용이 모두 허용된다고 표시하지 않는다. 정확한 조건을 확인하지 못한 자원은 그 사실을 해당 행에 남긴다. 개별 OS 이미지 내부의 모든 시스템 패키지를 재귀 분석한 바이너리 SBOM은 아니며, Python 직접·전이 의존성의 전수 목록과 인프라 구성요소를 제공한다.

## 1. 사전 보유 코드와 직접 개발 범위

| 구분 | 명칭 | 용도 | 라이선스 |
| --- | --- | --- | --- |
| 사전 보유 코드 | **해당 없음** | 사용자가 “사전 보유 코드 없음”으로 확인. 행사 개회식 전에 작성·보유한 코드를 이번 저장소에 가져온 항목 없음. 디자인·자료의 사전 보유 여부까지 확인한 답변은 아님 | 해당 없음 |
| 기타 | 직접 개발한 봉화지기 서버·학습 코드 | 이벤트 수신·DB 큐·검색 연결·모델 API·정책 규칙·알림 계약·시나리오 재생·학습/평가/출처 추적 | 프로젝트 자체 배포 라이선스는 저장소에 명시되지 않음. 외부 의존성의 MIT/Apache 라이선스가 프로젝트 전체에 자동 적용되는 것은 아님 |
| 기타 | 팀 제공 설계·화면 자료 | `docs/HeoNey/`의 기획서와 `disaster.png`, `nomal_home.png` 등 현재 작업의 요구사항 자료 | 사용자 제공 자료. 독립적인 외부 이미지·폰트의 권리 내역은 이 서버 감사에서 확인하지 않음; 앱 자원 목록은 별도 범위 |

직접 구현한 검색·통합·정책 코드와 외부 모델 자체를 구분한다. Qwen 모델 가중치를 팀이 개발하거나 새로 사전학습했다고 표기하지 않는다. XGBoost 라이브러리를 이용한 데이터 가공·특성 구성·학습·검증은 직접 개발 범위이며, 현재 연구 모델은 실제 사용자 대응 단계 결정에 연결하지 않는다. 근거: [실행 검증](mvp-server-evidence.json), [모델 개선 기록](korea-wildfire-improvement.md).

## 2. 서버에서 사용한 API·모델·참고 콘텐츠

| 구분 | 명칭 | 용도 | 라이선스 |
| --- | --- | --- | --- |
| 외부 API | Google News RSS `https://news.google.com/rss/search` | **실제 사용** — 산불 검색 제목·최대 500자 설명·링크·매체·발표 시각 확보. `src/bonghwajigi/retrieval/web_search.py`에 구현, 실제 검색 근거가 `analysis-retrieval-evidence.json` 및 `qwen-integration/retrieval-handoff.json`에 있음. 기사 본문 크롤링은 하지 않음 | [Google 서비스 약관](https://policies.google.com/terms) 및 개별 기사 권리. 공개 RSS 접근이 콘텐츠 재배포·모델 학습·상업적 이용에 대한 포괄 허가를 뜻하지 않음. 공식 상용 검색 API 계약/SLA로 확인된 경로가 아님 |
| 기타 | 대한민국 정책브리핑 `newsId=148940993` | **실제 시연 사용** — 2025년 전국 산불경보 확대의 원자료. `data/scenarios/yeongdeok-integration.json` | [해당 문서](https://www.korea.kr/news/policyNewsView.do?newsId=148940993)에 **텍스트에 한하여 공공누리 제1유형(출처표시)** 명시. 사진·이미지·영상은 별도 권리자 허락 대상 |
| 기타 | 행정안전부 안전한TV `[사회재난] 산불 발생 시 행동 요령`, `idx=2759` | **실제 시연 사용** — 같은 시나리오의 참고 행동요령, 검색 후 Qwen 통합 근거. 승인 정책 DB로 등록한 자료는 아님 | [해당 문서](https://www.safetv.go.kr/base/video/view?idx=2759&menuLevel=&menuNo=&playlistManagementIdx=8)에 **공공누리 제4유형: 출처표시·상업적이용금지·변경금지** 표시. 상업적 재사용/변형 권한이 있다고 처리하면 안 됨 |
| 기타 | 국민안전24 산불 국민행동요령 | **실제 코드 참조** — `src/bonghwajigi/policy/three_stage.py`의 근거 URL | [원문](https://www.safekorea.go.kr/safekorea-kor/acts/nacts/action-guide.do?category=forestFires&menuSn=4) 확인. 해당 페이지에서 정확한 공공누리 유형/재사용 조건은 확인되지 않음. 정부 웹사이트라는 사실로 제1유형을 부여하지 않음 |
| 기타 | 중앙일보·연합뉴스TV·연합뉴스·경향신문·MBC 뉴스 | **실제 검색 결과에 포함** — `qwen-integration/retrieval-handoff.json`과 `personal-policy-loop-evidence.json`에 다섯 매체의 제목/설명/URL이 남음. Google News를 통해 확보 | 언론사별 저작권·이용약관 적용, 콘텐츠별 개방 라이선스 미확인. [중앙일보](https://www.joongang.co.kr/), [연합뉴스TV](https://www.yonhapnewstv.co.kr/), [연합뉴스](https://www.yna.co.kr/), [경향신문](https://www.khan.co.kr/), [MBC 뉴스](https://imnews.imbc.com/). 매체 사이트 링크는 출처이며 재사용 허가 근거가 아님 |
| 외부 API | Firebase Cloud Messaging HTTP v1 | **구현, 실발신 미사용** — `FcmSender`가 `/v1/projects/{project}/messages:send` 호출. 현재 배포는 simulation이고 실제 프로젝트/자격 파일/기기 토큰 미제공 | [Firebase 서비스별 약관](https://firebase.google.com/terms)에 FCM은 Google APIs Terms 및 Firebase Data Processing and Security Terms 적용. Firebase SDK 오픈소스 라이선스를 서비스 이용권으로 해석하지 않음 |
| 외부 API | Google OAuth 2.0 token endpoint | **FCM 어댑터 내 구현, 실호출 미확인** — 서비스 계정 JWT를 `https://oauth2.googleapis.com/token`에 교환하는 FCM 인증 경로 | [Google APIs Terms](https://developers.google.com/terms). 앱 사용자 인증은 자체 JWT이며 Firebase Authentication 사용으로 기록하면 안 됨 |
| 기타 | Qwen3-4B-Instruct-2507, revision `cdbee75f17c01a7cc42f958dc650907174af0554` | **GPU 실제 사용** — 근거 자료 정리·생성. `.venv-gpu`, BF16, Transformers SDPA, localhost 인증 API | [고정 revision의 공식 LICENSE](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507/blob/cdbee75f17c01a7cc42f958dc650907174af0554/LICENSE): Apache-2.0. 모델 가중치 라이선스와 입력 문서/뉴스 재사용 권리는 별개 |
| 기타 | Qwen3-Embedding-0.6B, revision `97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3` | **GPU 실제 사용** — 문서·검색 질의를 1024차원 정규화 벡터로 변환 | [고정 revision의 공식 모델 카드](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B/blob/97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3/README.md): Apache-2.0 선언. 해당 revision에는 별도 LICENSE 파일이 없으며 카드·공식 metadata를 근거로 기록 |
| 기타 | Hugging Face Hub | **실제 다운로드** — Qwen 모델을 `/home1/ncloud/bonghwajigi/models/hub`에 고정 revision으로 내려받음. 런타임은 `local_files_only=True` | 모델별 라이선스에 더해 [Hugging Face Hub 이용약관](https://huggingface.co/terms-of-service). Hugging Face 유료 inference endpoint 사용은 확인되지 않음 |

APNs 직접 전송, 카카오/네이버/Google Maps/Mapbox 지도 API, 경로 탐색 서비스, OpenAI API, vLLM, LangChain은 현 서버 실행 코드·의존성에서 사용 확인되지 않는다. CesiumJS·MeloTTS는 초기 설계 검토 항목이며 현재 산불 MVP의 3D/서버 음성 제외 범위다. 실제 사용 목록과 분리해야 한다. `example.invalid` 링크는 합성 자료 자리표시자다.

## 3. 주요 오픈소스와 직접 의존성

아래 버전은 현재 `uv.lock`의 해결 결과다. 서버·개발 설치 확인은 `.venv` metadata 및 기존 GPU readiness 기록으로 구분했다. GPU 환경은 torch `2.11.0+cu128` 실측이며 다른 플랫폼 분기의 torch `2.15.0`을 GPU 설치 버전으로 적으면 안 된다. `hatchling>=1.27,<2`는 빌드 요구이며 lock에 실제 build-isolation 버전이 고정돼 있지 않다.

| 구분 | 명칭 | 용도 | 라이선스 |
| --- | --- | --- | --- |
| 오픈소스 | FastAPI 0.162.0 | **실제 코드·설치** — HTTP API·OpenAPI | [MIT](https://raw.githubusercontent.com/fastapi/fastapi/master/LICENSE) |
| 오픈소스 | pydantic-settings 2.16.2 | **실제 코드·설치** — 설정 검증·환경변수 로딩 | [MIT](https://raw.githubusercontent.com/pydantic/pydantic-settings/main/LICENSE) |
| 오픈소스 | Uvicorn 0.54.0 | **실제 실행·설치** — ASGI API 실행 | [BSD-3-Clause](https://raw.githubusercontent.com/encode/uvicorn/master/LICENSE.md) |
| 오픈소스 | SQLAlchemy 2.1.6 | **실제 코드·설치** — DB 모델·트랜잭션·쿼리 | [MIT](https://raw.githubusercontent.com/sqlalchemy/sqlalchemy/main/LICENSE) |
| 오픈소스 | psycopg 3.3.6 / psycopg-binary 3.3.6 | **실제 코드·설치** — PostgreSQL 연결 | [LGPL-3.0-only](https://raw.githubusercontent.com/psycopg/psycopg/master/LICENSE.txt), 설치 metadata 확인. binary wheel에 포함된 libpq 등 별도 고지 유지 |
| 오픈소스 | Alembic 1.20.1 | **실제 실행·설치** — DB schema migration | [MIT](https://raw.githubusercontent.com/sqlalchemy/alembic/main/LICENSE) |
| 오픈소스 | GeoAlchemy2 0.20.0 | **설치·선언, 현재 import 없음** — 후속 PostGIS ORM 통합 준비 | [MIT](https://github.com/geoalchemy/geoalchemy2). 설치 `COPYING.rst` 및 공식 저장소 MIT 표기 확인 |
| 오픈소스 | pgvector Python 0.5.1 | **실제 코드·설치** — SQLAlchemy 벡터 컬럼·검색 | [MIT](https://raw.githubusercontent.com/pgvector/pgvector-python/master/LICENSE.txt). DB 확장 pgvector의 PostgreSQL License와 구분 |
| 오픈소스 | Celery 5.6.3 (`redis` extra) | **실제 실행·설치** — 긴급·분석·전달 워커 | [BSD-3-Clause](https://raw.githubusercontent.com/celery/celery/main/LICENSE). 문서 자체는 별도 CC-BY-SA-4.0 |
| 오픈소스 | PyJWT 2.15.1 (`crypto` extra) | **실제 코드·설치** — 자체 사용자 JWT, FCM 서비스 계정 JWT | [MIT](https://raw.githubusercontent.com/jpadilla/pyjwt/master/LICENSE) |
| 오픈소스 | prometheus-client 0.26.0 | **설치·선언, 현재 지표 노출 import 없음** — 계측 도구 준비 | [Apache-2.0](https://raw.githubusercontent.com/prometheus/client_python/master/LICENSE) **AND BSD-2-Clause**. [NOTICE](https://raw.githubusercontent.com/prometheus/client_python/master/NOTICE)의 내장 decorator 고지 포함; 설치 metadata도 AND로 표기 |
| 오픈소스 | HTTPX 0.28.1 | **실제 코드·설치** — 내부 모델 API·RSS·FCM HTTP 요청 및 테스트 | [BSD-3-Clause](https://raw.githubusercontent.com/encode/httpx/master/LICENSE.md) |
| 오픈소스 | defusedxml 0.7.1 | **실제 코드·설치** — RSS XML 파싱 | [PSF-2.0](https://raw.githubusercontent.com/tiran/defusedxml/main/LICENSE) |
| 오픈소스 | PyTorch 2.11.0+cu128 | **실제 설치·실행** — 두 Qwen 모델 GPU 추론 | [BSD-3-Clause](https://raw.githubusercontent.com/pytorch/pytorch/main/LICENSE), 포함 third-party notices 별도. NVIDIA 라이브러리를 모두 BSD로 표시하면 안 됨 |
| 오픈소스 | Transformers 4.57.6 | **실제 설치·실행** — Qwen tokenizer·생성 모델 로딩 | [Apache-2.0](https://raw.githubusercontent.com/huggingface/transformers/main/LICENSE) |
| 오픈소스 | Sentence Transformers 5.7.0 | **실제 설치·실행** — Qwen 임베딩 로딩·encode | [Apache-2.0](https://raw.githubusercontent.com/huggingface/sentence-transformers/master/LICENSE) |
| 오픈소스 | Accelerate 1.15.0 | **gpu extra 선언·lock** — Transformers 실행 지원 패키지. 직접 import는 없음 | [Apache-2.0](https://raw.githubusercontent.com/huggingface/accelerate/main/LICENSE) |
| 오픈소스 | XGBoost 3.4.1 | **실제 학습·별도 환경** — 산불 관측 예측 CPU/GPU 학습·추론 | [Apache-2.0](https://raw.githubusercontent.com/dmlc/xgboost/master/LICENSE) |
| 오픈소스 | scikit-learn 1.9.1 | **직접 선언·lock** — 분류 평가·보정 실험 | [BSD-3-Clause](https://raw.githubusercontent.com/scikit-learn/scikit-learn/main/COPYING) |
| 오픈소스 | NumPy 2.5.4 | **직접 선언·lock** — 배열·통계 계산 | [BSD-3-Clause](https://raw.githubusercontent.com/numpy/numpy/main/LICENSE.txt); wheel 포함 수치 라이브러리 고지는 별도 |
| 오픈소스 | pandas 2.3.3 | **직접 선언·lock** — 표형 데이터 처리 | [BSD-3-Clause](https://raw.githubusercontent.com/pandas-dev/pandas/main/LICENSE) |
| 오픈소스 | PyArrow 26.0.0 | **직접 선언·lock** — Arrow/Parquet 저장·읽기 | [Apache-2.0 및 bundled notices](https://raw.githubusercontent.com/apache/arrow/main/LICENSE.txt) |
| 오픈소스 | pytest 9.2.0 | **실제 실행·설치** — 단위·통합 테스트 | [MIT](https://raw.githubusercontent.com/pytest-dev/pytest/main/LICENSE) |
| 오픈소스 | Ruff 0.17.3 | **실제 실행·설치** — lint·format | [MIT 및 파생 코드 notices](https://raw.githubusercontent.com/astral-sh/ruff/main/LICENSE) |
| 오픈소스 | PyYAML 6.0.2 | **실제 실행·설치** — YAML 설정·OpenAPI 검증 | [MIT](https://raw.githubusercontent.com/yaml/pyyaml/main/LICENSE) |
| 오픈소스 | openapi-spec-validator 0.7.2 | **실제 실행·설치** — API 계약 검사 | [Apache-2.0](https://raw.githubusercontent.com/python-openapi/openapi-spec-validator/master/LICENSE) |
| 오픈소스 | jsonschema 4.23.0 | **실제 실행·설치** — JSON Schema·예제 검증 | [MIT](https://raw.githubusercontent.com/python-jsonschema/jsonschema/main/COPYING) |
| 오픈소스 | Hatchling `>=1.27,<2` | **pyproject 선언** — Python wheel 빌드 backend | [MIT](https://raw.githubusercontent.com/pypa/hatch/master/LICENSE.txt). 빌드 당시 정확 버전은 확인되지 않음 |
| 오픈소스 | uv 0.11.10 | **실제 사용** — lock·sync·Python 실행, Docker 빌드 및 CI | [MIT](https://github.com/astral-sh/uv/blob/main/LICENSE-MIT) OR [Apache-2.0](https://github.com/astral-sh/uv/blob/main/LICENSE-APACHE) |

주요 전이 의존성도 빠뜨리기 쉬움: 설치 metadata로 `pydantic 2.14.2 MIT`, `starlette 1.10.0 BSD-3-Clause`, `cryptography 50.0.2 Apache-2.0 OR BSD-3-Clause`, `redis-py 6.4.0 MIT`, `psycopg-binary 3.3.6 LGPL-3.0-only` 확인. **Redis Python 클라이언트 MIT와 Redis 서버 7.4의 라이선스를 혼동하지 말 것.** 두 잠금 파일의 전체 전이 항목은 아래 Python 의존성 전수 부록에 개별 수록했다.

## 4. 인프라·공급 경로·운영 도구

| 구분 | 명칭 | 용도 | 라이선스 |
| --- | --- | --- | --- |
| 오픈소스 | PostgreSQL 16 (`pgvector/pgvector:pg16`) | **실제 MVP 배포** — 이벤트·정책·프로필·문서·outbox 저장 | [PostgreSQL License](https://www.postgresql.org/about/licence/). 태그만으로 정확 patch/digest를 확정하지 않음 |
| 오픈소스 | pgvector DB extension (`pgvector/pgvector:pg16`) | **실제 MVP 배포** — 1024차원 임베딩 저장·cosine 검색 | [PostgreSQL License](https://github.com/pgvector/pgvector/blob/master/LICENSE). Python 패키지 MIT와 다름; 확장 정확 버전 미확인 |
| 오픈소스 | PostGIS `postgis/postgis:16-3.5` | **구성만** — 일반 서버 초기 scaffold 공간 DB 구성 | [GNU GPL v2 계열](https://github.com/postgis/postgis/blob/master/COPYING). 실제 MVP compose는 pgvector 이미지이므로 PostGIS 실제 활성화로 적지 않음 |
| 기타 | Redis `7.4-bookworm` | **실제 MVP 배포** — Celery broker, AOF 저장 | **[RSALv2 OR SSPLv1](https://redis.io/legal/licenses/)**. 7.2 이하 BSD와 다름. Redis 8+의 AGPL 선택지가 7.4에 적용되는 것은 아님 |
| 오픈소스 | CPython 3.12 (GPU 3.12.3, 로컬 3.12.13), `python:3.12-slim-bookworm` | **실제 실행** — API·워커·학습 실행 | [PSF License 및 포함 구성요소 고지](https://docs.python.org/3.12/license.html) |
| 기타 | Debian Bookworm | **실제 빌드** — Python/Redis 컨테이너 기반 | [개별 패키지 라이선스](https://www.debian.org/legal/licenses/); OS 전체가 단일 MIT/Apache 라이선스인 것이 아님 |
| 기타 | Ubuntu 24.04.1 LTS(두 서버), Ubuntu 22.04.5 LTS(K8s) | **기존 확인** — 모델·MVP·기존 클러스터 호스트 | 개별 패키지 라이선스 및 [Canonical IP 정책](https://canonical.com/legal/intellectual-property-policy) |
| 오픈소스 | Docker Engine/Moby, Docker Compose | **실제 서버 배포** — 일반 서버 서비스·DB·워커 배포 | [Moby Apache-2.0](https://github.com/moby/moby/blob/master/LICENSE), [Compose Apache-2.0](https://github.com/docker/compose/blob/main/LICENSE). GPU/일반 서버별 정확 설치 버전·이미지 내부 패키지는 이 명세에서 모두 확정하지 않음. Docker Desktop 구독 조건과 별개 |
| 기타 | NVIDIA L4 / driver 580.159.04 / PyTorch CUDA runtime 12.8 | **실제 사용** — Qwen 추론·XGBoost CUDA 연구 | [NVIDIA CUDA EULA·제품별 부속 조건](https://docs.nvidia.com/cuda/eula/index.html). GPU 하드웨어 자체를 OSS 라이선스로 표기하지 않음. cuBLAS/cuDNN 등 동봉 라이브러리는 각 패키지 고지 필요 |
| 기타 | Tailscale 1.104.4 | **실제 사용** — 두 서버 Tailnet 접근 | CLI/daemon [BSD-3-Clause](https://github.com/tailscale/tailscale/blob/main/LICENSE), 관리 서비스는 [Tailscale 약관](https://tailscale.com/terms). Operator는 설치돼 있지 않음 |
| 오픈소스 | OpenSSH | **실제 사용** — 서버 로그인·GPU localhost API 터널 | [BSD 계열 및 각 구성요소 허용 라이선스](https://raw.githubusercontent.com/openssh/openssh-portable/master/LICENCE), 정확 package 버전 미확인 |
| 오픈소스 | systemd 사용자 서비스 | **실제 사용** — GPU·일반 서버·학습 작업 지속 실행 | 주로 [LGPL-2.1-or-later 및 개별 파일 라이선스](https://github.com/systemd/systemd/blob/main/LICENSE.LGPL2.1). 정확 버전 미확인 |
| 오픈소스 | Kubernetes v1.30.14 | **기존 보존, MVP 수집 미사용** — 기존 6노드 플랫폼. 프로젝트 수집기는 실행하지 않음 | [Apache-2.0](https://github.com/kubernetes/kubernetes/blob/master/LICENSE) |
| 오픈소스 | containerd 2.2.1 | **기존 보존** — 기존 K8s 컨테이너 실행 | [Apache-2.0](https://github.com/containerd/containerd/blob/main/LICENSE) |
| 오픈소스 | Argo CD, Harbor, ingress-nginx, MetalLB | **기존 보존** — 기존 배포·registry·ingress·LB. 봉화지기 MVP에서의 직접 사용은 확인되지 않음 | 각각 [Argo CD Apache-2.0](https://raw.githubusercontent.com/argoproj/argo-cd/master/LICENSE), [Harbor Apache-2.0](https://raw.githubusercontent.com/goharbor/harbor/main/LICENSE), [ingress-nginx Apache-2.0](https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/LICENSE), [MetalLB Apache-2.0](https://raw.githubusercontent.com/metallb/metallb/main/LICENSE). 기존 설치 버전 미확인 |
| 오픈소스 | Prometheus / Grafana | **기존 보존** — 기존 플랫폼 지표·대시보드. 이번 MVP 계측 연결은 미확인 | [Prometheus Apache-2.0](https://raw.githubusercontent.com/prometheus/prometheus/main/LICENSE). Grafana 최신 OSS [AGPL-3.0](https://github.com/grafana/grafana/blob/main/LICENSE); 기존 설치 버전·edition을 모른 채 전체 설치의 라이선스를 확정하지 않음 |
| 오픈소스 | metrics-server, NFS provisioner, local-path StorageClass | **기존 보존** — 기존 노드 지표·NFS/local storage provisioning | 정확 배포 구현체·버전 미확인. `nfs-storage`/`nfs-bulk`라는 StorageClass 이름은 특정 라이선스 증명이 아님 |
| 기타 | NAVER Cloud 제공 GPU·일반 서버 | **제공 서버 사용** — 사용자 제공 인프라 | [Ncloud 서비스 약관](https://www.ncloud.com/policy/terms/svc) 및 제공 계정/행사 계약. 이번에 새 결제·서버 생성한 것은 아님 |
| 기타 | PyPI, PyTorch CUDA wheel index, Docker Hub, GHCR | **실제 다운로드 경로** — Python 패키지·컨테이너 공급 | [PyPI 약관](https://policies.python.org/pypi.org/Terms-of-Service/), [Docker 약관](https://www.docker.com/legal/docker-terms-use/), [GitHub Packages 조건](https://docs.github.com/en/site-policy/github-terms/github-terms-for-additional-products-and-features)과 각 artifact의 upstream 라이선스가 별개. `uv.lock` SHA와 Docker 이미지 실제 digest 필요; registry 공개 제공이 내용물의 일괄 자유 이용 허가가 아님 |
| 기타 | Git, GitHub | **실제 사용** — 코드 이력·원격 저장소 | [Git GPL-2.0 계열](https://github.com/git/git/blob/master/COPYING); GitHub는 [서비스 약관](https://docs.github.com/en/site-policy/github-terms/github-terms-of-service). 저장소 자체 LICENSE 파일은 이번 검색에서 확인되지 않음 |
| 기타 | GitHub Actions, `actions/checkout@v4`, `astral-sh/setup-uv@v6` | **구성만 확인** — 테스트·lint·migration·compose 검증 workflow | GitHub 서비스 약관 + [checkout MIT](https://raw.githubusercontent.com/actions/checkout/main/LICENSE), [setup-uv MIT](https://raw.githubusercontent.com/astral-sh/setup-uv/main/LICENSE). workflow 파일이 있다고 실제 원격 CI 성공을 의미하지 않음 |

## 5. 학습·연구에 확보한 데이터와 출처

| 구분 | 명칭 | 용도 | 라이선스 |
|---|---|---|---|
| 기타 | XGBoost 산불 관측 예측 가중치 | **자체 학습 모델 · 연구** — NDWS 다음 날 관측, 미국 GOES 및 국내 GK2A의 1·3·6시간 화재 관측 연구 | 별도 외부 사전학습 모델이 아닌 프로젝트 산출물. 현재 자체 가중치의 독립적인 공개 배포 라이선스는 확인하지 못함. **XGBoost 라이브러리 라이선스와 학습 데이터 이용조건은 별개**. 아래 데이터 조건을 일괄 Apache-2.0으로 바꾸어 표기하지 않음. |
| 기타 | [Next Day Wildfire Spread v2](https://www.kaggle.com/datasets/fantineh/next-day-wildfire-spread) | **학습 데이터 · 사용** — 미국 과거 위성 관측 기반 초기 일별 학습. 공식 train/eval/test 첫 shard 다운로드 | **CC BY 4.0**. 실제 다운로드 manifest에 저장된 제공자 라이선스. 저자·원문·라이선스 출처와 가공 사실 표시, 상업 이용·수정·재배포 가능. [CC BY 4.0 조건](https://creativecommons.org/licenses/by/4.0/). Google Research의 코드 라이선스와 데이터 라이선스는 구별. |
| 기타 | [NOAA GOES-17/18 ABI-L2-FDCC](https://registry.opendata.aws/noaa-goes/) | **위성 데이터 · 학습 사용** — 미국 산불 6개 사건의 5분 화재 관측을 시간별 연구 학습·검증·보정·시험으로 구성 | **NOAA NODD 공개 데이터 이용조건**. 계정 없이 공개 S3 접근·사용·배포 가능. NOAA 출처표시 요청, NOAA 보증·제휴 암시 금지, 가공 자료를 무가공 NOAA 원본으로 표시하지 않음. |
| 기타 | [NOAA ISD / ISD Lite](https://registry.opendata.aws/noaa-isd/) | **기상 데이터 · 학습 사용** — 한국 인근 관측소 과거 시간별 온도·이슬점·바람·강수 등 환경 특성 | **NOAA NODD 공개 데이터 이용조건**. 공개 S3, 별도 키 없음. 출처표시 요청, 기관 보증 암시 금지, 가공 여부 구분. ISD Lite의 제품 설명은 [NCEI 공식 문서](https://www.ncei.noaa.gov/products/land-based-station/integrated-surface-database) 참조. |
| 외부 API | [기상청 API Hub GK2A L2 FF / KO](https://apihub.kma.go.kr/apiList.do?seqApi=6&seqApiSub=271) | **국내 위성 API·데이터 · 학습 사용** — 국내 10분 산불탐지 관측으로 입력 이력과 1·3·6시간 관측 정답 구성 | **공공누리 유형별 조건 + 승인 계정 접근**. [API 이용안내](https://apihub.kma.go.kr/apiInfo.do)는 인증키와 유형별 조건을 명시. 실제 파일에는 `Access is restricted to approved users only`가 기록됨. 이것만으로 저작물의 KOGL 유형·상업 이용·원본 재배포권을 확정할 수 없어 **정확 유형 확인 필요**로 표기. |
| 기타 | [GK2A KO020LC 위경도 NetCDF](https://nmsc.kma.go.kr/upload/resource/data/gk2a/gk2a_ami_ko020lc_latlon.nc) | **국내 좌표 자료 · 검증 사용** — 공식 900×900 격자와 구현 좌표 변환 비교 | 공개 다운로드 가능. **해당 파일의 개별 라이선스 미확인**. [NMSC 저작권 정책](https://api.nmsc.kma.go.kr/homepage/html/base/cmm/selectPage.do?page=static.etc.copyrightProtectionPolicy)은 KOGL 표시 확인과 출처표시, 미표시 자료의 별도 협의를 요구. 공개 URL을 Public Domain으로 간주하지 않음. |
| 외부 API | [Microsoft Planetary Computer STAC / SAS](https://planetarycomputer.microsoft.com/docs/) | **데이터 검색·다운로드 API · 사용** — MODIS·토지피복·DEM 검색과 COG 읽기 | STAC 익명 접근, 일부 자산은 공개 발급 SAS 토큰 필요. [SAS 안내](https://planetarycomputer.microsoft.com/docs/concepts/sas/). **API 접근 가능성과 데이터 라이선스는 별개**이며 세 데이터 컬렉션의 STAC `license`는 모두 `other`; 원 공급자 조건 적용. |
| 기타 | [MODIS/Terra MOD14A1.061 및 Aqua MYD14A1.061](https://planetarycomputer.microsoft.com/dataset/modis-14A1-061) | **위성 데이터 · 확보·일별 감사** — 한국 일별 화재·QA·FRP 자료 확보 및 일별 데이터셋 감사. 현재 GK2A 시간별 정답과 구별 | NASA/LP DAAC 공개 데이터. [LP DAAC 이용조건 FAQ](https://forum.earthdata.nasa.gov/viewtopic.php?t=6891)는 이용·판매·재배포 제한 없음과 제품 DOI 인용을 안내. [NASA MODIS/VIIRS 공개 정책](https://ladsweb.modaps.eosdis.nasa.gov/learn/)도 공개 이용·재배포와 출처 인용을 안내. 정확 인용: [MOD14A1.061 DOI](https://doi.org/10.5067/MODIS/MOD14A1.061), [MYD14A1.061 DOI](https://doi.org/10.5067/MODIS/MYD14A1.061). PC 자체 STAC에는 `other`로 기록되므로 CC BY로 임의 표기하지 않음. |
| 기타 | [NASA FIRMS 국가별 연간 VIIRS 자료](https://firms.modaps.eosdis.nasa.gov/data/country/yearly_summary_files.txt) | **화재 관측점 · 확보·보조 감사** — 2018–2024 한국 연간 관측 CSV 확보·교차 확인. 화선·연속 음성 정답 아님 | NASA 공개 관측 데이터, 출처·제품 인용 요청. [FIRMS 공식 안내](https://www.earthdata.nasa.gov/data/tools/firms), [NASA 데이터 정책](https://ladsweb.modaps.eosdis.nasa.gov/learn/). 실제 다운로드는 키 없는 연간 파일 경로. **MAP_KEY 기반 area/history API를 사용한 것으로 표시하지 않음**. |
| 기타 | [ESA CCI Land Cover 2015 v2.0.7cds](https://planetarycomputer.microsoft.com/dataset/esa-cci-lc) | **토지피복 · 학습 사용** — 한국 토지피복·산림 특성, 과거 기준 정적 입력 | **ESA CCI 전용 조건 / 정확 판본 적용 조건 추가 확인**. PC STAC는 `other`; [원본 CDS 카탈로그](https://cds.climate.copernicus.eu/datasets/satellite-land-cover?tab=overview)는 ESA CCI·CC-BY·VITO 라이선스를 함께 표시. [ESA CCI 조건](https://cds.climate.copernicus.eu/licences/satellite-land-cover)은 교육·과학 목적 무료와 출처표시, 과학 출판물 전달, 광고·상업 홍보물 사전 검토를 명시. 이 구버전 자산을 모든 용도에서 CC BY로 단정하지 않음. |
| 기타 | [Copernicus DEM GLO-90](https://planetarycomputer.microsoft.com/dataset/cop-dem-glo-90) | **지형 · 학습 사용** — 한국 44개 DEM 타일에서 고도·경사 입력 생성 | **COP-DEM-GLO-90-F 전용 무료·공개 라이선스**. 복제·배포·공개·수정·결합 허용. 원본/가공본 각각의 정해진 출처 고지, 면책 문구, 후속 수령자에게 의무 전달, 기관 보증 암시 금지. [공식 라이선스 PDF의 GLO-90 부분, 19–21쪽](https://dataspace.copernicus.eu/sites/default/files/media/files/2025-06/copernicus_contributing_mission_data_access_v2_cop_dem_licenses.pdf). 같은 PDF 앞부분의 다른 제품 조건과 혼동하지 않음. |
| 기타 | [geoBoundaries gbOpen KOR ADM0](https://www.geoboundaries.org/api/current/gbOpen/KOR/ADM0/) / Natural Earth | **국경 경계 · 사용** — 한국 영역 마스크·데이터 절단 | 해당 KOR 메타데이터의 원천 라이선스는 **Public Domain**, 원천 Natural Earth. [Natural Earth 조건](https://www.naturalearthdata.com/about/terms-of-use/)은 자유 수정·배포·상업 이용 허용, 의무 출처표시 없음. 별도로 [geoBoundaries 데이터베이스](https://www.geoboundaries.org/index.html)는 **CC BY 4.0**·출처 인용 안내가 있으므로 Natural Earth와 geoBoundaries 양쪽을 표시. |
| 기타 | [CAL FIRE 산불 사건 페이지](https://www.fire.ca.gov/incidents/2021/7/13/dixie-fire) | **사건 메타데이터 · 참조** — Dixie·Caldor·Mosquito·Oak·Smith River의 날짜·위치 확인, 연구 수집 창 선정 | [CAL FIRE 이용조건](https://www.fire.ca.gov/conditions-of-use)은 별도 표시 없는 웹 정보를 일반적으로 Public Domain으로 안내. 제3자 사진·저작물은 별도 조건. 여기서는 사건 사실·출처 링크만 이용하며 사이트 이미지나 보고서 전부의 재배포 허락으로 확대하지 않음. |
| 기타 | [Alaska IMT / BLM Bootleg 2021 사건 요약](https://fire.ak.blm.gov/content/aicc/team_left/03.%20Alaska%20CIMT%20Incident%20Archive/Alaska%20IMT%20Incident%20Summaries/2021%20Summaries/2021%2007-23%20to%2008-06%20Bootleg.pdf) | **사건 메타데이터 · 참조** — Bootleg 날짜·지역 확인. 실제 격자 학습 정답은 GOES에서 생성 | [BLM 권리 정책](https://www.blm.gov/info/notices/drctp-policy)은 대부분 자료가 Public Domain이며 제3자 제한 자료는 별도 표시한다고 설명. 사건 사실·문서 출처 참조만 확인. 문서 내 모든 사진의 별도 권리까지 확인한 것은 아님. |

## 6. 조사했지만 현재 학습·운영에 채택하지 않은 자료

| 구분 | 명칭 | 용도 | 라이선스 |
|---|---|---|---|
| 기타 | [NOAA JPSS VIIRS EFIRE](https://registry.opendata.aws/noaa-jpss/) | **샘플 조사 · 미학습** — 키 없는 극궤도 화재 관측 대안 조사, 실제 EFIRE 샘플 확보 | NOAA NODD 공개 이용조건. 전체 geolocation·유효 관측 마스크와 시계열이 마련되지 않아 현 학습 입력·정답에 미사용. |
| 기타 | [NOAA 공개 GK2A L1B](https://registry.opendata.aws/noaa-gk2a-pds/) | **목록 조사 · 미학습** — 인증 없이 접근 가능한 GK2A 공개 버킷 목록 확인 | 해당 NOAA 제공 경로는 NODD 공개 이용조건. **인증 KMA FF 제품과 다른 경로·산출물**. L1B 목록 조회만으로 FF 정답 확보로 표기하지 않음. |
| 기타 | [JAXA P-Tree](https://www.eorc.jaxa.jp/ptree/registration_top.html) | **등록 조건 조사 · 미사용** — Himawari 자료 대안 조사 | 별도 등록·자료 이용조건. 실제 수집·학습에 채택하지 않음. 구체 원본 재배포 조건은 미감사. |
| 기타 | D01 [행정안전부 재난문자](https://www.safetydata.go.kr/disaster-data/view?dataSn=228) | **초기 카탈로그 · 학습 미사용** — 공식 경보 원문·발령 시각·대상 설계 참조 | 서비스 승인 키 필요. 이번 학습 업무에서 원본 미취득. 제품별 이용허락 유형은 현 페이지 파싱으로 확인하지 못했으므로 **미확인**. 현재 MVP는 시나리오를 이벤트 수신 API로 재생하며 이 정부 API의 자동 수집은 실행하지 않음. |
| 외부 API | D02 [산림청 산불 관련 API 3070842](https://www.data.go.kr/data/3070842/openapi.do) | **초기 카탈로그 · 미사용** — 국내 사건 대조·등록 정보 조사 | 실제 응답 미검증·serviceKey 필요. 이번 공식 페이지 접근이 실패하여 **이용허락 범위 재확인 필요**. 무조건 공공누리 1유형 또는 제한 없음으로 표기하지 않음. |
| 기타 | D03 [산림청 산불 이력 파일 15121380](https://www.data.go.kr/data/15121380/fileData.do) | **초기 카탈로그 · 미사용** — 발생·진화 시각·면적 후보 조사 | CSV 미다운로드. 이번 공식 페이지 접근 실패로 **제품별 이용허락 미확인**. |
| 외부 API | D04–D05 [기상청 ASOS 시간자료 15057210](https://www.data.go.kr/data/15057210/openapi.do), [별도 API Hub 지상관측](https://apihub.kma.go.kr/apiList.do?seqApi=2&seqApiSub=239) | **초기 카탈로그 · 미사용** — 국내 바람·온습도·강수 후보 조사 | 현재 연구에서 실제 사용한 기상은 NOAA ISD. 국내 API 과거 시계열 미취득. data.go.kr은 제품별 허락 재확인, API Hub는 공공누리 유형별 조건·승인 키. **15057210을 AWS API로 부르지 않음**. |
| 기타 | N01 GK2A FF | **초기 조사 후 채택** — 초기 source-audit에는 카탈로그 조사만 기록 | 현재는 위 ‘국내 위성 API·데이터’의 실제 사용 행이 정본. 초기 조사 상태를 현재 사용 상태로 복사하지 않음. |

국내 사건의 날짜·수집 영역을 정하는 데 사용한 산림청(`forest.go.kr`, `fmc.forest.go.kr`), 국무조정실(`opm.go.kr`), 행정안전부(`mois.go.kr`), 정책브리핑(`korea.kr`), 합천군의회(`hccl.go.kr`)의 게시물·보고서도 외부 참고자료다. 각 사건의 실제 원문 주소는 [출처 목록 JSON](external-resources/data-and-content-sources.json)과 [국내 수집 설정](../../../training/configs/korea-gk2a-hourly-v4.json)에 보존한다. 이 자료는 사건 창 선정 근거이며 위성 격자 정답·개인 피해 정답으로 사용하지 않았다. 개별 게시물의 공공누리 표시·첨부물 권리까지 모두 확인한 것은 아니므로 일괄 제1유형으로 표시하지 않는다.

| 구분 | 명칭 | 용도 | 라이선스 |
| --- | --- | --- | --- |
| 기타 | 국내 산불 공식 사건 게시물·보고서 | **참조:** 산림청·산불상황관제시스템·국무조정실·행안부·정책브리핑·합천군의회 자료로 사건 날짜와 영역 설정 | 게시물별 공공누리 표시와 첨부물 권리 적용. 이 목록의 정확한 개별 유형은 미확인; 사실·출처 링크를 참고한 것으로 기록 |
| 기타 | GK2A FF 알고리즘·지도 투영 설명 | **참조:** [국가기상위성센터 FF ATBD](https://api.nmsc.kma.go.kr/resources/common/pdf/%EC%99%B8GK2A_L2_ATBD_%EA%B5%AD%EB%AC%B8_%EC%82%B0%EB%B6%88%ED%83%90%EC%A7%80_FF.pdf)·[map_info.pdf](https://apihub.kma.go.kr/getAttachFile.do?fileName=map_info.pdf)를 통한 산불탐지 변수 및 좌표 해석 | 문서별 저작권 및 NMSC 정책 적용. 원문 전체의 재배포 허락을 별도로 확인하지 않음 |

실제 사용 근거: [초기 데이터 manifest](../../../training/reports/source-manifest.json), [국외·국내 공개자료 수집 inventory](../../../training/reports/improvement-audit-20261031/inventory.json), [KMA 원본 inventory](../../../training/reports/kma-audit-20261031/inventory.json), [KMA 실시간 원본 메타데이터](../../../training/reports/kma-audit-20261031/live-metadata/probe-20261031T1340.json), [공식 격자 대조](../../../training/reports/kma-audit-20261031/projection-audit.json). `training/sources/source-audit.json`의 초기 조사 상태보다 이 후속 기록을 우선한다. 원자료와 모델 파일은 GPU 프로젝트의 `data/raw/`, `data/processed/`, `data/artifacts/`에 있으며 저장소에는 안전한 보고서만 포함한다.

## 7. API 접근 경로·인증·자료형식

아래는 2026-10-31 기준 코드·수집 기록의 경로이다. URL에는 인증 값을 포함하지 않았다. ‘수치 쿼터 미확인’은 무제한이라는 뜻이 아니다. 웹 API 서비스 쿼터와 우리 수집기의 동시 다운로드 수는 다르다.

| 명칭·상태 | 실제 엔드포인트 / 요청 기준 | 응답 형식 | 인증·쿼터 확인 |
|---|---|---|---|
| KMA FF · 사용 | `GET https://apihub.kma.go.kr/api/typ05/api/GK2A/LE2/FF/KO/data`; `date`는 `YYYYMMDDHHMM`, 구현은 UTC로 변환하고 10분 간격 요청 | NetCDF, 900×900 `FF`·`DQF_FF`·투영 메타데이터 | 발급 `authKey` 필요. [공식 안내](https://apihub.kma.go.kr/apiInfo.do): 일반회원 하루 20,000건·5GB, 기관회원 30,000건·50GB, 상황에 따라 변경 가능. **현재 사용자 계정의 실효 할당량은 미조회**. 같은 사이트의 일부 텍스트·영상 API는 KST를 사용하므로 시간 인자를 섞지 않음. |
| KMA 공식 좌표 · 사용 | `GET https://nmsc.kma.go.kr/upload/resource/data/gk2a/gk2a_ami_ko020lc_latlon.nc`; 날짜 인자 없음 | NetCDF 위경도 배열 | 공개 URL, 수집 기록상 키 없음. 수치 쿼터 미확인. |
| NDWS · 사용 | `GET https://www.kaggle.com/api/v1/datasets/view/fantineh/next-day-wildfire-spread`, `/list/fantineh/next-day-wildfire-spread`, `/download/fantineh/next-day-wildfire-spread/{파일명}`; 다운로드에 `datasetVersionNumber=2` 적용 | 메타데이터·목록 JSON, 파일별 ZIP 내부 TFRecord | 수집 구현·기록상 무계정·무키 공개 다운로드. 수치 쿼터 미확인. 날짜별 API가 아니라 고정 데이터셋 파일 다운로드. |
| NOAA GOES · 사용 | `GET https://noaa-goes17.s3.amazonaws.com/`, `https://noaa-goes18.s3.amazonaws.com/`; 목록 `list-type=2`, `prefix=ABI-L2-FDCC/YYYY/DDD/HH/` (`DDD`는 UTC 연중 일수), 각 객체 key로 다운로드 | S3 목록 XML / NetCDF4 객체 | 공개 익명 S3, AWS 계정 없음. 수치 쿼터 미확인. 코드의 병렬 1–8개는 자체 상한. [공식 버킷·접근 안내](https://registry.opendata.aws/noaa-goes/) |
| NOAA ISD Lite · 사용 | `GET https://noaa-isd-pds.s3.amazonaws.com/isd-history.csv`, `/isd-lite/isd-lite-format.txt`, `/isd-lite/data/{YYYY}/{관측소}-{YYYY}.gz` | 관측소 CSV, 포맷 TXT, gzip 고정폭 시간별 관측 | 공개 익명 S3, 키 없음. 관측행의 연·월·일·시를 사용. 수치 쿼터 미확인. [공식 ISD 제공 경로](https://registry.opendata.aws/noaa-isd/) |
| Planetary Computer STAC · 사용 | `GET https://planetarycomputer.microsoft.com/api/stac/v1/search`; `collections`, `bbox`, `datetime`(ISO 8601 시작/종료), `limit`; 후속 페이지 link 추적 | STAC GeoJSON / 자산 메타데이터 | 공개 익명 검색. 공개 접근에도 throttling 있음, 이번 수치 쿼터 미확인. [공식 안내](https://planetarycomputer.microsoft.com/docs/) |
| Planetary Computer SAS·자산 · 사용 | `GET https://planetarycomputer.microsoft.com/api/sas/v1/token/{collection_id}` 또는 `/token/{storage_account}/{container}`; SDK가 STAC 자산 URL에 토큰 적용 | 토큰 JSON, MODIS·ESA CCI·CopDEM COG GeoTIFF | 토큰 발급은 계정 없이 가능. 실제 인증 토큰·서명 URL은 문서에 보관하지 않음. 만료·속도 제한이 있고 계정·접근 지역별로 달라짐. [공식 SAS 설명](https://planetarycomputer.microsoft.com/docs/concepts/sas/) |
| FIRMS 연간 CSV · 사용 | `GET https://firms.modaps.eosdis.nasa.gov/data/country/yearly_summary_files.txt`, `https://firms.modaps.eosdis.nasa.gov/data/country/AttributesReadme.txt`, `/data/country/{sensor}/{YYYY}/{sensor}_{YYYY}_Republic_of_Korea.csv`; 실제 sensor는 `viirs-snpp`, `viirs-jpss1` | 공개 연간 CSV와 속성 TXT | 키·계정 없는 실제 수집 경로. 파일 다운로드 수치 쿼터 미확인. 연도별 파일이며 아래 MAP_KEY API 한도를 이 경로에 적용했다고 단정하지 않음. |
| geoBoundaries · 사용 | 메타데이터 `GET https://www.geoboundaries.org/api/current/gbOpen/KOR/ADM0/`; 실제 경계 `GET https://github.com/wmgeolab/geoBoundaries/raw/9469f09/releaseData/gbOpen/KOR/ADM0/geoBoundaries-KOR-ADM0.geojson` | JSON / GeoJSON | 공개 무계정·무키 경로. 파일 revision 고정, 날짜 인자 없음. 수치 쿼터 미확인. |
| Qwen 모델 파일 · 사용 | Hugging Face의 `Qwen/Qwen3-4B-Instruct-2507`, `Qwen/Qwen3-Embedding-0.6B` 저장소, 위 표의 revision 고정 | Safetensors·토크나이저·설정 JSON 등 모델 저장소 파일 | 공개 모델 저장소. 다운로드 후 로컬 캐시로 추론하므로 **HF 호스팅 추론 API 사용이 아님**. [Hub 공식 제한](https://huggingface.co/docs/hub/main/rate-limits)은 5분 창 기준 익명 IP API 500 / resolver 3,000 / page 100회, 무료·익명 한도는 변동 가능. 실제 계정 인증 상태·잔여량 미조회. |
| JPSS · 샘플만 | `GET https://noaa-nesdis-n20-pds.s3.amazonaws.com/`, `https://noaa-nesdis-n21-pds.s3.amazonaws.com/`, `https://noaa-nesdis-snpp-pds.s3.amazonaws.com/`; `VIIRS_EFIRE_VIIRSI_EDR/` 날짜 prefix 탐색 | S3 XML / EFIRE 샘플 NetCDF | 공개 익명 S3. 수치 쿼터 미확인. [JPSS 제공 경로](https://registry.opendata.aws/noaa-jpss/). |
| 공개 GK2A · 목록만 | [공식 Registry](https://registry.opendata.aws/noaa-gk2a-pds/)가 안내하는 공개 S3 목록 | 객체 목록 XML, L1B 파일 메타데이터 | 공개 무계정 경로. 실제 FF 학습 입력은 인증 KMA 경로임. 원본 수집·학습 사용 없음, 수치 쿼터 미확인. |
| FIRMS area/history · 조사만 | `https://firms.modaps.eosdis.nasa.gov/api/area/csv/` 아래 MAP_KEY·자료원·영역·기간 인자로 구성하는 별도 API | CSV | 무료 MAP_KEY 필요. [공식 API 안내](https://firms.modaps.eosdis.nasa.gov/content/academy/data_api/firms_api_use.html): 10분당 5,000 transaction, 큰 요청은 여러 transaction. 현재 업무에서 이 인증 API는 미사용. |
| D01 재난문자 · 학습 미사용 | `https://www.safetydata.go.kr/V2/api/DSSP-IF-00247` (초기 인수 명세) | 실제 응답 미검증 | 승인 serviceKey 필요. 현재 시간 인자·포맷·실효 쿼터는 학습 코드에서 미검증. 현재 MVP는 이벤트 수신·시나리오 재생이며 이 정부 API 자동 수집은 실행하지 않음. |
| D02·D03·D04–D05 · 카탈로그만 | 위 조사 표의 data.go.kr / API Hub **카탈로그 URL** | 원본 API 응답·CSV 미취득 | 실제 요청 endpoint·시간형식·쿼터를 검증하지 않았으므로 카탈로그 링크를 실제 호출한 API endpoint로 표시하지 않음. |
| Google News RSS · 사용 | `GET https://news.google.com/rss/search`; `q`, `hl=ko`, `gl=KR`, `ceid=KR:ko` | RSS XML 제목·설명·링크·매체·시각 | 키 없이 조회. 코드의 10초 timeout·512,000바이트 상한은 자체 설정이며 공급자 쿼터가 아님. 공식 상용 검색 API 계약·보장 쿼터 미확인. |
| FCM · 구성, 실발신 미사용 | `POST https://fcm.googleapis.com/v1/projects/{project}/messages:send` | JSON | 서비스 계정 OAuth access token 및 단말 registration token 필요. 실효 프로젝트 쿼터·결제 설정 미조회. [공식 API](https://firebase.google.com/docs/cloud-messaging/send/v1-api) |
| Google OAuth · 구성 | `POST https://oauth2.googleapis.com/token`; JWT bearer grant, `firebase.messaging` scope | access token JSON | FCM 인증에 쓰는 서비스 계정 서명. 봉화지기 앱 사용자의 로그인 API가 아님. 실제 자격 파일 값은 기록하지 않음. |
| 자체 GPU API · 사용 | `POST /internal/v1/embeddings`, `POST /internal/v1/generate`; `GET /health/ready` | 벡터/텍스트 JSON | 직접 만든 서버 API와 서비스 토큰 사용. 외부 유료 생성 API가 아니라 설치한 두 Qwen 모델을 호출. [서버 사용법](gpu-model-readiness.md), [클라이언트](../../../tools/gpu_client.py) |

엔드포인트 근거: `training/src/bonghwa_training/kma_download.py:18`, `:76`; `download.py:12`, `:30`, `:74`; `goes_download.py:20`; `korea_download.py:22`, `:70`, `:157`, `:207`. KMA의 한계 처리 코드는 429를 자료 누락으로 간주하지 않는다.

사용자가 처음 제시한 `GK2A/LE2/CI/ELA/data` 예시는 실제 FF 학습 경로가 아니다. 채택한 제품은 위의 `GK2A/LE2/FF/KO/data`이며, 접근이 거절됐던 다른 경로는 성공적으로 사용한 API로 기록하지 않는다.

## 8. 개발 보조 도구와 저장소 서비스

| 구분 | 명칭 | 용도 | 라이선스 |
| --- | --- | --- | --- |
| 기타 | OpenAI Codex / ChatGPT의 개발 보조 기능 | **사용:** 코드·문서 작성, 코드 검토, 테스트/명령 실행 보조, 공식 자료 조사. 봉화지기 서버가 호출하는 상용 LLM API와 구분 | 계정에 적용되는 OpenAI 서비스 이용조건. 제품 가중치의 오픈소스 라이선스로 기재하지 않음. 실제 계정 플랜·결제 방식·모델별 사용 이력은 이 감사에서 확정하지 않음. [OpenAI 서비스 이용조건](https://openai.com/policies/terms-of-use/). 개발 도구 이용을 봉화지기의 OpenAI API 호출로 계산하지 않음 |
| 기타 | Loom CLI 0.1.0 | **사용:** 작업 계약·실행 기록·체크포인트 관리. 개발용 도구이며 앱/서버에 재사용한 사전 코드라는 뜻이 아님 | 설치 메타데이터와 도구 프로젝트에서 라이선스 선언/별도 LICENSE를 확인하지 못함. 임의로 MIT나 Apache로 표기하지 않음. 근거: `loom --version`, 설치된 `loom-0.1.0` 메타데이터, 저장소 `AGENTS.md` |

## 9. Python 의존성 전수 부록

조사 기준은 `uv.lock` 139개 항목과 `training/uv.lock` 71개 항목이다. 두 파일의 중복을 합치면 외부 **174개 `(패키지, 버전)`**과 직접 개발 패키지 2개다. 외부 174개 중 154개는 아래 다섯 환경 중 하나 이상에 설치되어 있고, 20개는 잠금 파일에만 존재한다. 별도로 두 프로젝트가 선언한 빌드 의존성 `hatchling>=1.27,<2`를 기록한다. 설치 여부는 해당 시점 확인이며, 설치되어 있다는 사실이 요청 경로에서 모두 실행되었다는 뜻은 아니다.

환경: **LR**=로컬 `.venv`, **LT**=로컬 `training/.venv`, **GR**=GPU `.venv-gpu`, **GT**=GPU `training/.venv`, **GM**=GPU 초기 `.venv-ml`. **R**=루트 프로젝트, **T**=학습 프로젝트. `직접`은 기본 의존성, `선택/…`은 extra, `개발/…`은 dependency group, `간접`은 전이 의존성이다. `lock만`은 이 다섯 환경에서 설치가 확인되지 않은 플랫폼·선택 분기다. 동일 패키지의 다른 버전은 각각 기록했다.

라이선스 판정은 설치된 배포물의 `License-Expression`, `License` 필드와 classifier를 구분하여 기록했다. CUDA/NVIDIA 36개 패키지·버전은 같은 고정 버전의 공식 wheel LICENSE도 추가 확인하여 라이선스 칸에 반영했다. metadata와 동봉 LICENSE의 표기가 다르면 둘을 구분하고 동봉 조건을 따로 기재했다. 미설치 분기는 정확한 버전의 공식 PyPI 메타데이터를 조회했다. `BSD 계열`, `Apache 계열`, `Dual License`, `미표기`를 임의로 특정 SPDX로 바꾸지 않았다. NVIDIA 바이너리의 독점 라이선스는 같은 이름의 공개 소스 저장소 라이선스로 대체하지 않았다. CUDA용 torch wheel은 PyPI 배포물이 아니므로 공식 PyTorch 배포 인덱스로 연결한다.

각 배포물의 METADATA SHA-256, 동봉 LICENSE/COPYING/NOTICE 파일 경로·SHA-256·크기, 잠금 파일 artifact hash, 설치 환경과 원문 메타데이터 요약은 [의존성 근거 JSON](external-resources/python-inventory.json)에 보존했다. 장문 라이선스 전문은 복제하지 않았다.

| 구분 | 명칭 | 용도 | 라이선스 |
| --- | --- | --- | --- |
| 오픈소스 | [accelerate 1.15.0](https://pypi.org/project/accelerate/1.15.0/) | Qwen 모델 장치 배치·추론 지원; R:선택/gpu; 설치: GR | Apache (License 필드) |
| 오픈소스 | [affine 3.0.1](https://pypi.org/project/affine/3.0.1/) | 상위 패키지 실행·개발 의존성 지원; T:간접; 설치: LT, GT | BSD-3-Clause |
| 오픈소스 | [alembic 1.20.1](https://pypi.org/project/alembic/1.20.1/) | DB 스키마 마이그레이션; R:선택/server; 설치: LR | MIT |
| 오픈소스 | [amqp 5.4.1](https://pypi.org/project/amqp/5.4.1/) | 상위 패키지 실행·개발 의존성 지원; R:간접; 설치: LR | BSD (License 필드) |
| 오픈소스 | [annotated-doc 0.0.5](https://pypi.org/project/annotated-doc/0.0.5/) | 상위 패키지 실행·개발 의존성 지원; R:간접; 설치: LR, GR, GM | MIT |
| 오픈소스 | [annotated-types 0.8.0](https://pypi.org/project/annotated-types/0.8.0/) | 상위 패키지 실행·개발 의존성 지원; R:간접, T:간접; 설치: LR, LT, GR, GT, GM | MIT |
| 오픈소스 | [anyio 4.15.1](https://pypi.org/project/anyio/4.15.1/) | 상위 패키지 실행·개발 의존성 지원; R:간접; 설치: LR, GR, GM | MIT |
| 오픈소스 | [attrs 26.1.0](https://pypi.org/project/attrs/26.1.0/) | 상위 패키지 실행·개발 의존성 지원; R:간접, T:간접; 설치: LR, LT, GT | MIT |
| 오픈소스 | [billiard 4.3.1](https://pypi.org/project/billiard/4.3.1/) | 상위 패키지 실행·개발 의존성 지원; R:간접; 설치: LR | BSD (License 필드) |
| 오픈소스 | [celery 5.6.3](https://pypi.org/project/celery/5.6.3/) | 분석·개인 정책 비동기 작업 큐; R:선택/server; 설치: LR | BSD-3-Clause (License 필드) |
| 오픈소스 | [certifi 2026.10.23](https://pypi.org/project/certifi/2026.10.23/) | 상위 패키지 실행·개발 의존성 지원; R:간접, T:간접; 설치: LR, LT, GR, GT | MPL-2.0 (License 필드) |
| 오픈소스 | [cffi 2.1.1](https://pypi.org/project/cffi/2.1.1/) | 상위 패키지 실행·개발 의존성 지원; R:간접; 설치: LR | MIT-0 |
| 오픈소스 | [cftime 1.6.6.1](https://pypi.org/project/cftime/1.6.6.1/) | 상위 패키지 실행·개발 의존성 지원; T:간접; 설치: LT, GT | MIT |
| 오픈소스 | [charset-normalizer 3.5.2](https://pypi.org/project/charset-normalizer/3.5.2/) | 상위 패키지 실행·개발 의존성 지원; R:간접, T:간접; 설치: LR, LT, GR, GT | MIT (License 필드) |
| 오픈소스 | [click 8.5.0](https://pypi.org/project/click/8.5.0/) | 상위 패키지 실행·개발 의존성 지원; R:간접, T:간접; 설치: LR, LT, GR, GT, GM | BSD-3-Clause |
| 오픈소스 | [click-didyoumean 0.3.1](https://pypi.org/project/click-didyoumean/0.3.1/) | 상위 패키지 실행·개발 의존성 지원; R:간접; 설치: LR | MIT (License 필드) |
| 오픈소스 | [click-plugins 1.1.1.2](https://pypi.org/project/click-plugins/1.1.1.2/) | 상위 패키지 실행·개발 의존성 지원; R:간접; 설치: LR | New BSD (License 필드) |
| 오픈소스 | [click-repl 0.4.1](https://pypi.org/project/click-repl/0.4.1/) | 상위 패키지 실행·개발 의존성 지원; R:간접; 설치: LR | MIT (License 필드) |
| 오픈소스 | [cloudpickle 3.1.2](https://pypi.org/project/cloudpickle/3.1.2/) | 상위 패키지 실행·개발 의존성 지원; R:간접, T:간접; 설치: LT, GR, GT, GM | BSD-3-Clause (License 필드) |
| 오픈소스 | [colorama 0.4.6](https://pypi.org/project/colorama/0.4.6/) | 상위 패키지 실행·개발 의존성 지원; R:간접, T:간접; 설치: lock만 | BSD 계열 (세부 조항 수 미표기) (classifier만 있음) |
| 오픈소스 | [cryptography 50.0.2](https://pypi.org/project/cryptography/50.0.2/) | 상위 패키지 실행·개발 의존성 지원; R:간접; 설치: LR | Apache-2.0 OR BSD-3-Clause |
| 오픈소스 | [cuda-bindings 12.9.10](https://pypi.org/project/cuda-bindings/12.9.10/) | CUDA Python 바인딩; R:간접; 설치: GR | Apache-2.0; metadata 원문·동봉 고지 해시는 근거 JSON 참조 |
| 오픈소스 | [cuda-bindings 13.4.4](https://pypi.org/project/cuda-bindings/13.4.4/) | CUDA Python 바인딩; R:간접; 설치: lock만 | Apache-2.0; metadata 원문·동봉 고지 해시는 근거 JSON 참조 |
| 오픈소스 | [cuda-pathfinder 1.8.5](https://pypi.org/project/cuda-pathfinder/1.8.5/) | CUDA 구성 요소 경로 검색; R:간접; 설치: GR | Apache-2.0; metadata 원문·동봉 고지 해시는 근거 JSON 참조 |
| 기타 | [cuda-toolkit 12.8.1](https://pypi.org/project/cuda-toolkit/12.8.1/) | CUDA 구성 요소를 선택하는 메타패키지; R:간접; 설치: GR | 설치 메타패키지 자체 라이선스 미기재·미확인; 설치 대상은 NVIDIA CUDA 구성별 EULA; metadata 원문·동봉 고지 해시는 근거 JSON 참조 |
| 기타 | [cuda-toolkit 13.2.2](https://pypi.org/project/cuda-toolkit/13.2.2/) | CUDA 구성 요소를 선택하는 메타패키지; R:간접; 설치: lock만 | 설치 메타패키지 자체 라이선스 미기재·미확인; 설치 대상은 NVIDIA CUDA 구성별 EULA; metadata 원문·동봉 고지 해시는 근거 JSON 참조 |
| 오픈소스 | [defusedxml 0.7.1](https://pypi.org/project/defusedxml/0.7.1/) | 외부 XML/RSS 안전 파싱; R:선택/server; 설치: LR | PSFL (License 필드) |
| 오픈소스 | [fastapi 0.162.0](https://pypi.org/project/fastapi/0.162.0/) | 서버·GPU HTTP API; R:직접; 설치: LR, GR, GM | MIT |
| 오픈소스 | [filelock 4.2.5](https://pypi.org/project/filelock/4.2.5/) | 상위 패키지 실행·개발 의존성 지원; R:간접; 설치: GR | MIT |
| 오픈소스 | [fsspec 2026.9.0](https://pypi.org/project/fsspec/2026.9.0/) | 상위 패키지 실행·개발 의존성 지원; R:간접; 설치: GR | BSD-3-Clause |
| 오픈소스 | [geoalchemy2 0.20.0](https://pypi.org/project/geoalchemy2/0.20.0/) | PostGIS 공간 데이터 ORM; R:선택/server; 설치: LR | MIT |
| 오픈소스 | [google-crc32c 1.9.0](https://pypi.org/project/google-crc32c/1.9.0/) | TFRecord 레코드 CRC 검증; T:직접; 설치: LT, GT | Apache-2.0 (License 필드) |
| 오픈소스 | [h11 0.16.0](https://pypi.org/project/h11/0.16.0/) | 상위 패키지 실행·개발 의존성 지원; R:간접; 설치: LR, GR, GM | MIT (License 필드) |
| 오픈소스 | [h5py 3.16.0](https://pypi.org/project/h5py/3.16.0/) | HDF5 위성 자료 읽기; T:선택/geo; 설치: LT, GT | BSD-3-Clause |
| 오픈소스 | [hf-xet 1.8.0](https://pypi.org/project/hf-xet/1.8.0/) | 상위 패키지 실행·개발 의존성 지원; R:간접; 설치: GR | Apache-2.0 |
| 오픈소스 | [httpcore 1.0.9](https://pypi.org/project/httpcore/1.0.9/) | 상위 패키지 실행·개발 의존성 지원; R:간접; 설치: LR | BSD-3-Clause |
| 오픈소스 | [httpx 0.28.1](https://pypi.org/project/httpx/0.28.1/) | 외부 API·내부 서비스 HTTP 호출; R:선택/server, R:선택/collector, R:개발/dev; 설치: LR | BSD-3-Clause (License 필드) |
| 오픈소스 | [huggingface-hub 0.36.2](https://pypi.org/project/huggingface-hub/0.36.2/) | 상위 패키지 실행·개발 의존성 지원; R:간접; 설치: GR | Apache (License 필드) |
| 오픈소스 | [idna 3.20](https://pypi.org/project/idna/3.20/) | 상위 패키지 실행·개발 의존성 지원; R:간접, T:간접; 설치: LR, LT, GR, GT, GM | BSD-3-Clause |
| 오픈소스 | [iniconfig 2.3.1](https://pypi.org/project/iniconfig/2.3.1/) | 상위 패키지 실행·개발 의존성 지원; R:간접, T:간접; 설치: LR, LT | MIT |
| 오픈소스 | [jinja2 3.1.6](https://pypi.org/project/jinja2/3.1.6/) | 상위 패키지 실행·개발 의존성 지원; R:간접; 설치: GR | BSD 계열 (세부 조항 수 미표기) (classifier만 있음) |
| 오픈소스 | [joblib 1.6.0](https://pypi.org/project/joblib/1.6.0/) | 상위 패키지 실행·개발 의존성 지원; R:간접, T:간접; 설치: LT, GR, GT, GM | BSD-3-Clause |
| 오픈소스 | [jsonschema 4.23.0](https://pypi.org/project/jsonschema/4.23.0/) | JSON/API 계약 검증; R:개발/api-contract; 설치: LR | MIT (License 필드) |
| 오픈소스 | [jsonschema-path 0.3.4](https://pypi.org/project/jsonschema-path/0.3.4/) | 상위 패키지 실행·개발 의존성 지원; R:간접; 설치: LR | Apache-2.0 (License 필드) |
| 오픈소스 | [jsonschema-specifications 2025.9.1](https://pypi.org/project/jsonschema-specifications/2025.9.1/) | 상위 패키지 실행·개발 의존성 지원; R:간접; 설치: LR | MIT |
| 오픈소스 | [kombu 5.6.2](https://pypi.org/project/kombu/5.6.2/) | 상위 패키지 실행·개발 의존성 지원; R:간접; 설치: LR | BSD-3-Clause (License 필드) |
| 오픈소스 | [lazy-object-proxy 1.13.0](https://pypi.org/project/lazy-object-proxy/1.13.0/) | 상위 패키지 실행·개발 의존성 지원; R:간접; 설치: LR | BSD-2-Clause |
| 오픈소스 | [mako 1.4.3](https://pypi.org/project/mako/1.4.3/) | 상위 패키지 실행·개발 의존성 지원; R:간접; 설치: LR | MIT |
| 오픈소스 | [markupsafe 3.0.4](https://pypi.org/project/markupsafe/3.0.4/) | 상위 패키지 실행·개발 의존성 지원; R:간접; 설치: LR, GR | BSD-3-Clause |
| 오픈소스 | [mpmath 1.3.0](https://pypi.org/project/mpmath/1.3.0/) | 상위 패키지 실행·개발 의존성 지원; R:간접; 설치: GR | BSD (License 필드) |
| 오픈소스 | [narwhals 2.28.0](https://pypi.org/project/narwhals/2.28.0/) | 상위 패키지 실행·개발 의존성 지원; R:간접, T:간접; 설치: LT, GR, GT, GM | MIT |
| 오픈소스 | [netcdf4 1.7.5.1.post1](https://pypi.org/project/netcdf4/1.7.5.1.post1/) | GK2A/GOES NetCDF 위성 자료 읽기; T:선택/geo; 설치: LT, GT | MIT |
| 오픈소스 | [networkx 3.7](https://pypi.org/project/networkx/3.7/) | 상위 패키지 실행·개발 의존성 지원; R:간접; 설치: GR | BSD-3-Clause |
| 오픈소스 | [numpy 2.5.4](https://pypi.org/project/numpy/2.5.4/) | 격자·특징·수치 연산; R:선택/ml, T:직접; 설치: LT, GR, GT, GM | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 |
| 기타 | [nvidia-cublas 13.4.1.3](https://pypi.org/project/nvidia-cublas/13.4.1.3/) | CUDA 연산·통신 바이너리 지원; R:간접; 설치: lock만 | NVIDIA CUDA EULA + 포함 코드의 추가 고지 (고정 wheel LICENSE 확인); metadata 원문·동봉 고지 해시는 근거 JSON 참조 |
| 기타 | [nvidia-cublas-cu12 12.8.4.1](https://pypi.org/project/nvidia-cublas-cu12/12.8.4.1/) | CUDA 연산·통신 바이너리 지원; R:간접; 설치: GR | NVIDIA CUDA EULA + 포함 코드의 추가 고지 (고정 wheel LICENSE 확인); metadata 원문·동봉 고지 해시는 근거 JSON 참조 |
| 기타 | [nvidia-cuda-cccl 13.3.4.3.1](https://pypi.org/project/nvidia-cuda-cccl/13.3.4.3.1/) | CUDA 연산·통신 바이너리 지원; R:간접; 설치: lock만 | NVIDIA CUDA EULA + 포함 코드의 추가 고지 (고정 wheel LICENSE 확인); metadata 원문·동봉 고지 해시는 근거 JSON 참조 |
| 기타 | [nvidia-cuda-cupti 13.2.86](https://pypi.org/project/nvidia-cuda-cupti/13.2.86/) | CUDA 연산·통신 바이너리 지원; R:간접; 설치: lock만 | NVIDIA CUDA EULA + 포함 코드의 추가 고지 (고정 wheel LICENSE 확인); metadata 원문·동봉 고지 해시는 근거 JSON 참조 |
| 기타 | [nvidia-cuda-cupti-cu12 12.8.90](https://pypi.org/project/nvidia-cuda-cupti-cu12/12.8.90/) | CUDA 연산·통신 바이너리 지원; R:간접; 설치: GR | NVIDIA CUDA EULA + 포함 코드의 추가 고지 (고정 wheel LICENSE 확인); metadata 원문·동봉 고지 해시는 근거 JSON 참조 |
| 기타 | [nvidia-cuda-nvrtc 13.2.86](https://pypi.org/project/nvidia-cuda-nvrtc/13.2.86/) | CUDA 연산·통신 바이너리 지원; R:간접; 설치: lock만 | NVIDIA CUDA EULA + 포함 코드의 추가 고지 (고정 wheel LICENSE 확인); metadata 원문·동봉 고지 해시는 근거 JSON 참조 |
| 기타 | [nvidia-cuda-nvrtc-cu12 12.8.93](https://pypi.org/project/nvidia-cuda-nvrtc-cu12/12.8.93/) | CUDA 연산·통신 바이너리 지원; R:간접; 설치: GR | NVIDIA CUDA EULA + 포함 코드의 추가 고지 (고정 wheel LICENSE 확인); metadata 원문·동봉 고지 해시는 근거 JSON 참조 |
| 기타 | [nvidia-cuda-runtime 13.2.86](https://pypi.org/project/nvidia-cuda-runtime/13.2.86/) | CUDA 연산·통신 바이너리 지원; R:간접; 설치: lock만 | NVIDIA CUDA EULA + 포함 코드의 추가 고지 (고정 wheel LICENSE 확인); metadata 원문·동봉 고지 해시는 근거 JSON 참조 |
| 기타 | [nvidia-cuda-runtime-cu12 12.8.90](https://pypi.org/project/nvidia-cuda-runtime-cu12/12.8.90/) | CUDA 연산·통신 바이너리 지원; R:간접; 설치: GR | NVIDIA CUDA EULA + 포함 코드의 추가 고지 (고정 wheel LICENSE 확인); metadata 원문·동봉 고지 해시는 근거 JSON 참조 |
| 기타 | [nvidia-cudnn-cu12 9.19.0.56](https://pypi.org/project/nvidia-cudnn-cu12/9.19.0.56/) | CUDA 연산·통신 바이너리 지원; R:간접; 설치: GR | NVIDIA SDK License Agreement (고정 wheel LICENSE 확인); metadata 원문·동봉 고지 해시는 근거 JSON 참조 |
| 기타 | [nvidia-cudnn-cu13 9.26.0.51](https://pypi.org/project/nvidia-cudnn-cu13/9.26.0.51/) | CUDA 연산·통신 바이너리 지원; R:간접; 설치: lock만 | NVIDIA SDK License Agreement (고정 wheel LICENSE 확인); metadata 원문·동봉 고지 해시는 근거 JSON 참조 |
| 기타 | [nvidia-cufft 12.2.0.57](https://pypi.org/project/nvidia-cufft/12.2.0.57/) | CUDA 연산·통신 바이너리 지원; R:간접; 설치: lock만 | NVIDIA CUDA EULA + 포함 코드의 추가 고지 (고정 wheel LICENSE 확인); metadata 원문·동봉 고지 해시는 근거 JSON 참조 |
| 기타 | [nvidia-cufft-cu12 11.3.3.83](https://pypi.org/project/nvidia-cufft-cu12/11.3.3.83/) | CUDA 연산·통신 바이너리 지원; R:간접; 설치: GR | NVIDIA CUDA EULA + 포함 코드의 추가 고지 (고정 wheel LICENSE 확인); metadata 원문·동봉 고지 해시는 근거 JSON 참조 |
| 기타 | [nvidia-cufile 1.17.1.22](https://pypi.org/project/nvidia-cufile/1.17.1.22/) | CUDA 연산·통신 바이너리 지원; R:간접; 설치: lock만 | NVIDIA CUDA EULA + 포함 코드의 추가 고지 (고정 wheel LICENSE 확인); metadata 원문·동봉 고지 해시는 근거 JSON 참조 |
| 기타 | [nvidia-cufile-cu12 1.13.1.3](https://pypi.org/project/nvidia-cufile-cu12/1.13.1.3/) | CUDA 연산·통신 바이너리 지원; R:간접; 설치: GR | NVIDIA CUDA EULA + 포함 코드의 추가 고지 (고정 wheel LICENSE 확인); metadata 원문·동봉 고지 해시는 근거 JSON 참조 |
| 기타 | [nvidia-curand-cu12 10.3.9.90](https://pypi.org/project/nvidia-curand-cu12/10.3.9.90/) | CUDA 연산·통신 바이너리 지원; R:간접; 설치: GR | NVIDIA CUDA EULA + 포함 코드의 추가 고지 (고정 wheel LICENSE 확인); metadata 원문·동봉 고지 해시는 근거 JSON 참조 |
| 기타 | [nvidia-cusolver 12.2.0.11](https://pypi.org/project/nvidia-cusolver/12.2.0.11/) | CUDA 연산·통신 바이너리 지원; R:간접; 설치: lock만 | NVIDIA CUDA EULA + 포함 코드의 추가 고지 (고정 wheel LICENSE 확인); metadata 원문·동봉 고지 해시는 근거 JSON 참조 |
| 기타 | [nvidia-cusolver-cu12 11.7.3.90](https://pypi.org/project/nvidia-cusolver-cu12/11.7.3.90/) | CUDA 연산·통신 바이너리 지원; R:간접; 설치: GR | NVIDIA CUDA EULA + 포함 코드의 추가 고지 (고정 wheel LICENSE 확인); metadata 원문·동봉 고지 해시는 근거 JSON 참조 |
| 기타 | [nvidia-cusparse 12.7.10.12](https://pypi.org/project/nvidia-cusparse/12.7.10.12/) | CUDA 연산·통신 바이너리 지원; R:간접; 설치: lock만 | NVIDIA CUDA EULA + 포함 코드의 추가 고지 (고정 wheel LICENSE 확인); metadata 원문·동봉 고지 해시는 근거 JSON 참조 |
| 기타 | [nvidia-cusparse-cu12 12.5.8.93](https://pypi.org/project/nvidia-cusparse-cu12/12.5.8.93/) | CUDA 연산·통신 바이너리 지원; R:간접; 설치: GR | NVIDIA CUDA EULA + 포함 코드의 추가 고지 (고정 wheel LICENSE 확인); metadata 원문·동봉 고지 해시는 근거 JSON 참조 |
| 기타 | [nvidia-cusparselt-cu12 0.7.1](https://pypi.org/project/nvidia-cusparselt-cu12/0.7.1/) | CUDA 연산·통신 바이너리 지원; R:간접; 설치: GR | NVIDIA SDK License Agreement (고정 wheel LICENSE 확인); metadata 원문·동봉 고지 해시는 근거 JSON 참조 |
| 기타 | [nvidia-cusparselt-cu13 0.8.1](https://pypi.org/project/nvidia-cusparselt-cu13/0.8.1/) | CUDA 연산·통신 바이너리 지원; R:간접; 설치: lock만 | NVIDIA SDK License Agreement (고정 wheel LICENSE 확인); metadata 원문·동봉 고지 해시는 근거 JSON 참조 |
| 기타 | [nvidia-nccl-cu12 2.28.9](https://pypi.org/project/nvidia-nccl-cu12/2.28.9/) | CUDA 연산·통신 바이너리 지원; R:간접; 설치: GR | BSD-3-Clause (고정 wheel LICENSE 확인; 최신 main과 구분); metadata 원문·동봉 고지 해시는 근거 JSON 참조 |
| 기타 | [nvidia-nccl-cu13 2.30.7](https://pypi.org/project/nvidia-nccl-cu13/2.30.7/) | CUDA 연산·통신 바이너리 지원; R:간접; 설치: lock만 | BSD-3-Clause (고정 wheel LICENSE 확인; 최신 main과 구분); metadata 원문·동봉 고지 해시는 근거 JSON 참조 |
| 기타 | [nvidia-nccl-cu13 2.32.3](https://pypi.org/project/nvidia-nccl-cu13/2.32.3/) | CUDA 연산·통신 바이너리 지원; R:간접, T:간접; 설치: GT, GM | BSD-3-Clause (고정 wheel LICENSE 확인; 최신 main과 구분); metadata 원문·동봉 고지 해시는 근거 JSON 참조 |
| 기타 | [nvidia-nvjitlink 13.4.92](https://pypi.org/project/nvidia-nvjitlink/13.4.92/) | CUDA 연산·통신 바이너리 지원; R:간접; 설치: lock만 | NVIDIA CUDA EULA + 포함 코드의 추가 고지 (고정 wheel LICENSE 확인); metadata 원문·동봉 고지 해시는 근거 JSON 참조 |
| 기타 | [nvidia-nvjitlink-cu12 12.8.93](https://pypi.org/project/nvidia-nvjitlink-cu12/12.8.93/) | CUDA 연산·통신 바이너리 지원; R:간접; 설치: GR | NVIDIA CUDA EULA + 포함 코드의 추가 고지 (고정 wheel LICENSE 확인); metadata 원문·동봉 고지 해시는 근거 JSON 참조 |
| 기타 | [nvidia-nvshmem-cu12 3.4.5](https://pypi.org/project/nvidia-nvshmem-cu12/3.4.5/) | CUDA 연산·통신 바이너리 지원; R:간접; 설치: GR | NVIDIA CUDA EULA + 포함 코드의 추가 고지 (고정 wheel LICENSE 확인); metadata 원문·동봉 고지 해시는 근거 JSON 참조 |
| 기타 | [nvidia-nvshmem-cu13 3.7.2](https://pypi.org/project/nvidia-nvshmem-cu13/3.7.2/) | CUDA 연산·통신 바이너리 지원; R:간접; 설치: lock만 | NVIDIA CUDA EULA + 포함 코드의 추가 고지 (고정 wheel LICENSE 확인); metadata 원문·동봉 고지 해시는 근거 JSON 참조 |
| 기타 | [nvidia-nvtx 13.2.86](https://pypi.org/project/nvidia-nvtx/13.2.86/) | CUDA 연산·통신 바이너리 지원; R:간접; 설치: lock만 | Apache-2.0 WITH LLVM-exception (고정 wheel LICENSE 확인); metadata 원문·동봉 고지 해시는 근거 JSON 참조 |
| 오픈소스 | [nvidia-nvtx-cu12 12.8.90](https://pypi.org/project/nvidia-nvtx-cu12/12.8.90/) | CUDA 연산·통신 바이너리 지원; R:간접; 설치: GR | Apache-2.0 WITH LLVM-exception (고정 wheel LICENSE 확인); metadata 원문·동봉 고지 해시는 근거 JSON 참조 |
| 오픈소스 | [openapi-schema-validator 0.6.3](https://pypi.org/project/openapi-schema-validator/0.6.3/) | 상위 패키지 실행·개발 의존성 지원; R:간접; 설치: LR | BSD-3-Clause (License 필드) |
| 오픈소스 | [openapi-spec-validator 0.7.2](https://pypi.org/project/openapi-spec-validator/0.7.2/) | OpenAPI 계약 검증; R:개발/api-contract; 설치: LR | Apache-2.0 (License 필드) |
| 오픈소스 | [opentelemetry-api 1.45.2](https://pypi.org/project/opentelemetry-api/1.45.2/) | 상위 패키지 실행·개발 의존성 지원; R:간접; 설치: LR, GR, GM | Apache-2.0 |
| 오픈소스 | [packaging 26.3](https://pypi.org/project/packaging/26.3/) | 버전·요구사항 처리 지원; 빌드 격리 환경 실행 버전은 별도 미확정; R:간접, T:간접; 설치: LR, LT, GR, GT | Apache-2.0 OR BSD-2-Clause |
| 오픈소스 | [pandas 2.3.3](https://pypi.org/project/pandas/2.3.3/) | ML 표 데이터 처리; R:선택/ml; 설치: GM | BSD-3-Clause 주코드 + 동봉 제3자 고지 조건 (장문 License 필드) |
| 오픈소스 | [pathable 0.4.4](https://pypi.org/project/pathable/0.4.4/) | 상위 패키지 실행·개발 의존성 지원; R:간접; 설치: LR | Apache-2.0 (License 필드) |
| 오픈소스 | [pgvector 0.5.1](https://pypi.org/project/pgvector/0.5.1/) | PostgreSQL 벡터 타입 연동; R:선택/server; 설치: LR | MIT |
| 오픈소스 | [planetary-computer 1.0.0](https://pypi.org/project/planetary-computer/1.0.0/) | Microsoft 공개 지리 자료 STAC·서명 자산 접근; T:선택/geo; 설치: LT, GT | MIT (동봉 License 전문에서 확인) |
| 오픈소스 | [pluggy 1.7.0](https://pypi.org/project/pluggy/1.7.0/) | 상위 패키지 실행·개발 의존성 지원; R:간접, T:간접; 설치: LR, LT | MIT (License 필드) |
| 오픈소스 | [prometheus-client 0.26.0](https://pypi.org/project/prometheus-client/0.26.0/) | Prometheus 형식 메트릭 노출; R:선택/server; 설치: LR | Apache-2.0 AND BSD-2-Clause |
| 오픈소스 | [prompt-toolkit 3.0.53](https://pypi.org/project/prompt-toolkit/3.0.53/) | 상위 패키지 실행·개발 의존성 지원; R:간접; 설치: LR | BSD 계열 (세부 조항 수 미표기) (classifier만 있음) |
| 오픈소스 | [protobuf 7.36.2](https://pypi.org/project/protobuf/7.36.2/) | TFRecord Example 파싱; T:직접; 설치: LT, GT | 3-Clause BSD License (License 필드) |
| 오픈소스 | [psutil 7.2.2](https://pypi.org/project/psutil/7.2.2/) | 상위 패키지 실행·개발 의존성 지원; R:간접; 설치: GR | BSD-3-Clause (License 필드) |
| 오픈소스 | [psycopg 3.3.6](https://pypi.org/project/psycopg/3.3.6/) | PostgreSQL 드라이버; R:선택/server; 설치: LR | LGPL-3.0-only |
| 오픈소스 | [psycopg-binary 3.3.6](https://pypi.org/project/psycopg-binary/3.3.6/) | PostgreSQL 드라이버 바이너리 배포; R:간접; 설치: LR | LGPL-3.0-only |
| 오픈소스 | [pyarrow 26.0.0](https://pypi.org/project/pyarrow/26.0.0/) | 학습 데이터 Parquet 읽기·쓰기; R:선택/ml, T:직접; 설치: LT, GT, GM | Apache-2.0 |
| 오픈소스 | [pycparser 3.12](https://pypi.org/project/pycparser/3.12/) | 상위 패키지 실행·개발 의존성 지원; R:간접; 설치: LR | BSD-3-Clause |
| 오픈소스 | [pydantic 2.14.2](https://pypi.org/project/pydantic/2.14.2/) | 상위 패키지 실행·개발 의존성 지원; R:간접, T:간접; 설치: LR, LT, GR, GT, GM | MIT |
| 오픈소스 | [pydantic-core 2.50.2](https://pypi.org/project/pydantic-core/2.50.2/) | 상위 패키지 실행·개발 의존성 지원; R:간접, T:간접; 설치: LR, LT, GR, GT, GM | MIT |
| 오픈소스 | [pydantic-settings 2.16.2](https://pypi.org/project/pydantic-settings/2.16.2/) | 환경 설정 모델; R:직접; 설치: LR, GR, GM | MIT |
| 오픈소스 | [pygments 2.21.0](https://pypi.org/project/pygments/2.21.0/) | 상위 패키지 실행·개발 의존성 지원; R:간접, T:간접; 설치: LR, LT | BSD-2-Clause |
| 오픈소스 | [pyjwt 2.15.1](https://pypi.org/project/pyjwt/2.15.1/) | 사용자 JWT 서명·검증; R:선택/server; 설치: LR | MIT |
| 오픈소스 | [pyparsing 3.3.3](https://pypi.org/project/pyparsing/3.3.3/) | 상위 패키지 실행·개발 의존성 지원; T:간접; 설치: LT, GT | MIT |
| 오픈소스 | [pyproj 3.8.0](https://pypi.org/project/pyproj/3.8.0/) | 좌표계 투영·변환; T:선택/geo; 설치: LT, GT | MIT |
| 오픈소스 | [pystac 1.15.2](https://pypi.org/project/pystac/1.15.2/) | 상위 패키지 실행·개발 의존성 지원; T:간접; 설치: LT, GT | Apache-2.0 (License 필드) |
| 오픈소스 | [pystac-client 0.9.1](https://pypi.org/project/pystac-client/0.9.1/) | STAC 확장 메타데이터 처리; T:간접; 설치: LT, GT | Apache-2.0 (License 필드) |
| 오픈소스 | [pystac-core 1.15.2](https://pypi.org/project/pystac-core/1.15.2/) | STAC 확장 메타데이터 처리; T:간접; 설치: LT, GT | Apache-2.0 (License 필드) |
| 오픈소스 | [pystac-ext-classification 2.0.1](https://pypi.org/project/pystac-ext-classification/2.0.1/) | STAC 확장 메타데이터 처리; T:간접; 설치: LT, GT | Apache-2.0 (License 필드) |
| 오픈소스 | [pystac-ext-datacube 2.2.1](https://pypi.org/project/pystac-ext-datacube/2.2.1/) | STAC 확장 메타데이터 처리; T:간접; 설치: LT, GT | Apache-2.0 (License 필드) |
| 오픈소스 | [pystac-ext-eo 1.1.1](https://pypi.org/project/pystac-ext-eo/1.1.1/) | STAC 확장 메타데이터 처리; T:간접; 설치: LT, GT | Apache-2.0 (License 필드) |
| 오픈소스 | [pystac-ext-file 2.1.1](https://pypi.org/project/pystac-ext-file/2.1.1/) | STAC 확장 메타데이터 처리; T:간접; 설치: LT, GT | Apache-2.0 (License 필드) |
| 오픈소스 | [pystac-ext-grid 1.1.1](https://pypi.org/project/pystac-ext-grid/1.1.1/) | STAC 확장 메타데이터 처리; T:간접; 설치: LT, GT | Apache-2.0 (License 필드) |
| 오픈소스 | [pystac-ext-item-assets 1.0.1](https://pypi.org/project/pystac-ext-item-assets/1.0.1/) | STAC 확장 메타데이터 처리; T:간접; 설치: LT, GT | Apache-2.0 (License 필드) |
| 오픈소스 | [pystac-ext-label 1.0.2](https://pypi.org/project/pystac-ext-label/1.0.2/) | STAC 확장 메타데이터 처리; T:간접; 설치: LT, GT | Apache-2.0 (License 필드) |
| 오픈소스 | [pystac-ext-mgrs 1.0.1](https://pypi.org/project/pystac-ext-mgrs/1.0.1/) | STAC 확장 메타데이터 처리; T:간접; 설치: LT, GT | Apache-2.0 (License 필드) |
| 오픈소스 | [pystac-ext-mlm 1.4.1](https://pypi.org/project/pystac-ext-mlm/1.4.1/) | STAC 확장 메타데이터 처리; T:간접; 설치: LT, GT | Apache-2.0 (License 필드) |
| 오픈소스 | [pystac-ext-pointcloud 1.0.1](https://pypi.org/project/pystac-ext-pointcloud/1.0.1/) | STAC 확장 메타데이터 처리; T:간접; 설치: LT, GT | Apache-2.0 (License 필드) |
| 오픈소스 | [pystac-ext-projection 2.0.1](https://pypi.org/project/pystac-ext-projection/2.0.1/) | STAC 확장 메타데이터 처리; T:간접; 설치: LT, GT | Apache-2.0 (License 필드) |
| 오픈소스 | [pystac-ext-raster 1.1.1](https://pypi.org/project/pystac-ext-raster/1.1.1/) | STAC 확장 메타데이터 처리; T:간접; 설치: LT, GT | Apache-2.0 (License 필드) |
| 오픈소스 | [pystac-ext-render 2.0.0](https://pypi.org/project/pystac-ext-render/2.0.0/) | STAC 확장 메타데이터 처리; T:간접; 설치: LT, GT | Apache-2.0 (License 필드) |
| 오픈소스 | [pystac-ext-sar 1.0.1](https://pypi.org/project/pystac-ext-sar/1.0.1/) | STAC 확장 메타데이터 처리; T:간접; 설치: LT, GT | Apache-2.0 (License 필드) |
| 오픈소스 | [pystac-ext-sat 1.0.1](https://pypi.org/project/pystac-ext-sat/1.0.1/) | STAC 확장 메타데이터 처리; T:간접; 설치: LT, GT | Apache-2.0 (License 필드) |
| 오픈소스 | [pystac-ext-scientific 1.0.1](https://pypi.org/project/pystac-ext-scientific/1.0.1/) | STAC 확장 메타데이터 처리; T:간접; 설치: LT, GT | Apache-2.0 (License 필드) |
| 오픈소스 | [pystac-ext-storage 2.0.1](https://pypi.org/project/pystac-ext-storage/2.0.1/) | STAC 확장 메타데이터 처리; T:간접; 설치: LT, GT | Apache-2.0 (License 필드) |
| 오픈소스 | [pystac-ext-table 1.2.1](https://pypi.org/project/pystac-ext-table/1.2.1/) | STAC 확장 메타데이터 처리; T:간접; 설치: LT, GT | Apache-2.0 (License 필드) |
| 오픈소스 | [pystac-ext-timestamps 1.1.1](https://pypi.org/project/pystac-ext-timestamps/1.1.1/) | STAC 확장 메타데이터 처리; T:간접; 설치: LT, GT | Apache-2.0 (License 필드) |
| 오픈소스 | [pystac-ext-version 1.2.1](https://pypi.org/project/pystac-ext-version/1.2.1/) | STAC 확장 메타데이터 처리; T:간접; 설치: LT, GT | Apache-2.0 (License 필드) |
| 오픈소스 | [pystac-ext-view 1.0.1](https://pypi.org/project/pystac-ext-view/1.0.1/) | STAC 확장 메타데이터 처리; T:간접; 설치: LT, GT | Apache-2.0 (License 필드) |
| 오픈소스 | [pystac-ext-xarray-assets 1.0.1](https://pypi.org/project/pystac-ext-xarray-assets/1.0.1/) | STAC 확장 메타데이터 처리; T:간접; 설치: LT, GT | Apache-2.0 (License 필드) |
| 오픈소스 | [pytest 9.2.0](https://pypi.org/project/pytest/9.2.0/) | 자동 검증; R:개발/dev, T:개발/dev; 설치: LR, LT | MIT |
| 오픈소스 | [python-dateutil 3.0.0](https://pypi.org/project/python-dateutil/3.0.0/) | 상위 패키지 실행·개발 의존성 지원; R:간접, T:간접; 설치: LR, LT, GT, GM | Dual License (License 필드) |
| 오픈소스 | [python-dotenv 1.2.4](https://pypi.org/project/python-dotenv/1.2.4/) | 상위 패키지 실행·개발 의존성 지원; R:간접, T:간접; 설치: LR, LT, GR, GT, GM | BSD-3-Clause (License 필드) |
| 오픈소스 | [pytz 2026.6](https://pypi.org/project/pytz/2026.6/) | 상위 패키지 실행·개발 의존성 지원; R:간접, T:간접; 설치: LT, GT, GM | MIT (License 필드) |
| 오픈소스 | [pyyaml 6.0.2](https://pypi.org/project/pyyaml/6.0.2/) | YAML·계약 설정 파싱; R:개발/dev, R:개발/api-contract; 설치: LR, GR | MIT (License 필드) |
| 오픈소스 | [rasterio 1.5.2](https://pypi.org/project/rasterio/1.5.2/) | DEM·토지피복 래스터 처리; T:선택/geo; 설치: LT, GT | BSD-3-Clause |
| 오픈소스 | [redis 6.4.0](https://pypi.org/project/redis/6.4.0/) | Redis Python 클라이언트; Redis 서버 라이선스와 별개; R:간접; 설치: LR | MIT |
| 오픈소스 | [referencing 0.36.2](https://pypi.org/project/referencing/0.36.2/) | 상위 패키지 실행·개발 의존성 지원; R:간접; 설치: LR | MIT |
| 오픈소스 | [regex 2026.9.29](https://pypi.org/project/regex/2026.9.29/) | 상위 패키지 실행·개발 의존성 지원; R:간접; 설치: GR | Apache-2.0 AND CNRI-Python |
| 오픈소스 | [requests 2.34.2](https://pypi.org/project/requests/2.34.2/) | 상위 패키지 실행·개발 의존성 지원; R:간접, T:간접; 설치: LR, LT, GR, GT | Apache-2.0 (License 필드) |
| 오픈소스 | [rfc3339-validator 0.1.4](https://pypi.org/project/rfc3339-validator/0.1.4/) | 상위 패키지 실행·개발 의존성 지원; R:간접; 설치: LR | MIT license (License 필드) |
| 오픈소스 | [rpds-py 2026.9.1](https://pypi.org/project/rpds-py/2026.9.1/) | 상위 패키지 실행·개발 의존성 지원; R:간접; 설치: LR | MIT |
| 오픈소스 | [ruff 0.17.3](https://pypi.org/project/ruff/0.17.3/) | Python 린트·포맷; R:개발/dev, T:개발/dev; 설치: LR, LT | MIT |
| 오픈소스 | [safetensors 0.8.0](https://pypi.org/project/safetensors/0.8.0/) | 상위 패키지 실행·개발 의존성 지원; R:간접; 설치: GR | Apache 계열 (버전 미표기) (classifier만 있음) |
| 오픈소스 | [scikit-learn 1.9.1](https://pypi.org/project/scikit-learn/1.9.1/) | 평가 지표·보정·학습 지원; R:선택/ml, T:선택/train; 설치: LT, GR, GT, GM | BSD-3-Clause |
| 오픈소스 | [scipy 1.18.1](https://pypi.org/project/scipy/1.18.1/) | 공간·거리·행렬 수치 처리; T:직접, R:간접; 설치: LT, GR, GT, GM | BSD 계열 주코드 + 번들 라이선스 (아래 설명) |
| 오픈소스 | [sentence-transformers 5.7.0](https://pypi.org/project/sentence-transformers/5.7.0/) | Qwen 임베딩 모델 실행; R:선택/gpu; 설치: GR | Apache-2.0 |
| 오픈소스 | [setuptools 81.0.0](https://pypi.org/project/setuptools/81.0.0/) | Python 패키징 지원; R:간접; 설치: GR | MIT |
| 오픈소스 | [shapely 2.2.0](https://pypi.org/project/shapely/2.2.0/) | 경계·기하 연산; T:선택/geo; 설치: LT, GT | BSD-3-Clause |
| 오픈소스 | [six 1.17.0](https://pypi.org/project/six/1.17.0/) | 상위 패키지 실행·개발 의존성 지원; R:간접, T:간접; 설치: LR, LT, GT, GM | MIT (License 필드) |
| 오픈소스 | [sqlalchemy 2.1.6](https://pypi.org/project/sqlalchemy/2.1.6/) | DB ORM·SQL 접근; R:선택/server; 설치: LR | MIT |
| 오픈소스 | [starlette 1.10.0](https://pypi.org/project/starlette/1.10.0/) | 상위 패키지 실행·개발 의존성 지원; R:간접; 설치: LR, GR, GM | BSD-3-Clause |
| 오픈소스 | [sympy 1.14.0](https://pypi.org/project/sympy/1.14.0/) | 상위 패키지 실행·개발 의존성 지원; R:간접; 설치: GR | BSD (License 필드) |
| 오픈소스 | [threadpoolctl 3.7.0](https://pypi.org/project/threadpoolctl/3.7.0/) | 상위 패키지 실행·개발 의존성 지원; R:간접, T:간접; 설치: LT, GR, GT, GM | BSD-3-Clause |
| 오픈소스 | [tokenizers 0.22.2](https://pypi.org/project/tokenizers/0.22.2/) | 상위 패키지 실행·개발 의존성 지원; R:간접; 설치: GR | Apache 계열 (버전 미표기) (classifier만 있음) |
| 오픈소스 | [torch 2.11.0+cu128](https://download.pytorch.org/whl/cu128/torch/) | Qwen GPU 텐서·추론 실행; R:선택/gpu; 설치: GR | BSD-3-Clause (License 필드) |
| 오픈소스 | [torch 2.15.0](https://pypi.org/project/torch/2.15.0/) | Qwen GPU 텐서·추론 실행; R:선택/gpu; 설치: lock만 | Apache-2.0 AND Apache-2.0 WITH LLVM-exception AND BSD-2-Clause AND BSD-3-Clause AND BSL-1.0 AND ISC AND MIT AND Zlib |
| 오픈소스 | [tqdm 4.70.1](https://pypi.org/project/tqdm/4.70.1/) | 상위 패키지 실행·개발 의존성 지원; R:간접; 설치: GR | MPL-2.0 AND MIT (License 필드) |
| 오픈소스 | [transformers 4.57.6](https://pypi.org/project/transformers/4.57.6/) | Qwen 모델·토크나이저 로드; R:선택/gpu; 설치: GR | Apache 2.0 License (License 필드) |
| 오픈소스 | [triton 3.6.0](https://pypi.org/project/triton/3.6.0/) | PyTorch GPU 커널 지원; R:간접; 설치: GR | MIT (classifier만 있음) |
| 오픈소스 | [triton 3.9.0](https://pypi.org/project/triton/3.9.0/) | PyTorch GPU 커널 지원; R:간접; 설치: lock만 | MIT (License 필드) |
| 오픈소스 | [typing-extensions 4.16.0](https://pypi.org/project/typing-extensions/4.16.0/) | 상위 패키지 실행·개발 의존성 지원; R:간접, T:간접; 설치: LR, LT, GR, GT, GM | PSF-2.0 |
| 오픈소스 | [typing-inspection 0.4.4](https://pypi.org/project/typing-inspection/0.4.4/) | 상위 패키지 실행·개발 의존성 지원; R:간접, T:간접; 설치: LR, LT, GR, GT, GM | MIT |
| 오픈소스 | [tzdata 2026.6](https://pypi.org/project/tzdata/2026.6/) | 상위 패키지 실행·개발 의존성 지원; R:간접, T:간접; 설치: LR, LT, GT, GM | Apache-2.0 (License 필드) |
| 오픈소스 | [tzlocal 5.4.5](https://pypi.org/project/tzlocal/5.4.5/) | 상위 패키지 실행·개발 의존성 지원; R:간접; 설치: LR | MIT |
| 오픈소스 | [urllib3 2.8.0](https://pypi.org/project/urllib3/2.8.0/) | 상위 패키지 실행·개발 의존성 지원; R:간접, T:간접; 설치: LR, LT, GR, GT | MIT |
| 오픈소스 | [uvicorn 0.54.0](https://pypi.org/project/uvicorn/0.54.0/) | ASGI 서버; R:직접; 설치: LR, GR, GM | BSD-3-Clause |
| 오픈소스 | [vine 5.1.0](https://pypi.org/project/vine/5.1.0/) | 상위 패키지 실행·개발 의존성 지원; R:간접; 설치: LR | BSD (License 필드) |
| 오픈소스 | [wcwidth 0.9.4](https://pypi.org/project/wcwidth/0.9.4/) | 상위 패키지 실행·개발 의존성 지원; R:간접; 설치: LR | MIT (classifier만 있음) |
| 오픈소스 | [xgboost 3.4.1](https://pypi.org/project/xgboost/3.4.1/) | 산불 관측·접근 위험 연구 모델 학습·추론; R:선택/ml, T:선택/train; 설치: LT, GT, GM | Apache-2.0 |

### 빌드 의존성과 직접 개발 패키지

| 구분 | 명칭 | 용도 | 라이선스 |
| --- | --- | --- | --- |
| 오픈소스 | [hatchling `>=1.27,<2`](https://pypi.org/project/hatchling/) | 루트·학습 프로젝트 wheel/editable 빌드 백엔드. lock에 없음; 빌드 격리 환경의 실제 사용 버전은 미확정 | MIT; 실제 배포 시 선택된 버전의 동봉 고지 확인 |
| 기타 | bonghwa-training 0.1.0 | 학습 데이터·검증 도구; 설치: LT, GT | 외부 패키지 아님; 프로젝트 공개 라이선스 미지정 |
| 기타 | bonghwajigi 0.1.0 | 서버·수집·모델 API; 설치: LR, GR, GM | 외부 패키지 아님; 프로젝트 공개 라이선스 미지정 |

### 바이너리 번들과 해석 시 주의할 항목

- SciPy 동봉 고지는 주코드 외 OpenBLAS(`BSD-3-Clause`), LAPACK(`BSD-3-Clause-Open-MPI`), GCC runtime(`GPL-3.0-or-later WITH GCC-exception-3.1`), libquadmath(`LGPL-2.1-or-later`)를 구분한다. 플랫폼마다 포함 여부가 달라질 수 있으므로 실제 wheel의 고지와 파일을 기준으로 확인한다.
- NumPy, pandas, PyArrow, torch, h5py, rasterio, pyproj, shapely 등은 제3자 코드 또는 네이티브 라이브러리 고지를 동봉한다. 특히 h5py의 HDF5, rasterio의 GDAL, pyproj의 PROJ, shapely의 GEOS 고지 파일을 JSON 증거에 포함했다. 위 표의 상위 패키지 라이선스가 동봉 구성 요소 전체를 하나의 조건으로 대체한다는 뜻은 아니다.
- `psycopg`/`psycopg-binary`의 `LGPL-3.0-only`, `certifi`의 `MPL-2.0`, `tqdm`의 `MPL-2.0 AND MIT`, NVIDIA 바이너리의 독점 조건을 별도로 유지한다. `redis` 행은 Python 클라이언트이며 서버 이미지 라이선스는 본문 인프라 표에서 따로 확인한다.
- `cuda-toolkit`은 구성 요소를 묶는 메타패키지다. 메타데이터가 비어 있으므로 이를 MIT/Apache 또는 자유 재배포 가능으로 판정하지 않는다. 36개 고정 버전 wheel의 추가 확인은 아래 부록과 보충 JSON을 따른다. 메타패키지 자체 조건이 미확인인 경우는 그대로 남긴다.
- 잠금 분기의 torch 2.15.0과 실제 GPU 추론 환경의 torch 2.11.0+cu128을 구분한다. CUDA 13 패키지 중에는 초기 `.venv-ml`의 NCCL 2.32.3처럼 설치된 항목도 있으므로, CUDA 계열 전체를 미설치로 묶지 않고 각 행의 설치 환경을 기준으로 확인한다.
- 이 부록은 명시된 Python 잠금 파일과 다섯 가상환경의 배포 패키지 전수 목록이다. 운영체제 전체 패키지·컨테이너 내부 모든 파일·임시 빌드 캐시의 완전한 바이너리 SBOM이라고 주장하지 않는다.

## 10. 확인 방법과 남은 확인 사항

[전수 대조 결과](external-resources/python-coverage.json)에서 외부 패키지·버전 174개 모두 일치했다. [문서 검증 결과](external-resources/document-validation.json)에서 누락 행·잘못된 4열 표·깨진 로컬 링크·인증정보 패턴은 발견되지 않았다. 공식 약관/라이선스의 모든 외부 링크에 대한 자동 가용성 검사나 법적 적합성 보증을 뜻하지 않는다.

이 명세는 발표용 자원 사용 내역이며 배포물에 동봉할 모든 LICENSE/NOTICE 원문을 대체하지 않는다. 버전·라이선스 표현·설치 환경·잠금 파일 해시는 함께 제공하는 [의존성 근거 JSON](external-resources/python-inventory.json)에 보존한다. 패키지 이름이 같더라도 버전과 공급 형태가 다르면 조건을 각각 확인한다.

| 구분 | 명칭 | 용도 | 라이선스 |
| --- | --- | --- | --- |
| 기타 | 기상청 GK2A FF 및 격자 자료 조건 확인 | API 승인 범위, 공개 시연 화면과 원자료/가공 데이터 재배포 범위를 확인할 항목 | 승인 사용자 접근 제한을 확인했으나 제품별 정확한 공공누리 유형·재배포 허용 범위는 미확정 |
| 기타 | ESA CCI Land Cover 판본 조건 확인 | 실제 내려받은 2015 자료의 판본/공급 경로에 대응하는 이용조건을 최종 확인할 항목 | STAC의 `other`를 CC0로 치환하지 않음. 공급자·판본 조건 유지 |
| 기타 | 정부 행동요령과 기사별 권리 확인 | 공개 자료라도 각 페이지의 공공누리 유형과 제3자 저작물 표시가 다름 | 안전한TV 제4유형 및 언론사별 권리를 구분. 기사 전문·이미지·영상의 자유 재배포를 주장하지 않음 |
| 기타 | 프로젝트 자체 배포 라이선스·Loom 라이선스 | 외부 공개 또는 코드 재배포 시 확정할 항목 | 미표기 상태를 공개 사용 허가로 해석하지 않음 |
| 기타 | 앱 외부 자원 목록 | Android 네이버 지도 자원은 마지막 절에 추가 확인; 나머지 앱 자원은 별도 조사 범위 | 전체 앱 제출 자료에는 폰트·이미지·나머지 SDK의 사용 항목과 배포 고지도 별도로 대조해야 함 |

문서를 갱신할 때는 `pyproject.toml`, `training/pyproject.toml`, `uv.lock`, `training/uv.lock`, `deploy/`, 데이터 다운로드 코드/출처 manifest와 실제 모델 revision을 다시 대조한다. 조사만 한 자료를 실제 사용 표로 옮기는 경우에는 API 응답·다운로드·실행 근거와 해당 판본의 이용조건을 함께 갱신한다. 인증키, 비밀번호, 서비스 계정 비공개 키, 서명된 일회성 다운로드 토큰은 이 문서와 근거 파일에 저장하지 않는다.

## 11. 고정 배포물 라이선스 추가 확인

두 lock의 CUDA/NVIDIA **36개 패키지·버전**에 대해 공식 PyPI의 Linux x86_64 또는 플랫폼 공통 wheel을 열어 LICENSE 경로와 SHA-256을 기록했다. 작은 메타패키지 2개에는 LICENSE 파일이 없었다. 설치된 환경의 원본 METADATA·고지 파일은 기존 의존성 JSON에, 이 추가 검사의 정확한 wheel URL·LICENSE 해시는 [보충 검증 JSON](external-resources/supplemental-verification-20261101.json)에 보존한다. 이 추가 검사는 동일 버전의 모든 Python ABI·운영체제 wheel을 검사했다는 뜻은 아니다. 실제 배포 시에는 선택한 artifact와 동봉 고지를 기준으로 삼는다.

| 구분 | 명칭 | 용도 | 라이선스 |
| --- | --- | --- | --- |
| 오픈소스 | cuda-bindings 12.9.10·13.4.4, cuda-pathfinder 1.8.5 | CUDA Python 바인딩·경로 탐색. 설치 여부는 전수 부록의 환경 표기 참고 | 확인한 고정 wheel의 LICENSE: Apache-2.0 |
| 기타 | cuda-toolkit 12.8.1·13.2.2 | CUDA 구성요소 설치 메타패키지 | 메타패키지 자체 metadata·LICENSE 없음, 자체 라이선스 미확인. 설치 대상 CUDA 구성요소는 각각의 NVIDIA 약관 적용 |
| 기타 | cuBLAS·CUPTI·NVRTC·CUDA Runtime·cuFFT·cuFile·cuRAND·cuSOLVER·cuSPARSE·nvJitLink | GPU 수치 계산·실행·프로파일링 | 고정 wheel의 NVIDIA CUDA End User License Agreement와 포함 코드별 추가 고지. 전체를 Apache/BSD 오픈소스로 분류하지 않음. [CUDA EULA](https://docs.nvidia.com/cuda/eula/index.html) |
| 기타 | nvidia-cuda-cccl 13.3.4.3.1 | CUDA C++ 코어 구성 | 배포물의 CUDA EULA 및 CCCL 소스 LICENSE(LLVM 예외를 포함한 Apache 조건), 추가 BSD 고지 등 구성별 조건 |
| 기타 | cuDNN 9.19.0.56·9.26.0.51, cuSPARSELt 0.7.1·0.8.1 | GPU 신경망·희소 행렬 실행 | 고정 wheel의 NVIDIA SDK License Agreement. 공개 소스 라이선스와 다름. 제품·버전별 부속 조건 유지 |
| 오픈소스 | NCCL cu12 2.28.9, cu13 2.30.7·2.32.3 | GPU 통신 런타임 의존성 | **고정 wheel은 BSD-3-Clause**. 최신 GitHub main의 다른 표기를 설치한 과거 버전에 소급 적용하지 않음 |
| 기타 | NVSHMEM cu12 3.4.5, cu13 3.7.2 | GPU 공유 메모리 런타임 의존성 | **이 고정 wheel에는 NVIDIA EULA가 동봉**. 최신 NVSHMEM 소스 저장소의 Apache-2.0 선언으로 배포 바이너리 조건을 대체하지 않음 |
| 오픈소스 | NVTX cu12 12.8.90, 13.2.86 | GPU 실행 추적·프로파일링 의존성 | 고정 wheel LICENSE: **Apache-2.0 WITH LLVM-exception**. metadata의 단순 Apache 표기만 옮기면 예외 조건이 누락됨 |
| 기타 | 로컬 Docker Desktop `desktop-linux` 컨텍스트 | 개발 컴퓨터 컨테이너 실행 환경 | [Docker 구독 서비스 계약](https://www.docker.com/legal/docker-subscription-service-agreement/). Docker Engine/Moby 및 Compose의 Apache-2.0과 구분. 설치 조직·규모에 따른 실제 구독 자격은 이 명세에서 판정하지 않음 |

NCCL·NVTX의 조건을 바이너리에서 확인했고, NVSHMEM도 실제 배포 형태를 별도로 확인했다. 이 결과는 9절의 해당 36개 행에도 반영했다. Qwen 두 모델은 위의 고정 revision을 조회했으며, Embedding 모델은 Apache-2.0을 선언한 카드가 근거이고 별도 LICENSE 파일이 존재한다고 기재하지 않았다.

## 12. 직접 구현한 API 전체 목록

다음은 봉화지기에서 직접 개발한 FastAPI HTTP 인터페이스다. 연동된 외부 서비스/모델/라이브러리의 조건은 앞 표를 따른다. [일반 서버 실행 OpenAPI](api/mvp-openapi.json)의 `0.2.0-mvp`에 있는 모든 동작을 열거했고 GPU API는 별도 4개 동작이다. 내부 API는 서비스 토큰, 앱 사용자 API는 사용자 JWT를 쓴다. 상태 확인 등 공개 경로의 정확한 인증 지정은 실행 OpenAPI를 따른다.

| 구분 | 명칭·경로 | 용도 | 구현 상태·라이선스 |
| --- | --- | --- | --- |
| 상태 확인 | `GET /health/live` | 프로세스 생존 확인 | 구현; 팀 작성 API, 공개 라이선스 미지정 |
| 상태 확인 | `GET /health/ready` | 서버 의존성 준비 상태 확인 | 구현; 팀 작성 API, 공개 라이선스 미지정 |
| 내부용 | `POST /internal/v1/scenario-events` | 시나리오 이벤트 수신·DB/outbox·큐 연결 | 구현; 팀 작성 API, 공개 라이선스 미지정 |
| 내부용 | `POST /internal/v1/retrieval-documents` | 검색용 문서 등록·임베딩 처리 요청 | 구현; 팀 작성 API, 공개 라이선스 미지정 |
| 내부용 | `GET /internal/v1/scenarios/{scenario_id}/analysis-jobs/{job_id}` | 분석 작업 상태·검색 결과 조회 | 구현; 팀 작성 API, 공개 라이선스 미지정 |
| 내부용 | `POST /internal/v1/scenarios/{scenario_id}/analysis-jobs/{job_id}/retry` | 실패한 분석 작업 재시도 | 구현; 팀 작성 API, 공개 라이선스 미지정 |
| 내부용 | `GET /internal/v1/analysis-health` | 분석 작업 운영 상태 조회 | 구현; 팀 작성 API, 공개 라이선스 미지정 |
| 내부용 | `PUT /internal/v1/policy/scenarios/{scenario_id}/clock` | 시나리오 기준 시각 갱신 | 구현; 팀 작성 API, 공개 라이선스 미지정 |
| 내부용 | `PUT /internal/v1/policy/scenarios/{scenario_id}/users/{user_id}/profile` | 시연 사용자 프로필 입력 | 구현; 팀 작성 API, 공개 라이선스 미지정 |
| 내부용 | `PUT /internal/v1/policy/scenarios/{scenario_id}/users/{user_id}/location` | 시연 사용자 위치 입력 | 구현; 팀 작성 API, 공개 라이선스 미지정 |
| 내부용 | `PUT /internal/v1/policy/scenarios/{scenario_id}/incidents/{incident_id}` | 사건 정보 등록·변경 | 구현; 팀 작성 API, 공개 라이선스 미지정 |
| 내부용 | `PUT /internal/v1/policy/scenarios/{scenario_id}/incidents/{incident_id}/prediction` | 모의 예측 입력 수신 계약 | 내부 모의 입력 계약·실제 예측 호출 없음; 팀 작성 API, 공개 라이선스 미지정 |
| 내부용 | `PUT /internal/v1/policy/scenarios/{scenario_id}/incidents/{incident_id}/alerts/{alert_id}` | 공식 경보 등록·정정·해제 입력 | 구현; 팀 작성 API, 공개 라이선스 미지정 |
| 내부용 | `GET /internal/v1/policy/scenarios/{scenario_id}/incidents/{incident_id}/alerts` | 사건의 공식 경보 또는 내 경보 목록 조회 | 구현; 팀 작성 API, 공개 라이선스 미지정 |
| 내부용 | `PUT /internal/v1/policy/scenarios/{scenario_id}/guidance/{guidance_id}` | 검토된 기본 행동지침 등록 | 구현; 팀 작성 API, 공개 라이선스 미지정 |
| 내부용 | `PUT /internal/v1/policy/scenarios/{scenario_id}/rules` | 개인 정책 규칙 등록·변경 | 구현; 팀 작성 API, 공개 라이선스 미지정 |
| 내부용 | `POST /internal/v1/policy/scenarios/{scenario_id}/bootstrap-policy` | 3단계 기본 규칙·지침 초기 등록 | 구현; 팀 작성 API, 공개 라이선스 미지정 |
| 내부용 | `PUT /internal/v1/policy/scenarios/{scenario_id}/incidents/{incident_id}/environment` | 사건 환경 상태 갱신 | 구현; 팀 작성 API, 공개 라이선스 미지정 |
| 내부용 | `PUT /internal/v1/policy/scenarios/{scenario_id}/incidents/{incident_id}/users/{user_id}/state` | 현재 사용자 상태 입력 | 구현; 팀 작성 API, 공개 라이선스 미지정 |
| 내부용 | `PUT /internal/v1/policy/scenarios/{scenario_id}/incidents/{incident_id}/users/{user_id}/route` | 경로 상태·제약 입력 또는 조회; 실제 경로 탐색 없음 | 시연 경로 상태 입력; 실제 탐색 미연결. 팀 작성 API, 공개 라이선스 미지정 |
| 내부용 | `GET /internal/v1/policy/scenarios/{scenario_id}/users/{user_id}/plans/{incident_id}` | 사용자의 현재 개인 대응 정책 조회 | 구현; 팀 작성 API, 공개 라이선스 미지정 |
| 내부용 | `GET /internal/v1/policy/scenarios/{scenario_id}/users/{user_id}/plans/{incident_id}/history` | 개인 정책 변경 이력 조회 | 구현; 팀 작성 API, 공개 라이선스 미지정 |
| 내부용 | `GET /internal/v1/policy/scenarios/{scenario_id}/integrations/{job_id}` | Qwen 통합 작업·결과 조회 | 구현; 팀 작성 API, 공개 라이선스 미지정 |
| 내부용 | `POST /internal/v1/policy/scenarios/{scenario_id}/integrations/{job_id}/retry` | Qwen 통합 실패 재시도 | 구현; 팀 작성 API, 공개 라이선스 미지정 |
| 앱용 | `GET /v1/app-config` | 앱 기능·단계·갱신 설정 조회 | 구현; 팀 작성 API, 공개 라이선스 미지정 |
| 앱용 | `GET /v1/me/profile` | 내 프로필 조회 | 구현; 팀 작성 API, 공개 라이선스 미지정 |
| 앱용 | `PUT /v1/me/profile` | 내 프로필 수정 | 구현; 팀 작성 API, 공개 라이선스 미지정 |
| 앱용 | `DELETE /v1/me/profile` | 내 프로필 삭제 | 구현; 팀 작성 API, 공개 라이선스 미지정 |
| 앱용 | `GET /v1/me/preferences` | 내 알림·사용 환경 설정 조회 | 구현; 팀 작성 API, 공개 라이선스 미지정 |
| 앱용 | `PUT /v1/me/preferences` | 내 설정 수정 | 구현; 팀 작성 API, 공개 라이선스 미지정 |
| 앱용 | `PUT /v1/me/devices/{installation_id}` | 내 단말·푸시 토큰 등록/갱신 | 구현; 팀 작성 API, 공개 라이선스 미지정 |
| 앱용 | `DELETE /v1/me/devices/{installation_id}` | 내 단말 등록 해제 | 구현; 팀 작성 API, 공개 라이선스 미지정 |
| 앱용 | `GET /v1/me/location` | 내 위치 조회 | 구현; 팀 작성 API, 공개 라이선스 미지정 |
| 앱용 | `PUT /v1/me/location` | 내 현재 위치 갱신 | 구현; 팀 작성 API, 공개 라이선스 미지정 |
| 앱용 | `DELETE /v1/me/location` | 내 위치 삭제 | 구현; 팀 작성 API, 공개 라이선스 미지정 |
| 앱용 | `GET /v1/me/alerts` | 사건의 공식 경보 또는 내 경보 목록 조회 | 구현; 팀 작성 API, 공개 라이선스 미지정 |
| 앱용 | `GET /v1/me/alerts/{alert_id}` | 내 공식 경보 상세 조회 | 구현; 팀 작성 API, 공개 라이선스 미지정 |
| 앱용 | `POST /v1/me/alerts/{alert_id}/receipts` | 경보 수신·열람·행동 확인 기록 | 구현; 팀 작성 API, 공개 라이선스 미지정 |
| 앱용 | `GET /v1/me/responses/{response_id}` | 내 개인 대응 안내 조회 | 구현; 팀 작성 API, 공개 라이선스 미지정 |
| 앱용 | `PUT /v1/me/responses/{response_id}/context` | 내 현재 상태·이동 제약 갱신 | 구현; 팀 작성 API, 공개 라이선스 미지정 |
| 앱용 | `GET /v1/me/responses/{response_id}/history` | 개인 정책 변경 이력 조회 | 구현; 팀 작성 API, 공개 라이선스 미지정 |
| 앱용 | `GET /v1/me/updates` | 커서 기준 변경 목록 조회 | 구현; 팀 작성 API, 공개 라이선스 미지정 |
| 앱용 | `GET /v1/disasters` | 재난·사건 목록 조회 | 구현; 팀 작성 API, 공개 라이선스 미지정 |
| 앱용 | `GET /v1/safety-rules/{disaster_type}` | 재난별 기본 행동지침 조회 | 구현; 팀 작성 API, 공개 라이선스 미지정 |
| 앱용 | `GET /v1/home` | 현재 위치·경보·개인 안내 홈 조회 | 구현; 팀 작성 API, 공개 라이선스 미지정 |
| 앱용 | `GET /v1/me/deliveries` | 내 알림 전달 상태 조회 | 구현; 팀 작성 API, 공개 라이선스 미지정 |
| 앱용 | `POST /v1/me/logout` | 현재 세션 로그아웃 | 구현; 팀 작성 API, 공개 라이선스 미지정 |
| 앱용 | `GET /v1/me/responses/{response_id}/route` | 경로 상태·제약 입력 또는 조회; 실제 경로 탐색 없음 | unavailable/null·경로 도형 없음; 팀 작성 API, 공개 라이선스 미지정 |
| 앱용 | `POST /v1/me/responses/{response_id}/support-drafts` | 신고 지원 초안 계약 | 비활성 503·단말 작성 영역; 팀 작성 API, 공개 라이선스 미지정 |
| 앱용 | `POST /v1/me/responses/{response_id}/voice-turns` | 음성 대화 시작 계약 | 비활성 503·서버 음성 제외; 팀 작성 API, 공개 라이선스 미지정 |
| 앱용 | `GET /v1/me/responses/{response_id}/voice-turns/{turn_id}` | 음성 대화 조회 계약 | 비활성 503·서버 음성 제외; 팀 작성 API, 공개 라이선스 미지정 |
| 앱용 | `DELETE /v1/me/responses/{response_id}/voice-turns/{turn_id}` | 음성 대화 삭제 계약 | 비활성 503·서버 음성 제외; 팀 작성 API, 공개 라이선스 미지정 |
| GPU 내부용 | `GET /health/live` | GPU 프로세스 상태 | 구현; 팀 작성 API + 모델 Apache-2.0 및 라이브러리별 조건 |
| GPU 내부용 | `GET /health/ready` | 실제 모델 준비 상태 | 구현; 팀 작성 API + 모델 Apache-2.0 및 라이브러리별 조건 |
| GPU 내부용 | `POST /internal/v1/generate` | 자체 호스팅 Qwen 생성 | 구현; 팀 작성 API + 모델 Apache-2.0 및 라이브러리별 조건 |
| GPU 내부용 | `POST /internal/v1/embeddings` | 자체 호스팅 Qwen 임베딩 | 구현; 팀 작성 API + 모델 Apache-2.0 및 라이브러리별 조건 |

예측·경로 도형·신고 초안·음성 경로가 목록에 있어도 해당 기능이 완성된 것은 아니다. 실제 예측은 unavailable/null이며, 경로는 unavailable/null, 신고 초안과 서버 음성은 비활성 응답이다. 실제 푸시는 simulation이다. 앱 저장소의 화면 연결은 이 문서의 검증 대상이 아니다.


## 13. 원본 코드·설정에서 확인한 출처 URL

아래는 API·학습 자료·사건 선정·기하 검증에 사용하거나 인계 사양으로 기록한 경로다. 동적 URL의 실제 파일명 전체나 인증 파라미터는 넣지 않는다. `example.invalid`·loopback·XML namespace는 실제 외부 자원에서 제외했다. URL이 존재한다는 사실과 자료를 실제 확보·학습에 사용했다는 사실은 다르며, 역할과 이용조건은 본문의 상태 구분을 따른다.

| 구분 | 명칭·원문 URL | 사용·기록 위치 | 라이선스·이용조건 |
| --- | --- | --- | --- |
| 기상청 | [원문](https://apihub.kma.go.kr/api/typ05/api/GK2A/LE2/FF/KO/data) | `training/src/bonghwa_training/kma_download.py` | API허브·기관 조건/공공누리 제품별 확인 |
| 기상청 | [원문](https://apihub.kma.go.kr/api/typ05/api/GK2A/LE2/FF/KO/data?date=202610311240) | `training/reports/kma-audit-20261031/live-metadata/probe-20261031T1240.json` 외 3곳 | API허브·기관 조건/공공누리 제품별 확인 |
| 기상청 | [원문](https://apihub.kma.go.kr/api/typ05/api/GK2A/LE2/FF/KO/data?date=202610311340) | `training/reports/kma-audit-20261031/live-metadata/probe-20261031T1340.json` 외 1곳 | API허브·기관 조건/공공누리 제품별 확인 |
| 기상청 | [원문](https://apihub.kma.go.kr/apiList.do?seqApi=2&seqApiSub=239) | `training/sources/source-audit.json` | API허브·기관 조건/공공누리 제품별 확인 |
| 기상청 | [원문](https://apihub.kma.go.kr/apiList.do?seqApi=6&seqApiSub=271) | `training/sources/source-audit.json` | API허브·기관 조건/공공누리 제품별 확인 |
| 미국 사건 근거 | [원문](https://fire.ak.blm.gov/content/aicc/team_left/03.%20Alaska%20CIMT%20Incident%20Archive/Alaska%20IMT%20Incident%20Summaries/2021%20Summaries/2021%2007-23%20to%2008-06%20Bootleg.pdf) | `training/configs/goes-hourly-v1.json` 외 4곳 | 정부기관 게시물·첨부자료별 권리, 사건 선정 참고 |
| NASA | [원문](https://firms.modaps.eosdis.nasa.gov/content/academy/data_api/firms_api_use.html) | `training/sources/source-audit.json` | 제품별 공개 데이터 이용·인용 조건 |
| NASA | [원문](https://firms.modaps.eosdis.nasa.gov/data/active_fire/SUOMI_VIIRS_C2_Global_7d.csv) | `training/sources/source-audit.json` | 제품별 공개 데이터 이용·인용 조건 |
| NASA | [원문](https://firms.modaps.eosdis.nasa.gov/data/country) | `training/src/bonghwa_training/korea_download.py` | 제품별 공개 데이터 이용·인용 조건 |
| 국내 기관·공식 자료 | [원문](https://fmc.forest.go.kr/fmc/showTwbbsContDetail.do?bbrssId=BBRSS_0003&twbbsNo=91003737) | `training/configs/korea-gk2a-hourly-v4.json` | 개별 게시물·첨부물의 권리/공공누리 확인 |
| 국내 기관·공식 자료 | [원문](https://fmc.forest.go.kr/fmc/showTwbbsContDetail.do?bbrssId=BBRSS_0003&twbbsNo=91003815) | `training/configs/korea-gk2a-hourly-v4.json` | 개별 게시물·첨부물의 권리/공공누리 확인 |
| 국내 기관·공식 자료 | [원문](https://fmc.forest.go.kr/fmc/showTwbbsContDetail.do?bbrssId=BBRSS_0003&twbbsNo=91004062) | `training/configs/korea-gk2a-hourly-v4.json` | 개별 게시물·첨부물의 권리/공공누리 확인 |
| 국내 기관·공식 자료 | [원문](https://forest.go.kr/kfs/images/data/down/sb_3_09.pdf) | `training/configs/korea-gk2a-context-v2.json` 외 22곳 | 개별 게시물·첨부물의 권리/공공누리 확인 |
| 공개 배포 | [원문](https://github.com/wmgeolab/geoBoundaries/raw/9469f09/) | `training/src/bonghwa_training/korea_download.py` | 대상 자료별 조건, 국가 경계는 위 데이터 표 참고 |
| 뉴스 | [원문](https://news.google.com/rss/articles/CBMiVkFVX3lxTFBFa2p1clJ1b3RsOFNWRF9QSEVoY003OEppNjJmMXJOSmh1alhJWFJCemt5THFVdnpHeG4xa1VYN1FSaGN2OWhlNTNjaHMxYVh1d1YxRWh3?oc=5) | `docs/V2/delivery/qwen-integration/pre-inference.json` 외 1곳 | Google 약관 및 기사/언론사 저작권 |
| 뉴스 | [원문](https://news.google.com/rss/articles/CBMiW0FVX3lxTE5HWm9MU0FEQ180WFZvcUMzX3ZpSHoyTy1tWDZtQ2JyVlpqSFgweHlFb0lPajA1Q3hmb21BQUJ6aFpjMVVETWw0SHAxX0dYWGMtNzBqSVNndll1WDjSAWBBVV95cUxOTFp4M3RxSGZidFczX092cHo2X3ltRW8xYW1PZ3dQbVE3NDJCSnU2dlA4NTQtTlQ0dmNxWkFxUldVQnV6azUxY3VBZFFSMFQ0V3hSc0k3R3NiTG9tVklFYlE?oc=5) | `docs/V2/delivery/qwen-integration/pre-inference.json` 외 1곳 | Google 약관 및 기사/언론사 저작권 |
| 뉴스 | [원문](https://news.google.com/rss/articles/CBMiZ0FVX3lxTE5QeWY1WDM4OHVBaVkxM3ljNUVOdU5JcWNhQXVSTlFWV05Oby1sdnFtSHRCd1hrcEg2cUszYkYzX0VGdVhuV2lDMW9BbDdCOUFmNzduV0R3ckJ5MnFxaUkzNDk3UFFuY2M?oc=5) | `docs/V2/delivery/qwen-integration/pre-inference.json` 외 1곳 | Google 약관 및 기사/언론사 저작권 |
| 뉴스 | [원문](https://news.google.com/rss/search) | `src/bonghwajigi/retrieval/web_search.py` | Google 약관 및 기사/언론사 저작권 |
| 기상청 | [원문](https://nmsc.kma.go.kr/upload/resource/data/gk2a/gk2a_ami_ko020lc_latlon.nc) | `training/reports/kma-audit-20261031/projection-audit.json` | API허브·기관 조건/공공누리 제품별 확인 |
| NOAA | [원문](https://noaa-isd-pds.s3.amazonaws.com) | `training/src/bonghwa_training/korea_download.py` | NOAA 공공정보 조건·출처 |
| FCM 준비 | [원문](https://oauth2.googleapis.com/token) | `src/bonghwajigi/notifications/providers.py` | Google/Firebase 서비스 조건 |
| 데이터 카탈로그 | [원문](https://planetarycomputer.microsoft.com/api/stac/v1) | `training/src/bonghwa_training/korea_download.py` | 플랫폼 및 원 데이터별 이용조건 |
| 국내 기관·공식 자료 | [원문](https://www.data.go.kr/data/15057210/openapi.do) | `training/sources/source-audit.json` | 개별 게시물·첨부물의 권리/공공누리 확인 |
| 국내 기관·공식 자료 | [원문](https://www.data.go.kr/data/15121380/fileData.do) | `training/sources/source-audit.json` | 개별 게시물·첨부물의 권리/공공누리 확인 |
| 국내 기관·공식 자료 | [원문](https://www.data.go.kr/data/3070842/openapi.do) | `training/sources/source-audit.json` | 개별 게시물·첨부물의 권리/공공누리 확인 |
| 미국 사건 근거 | [원문](https://www.fire.ca.gov/incidents/2021/7/13/dixie-fire) | `training/configs/goes-hourly-v1.json` 외 4곳 | 정부기관 게시물·첨부자료별 권리, 사건 선정 참고 |
| 미국 사건 근거 | [원문](https://www.fire.ca.gov/incidents/2021/8/14/caldor-fire) | `training/configs/goes-hourly-v1.json` 외 4곳 | 정부기관 게시물·첨부자료별 권리, 사건 선정 참고 |
| 미국 사건 근거 | [원문](https://www.fire.ca.gov/incidents/2022/7/22/oak-fire) | `training/configs/goes-hourly-v1.json` 외 4곳 | 정부기관 게시물·첨부자료별 권리, 사건 선정 참고 |
| 미국 사건 근거 | [원문](https://www.fire.ca.gov/incidents/2022/9/6/mosquito-fire) | `training/configs/goes-hourly-v1.json` 외 4곳 | 정부기관 게시물·첨부자료별 권리, 사건 선정 참고 |
| 미국 사건 근거 | [원문](https://www.fire.ca.gov/incidents/2023/8/15/smith-river-complex) | `training/configs/goes-hourly-v1.json` 외 4곳 | 정부기관 게시물·첨부자료별 권리, 사건 선정 참고 |
| 국내 기관·공식 자료 | [원문](https://www.forest.go.kr/kfsweb/cop/bbs/selectBoardArticle.do?bbsId=BBSMSTR_1009&nttId=3180876) | `training/configs/korea-gk2a-hourly-v4.json` | 개별 게시물·첨부물의 권리/공공누리 확인 |
| 국내 기관·공식 자료 | [원문](https://www.forest.go.kr/kfsweb/cop/bbs/selectBoardArticle.do?bbsId=BBSMSTR_1036&nttId=3181783&mn=NKFS_04_02_01) | `training/configs/korea-gk2a-hourly-v4.json` | 개별 게시물·첨부물의 권리/공공누리 확인 |
| 국내 기관·공식 자료 | [원문](https://www.hccl.go.kr/CLRecords/Files/FileAppendix/a9/A006406.pdf) | `training/configs/korea-gk2a-context-v2.json` 외 18곳 | 개별 게시물·첨부물의 권리/공공누리 확인 |
| 뉴스 | [원문](https://www.joongang.co.kr/) | `docs/V2/delivery/qwen-integration/pre-inference.json` 외 1곳 | Google 약관 및 기사/언론사 저작권 |
| Kaggle/NDWS | [원문](https://www.kaggle.com/api/v1/datasets) | `training/src/bonghwa_training/download.py` | 자료 CC BY 4.0, 플랫폼 조건 별도 |
| Kaggle/NDWS | [원문](https://www.kaggle.com/api/v1/datasets/download/fantineh/next-day-wildfire-spread/next_day_wildfire_spread_eval_00.tfrecord?datasetVersionNumber=2) | `training/reports/dataset-report.json` 외 3곳 | 자료 CC BY 4.0, 플랫폼 조건 별도 |
| Kaggle/NDWS | [원문](https://www.kaggle.com/api/v1/datasets/download/fantineh/next-day-wildfire-spread/next_day_wildfire_spread_test_00.tfrecord?datasetVersionNumber=2) | `training/reports/dataset-report.json` 외 3곳 | 자료 CC BY 4.0, 플랫폼 조건 별도 |
| Kaggle/NDWS | [원문](https://www.kaggle.com/api/v1/datasets/download/fantineh/next-day-wildfire-spread/next_day_wildfire_spread_train_00.tfrecord?datasetVersionNumber=2) | `training/reports/dataset-report.json` 외 3곳 | 자료 CC BY 4.0, 플랫폼 조건 별도 |
| Kaggle/NDWS | [원문](https://www.kaggle.com/datasets/fantineh/next-day-wildfire-spread) | `training/reports/dataset-report.json` 외 4곳 | 자료 CC BY 4.0, 플랫폼 조건 별도 |
| 국내 기관·공식 자료 | [원문](https://www.korea.kr/) | `data/scenarios/yeongdeok-integration.json` 외 3곳 | 개별 게시물·첨부물의 권리/공공누리 확인 |
| 국내 기관·공식 자료 | [원문](https://www.korea.kr/briefing/policyBriefingView.do?newsId=156393191) | `training/configs/korea-gk2a-context-v2.json` 외 18곳 | 개별 게시물·첨부물의 권리/공공누리 확인 |
| 국내 기관·공식 자료 | [원문](https://www.korea.kr/news/policyNewsView.do?newsId=148940993) | `data/scenarios/yeongdeok-integration.json` 외 4곳 | 텍스트 한정 공공누리 제1유형; 이미지·영상 등 별도 권리 |
| 국내 기관·공식 자료 | [원문](https://www.mois.go.kr/frt/bbs/type010/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000008&nttId=99891) | `training/configs/korea-gk2a-context-v2.json` 외 18곳 | 개별 게시물·첨부물의 권리/공공누리 확인 |
| 국내 기관·공식 자료 | [원문](https://www.opm.go.kr/opm/news/press-release.do?articleNo=153083&mode=view) | `training/configs/korea-gk2a-context-v2.json` 외 18곳 | 개별 게시물·첨부물의 권리/공공누리 확인 |
| 국내 기관·공식 자료 | [원문](https://www.safekorea.go.kr/safekorea-kor/acts/nacts/action-guide.do?category=forestFires&menuSn=4) | `src/bonghwajigi/policy/three_stage.py` | 개별 게시물·첨부물의 권리/공공누리 확인 |
| 국내 기관·공식 자료 | [원문](https://www.safetv.go.kr/) | `data/scenarios/yeongdeok-integration.json` 외 3곳 | 개별 게시물·첨부물의 권리/공공누리 확인 |
| 국내 기관·공식 자료 | [원문](https://www.safetv.go.kr/base/video/view?idx=2759&menuLevel=&menuNo=&playlistManagementIdx=8) | `data/scenarios/yeongdeok-integration.json` 외 4곳 | 공공누리 제4유형: 출처표시·상업적이용금지·변경금지 |
| 국내 기관·공식 자료 | [원문](https://www.safetydata.go.kr/V2/api/DSSP-IF-00247) | `training/sources/source-audit.json` | 개별 게시물·첨부물의 권리/공공누리 확인 |
| 국내 기관·공식 자료 | [원문](https://www.safetydata.go.kr/disaster-data/view?dataSn=228) | `training/sources/source-audit.json` | 개별 게시물·첨부물의 권리/공공누리 확인 |
| 뉴스 | [원문](https://www.yna.co.kr/) | `docs/V2/delivery/qwen-integration/pre-inference.json` 외 1곳 | Google 약관 및 기사/언론사 저작권 |
| 뉴스 | [원문](https://www.yonhapnewstv.co.kr/) | `docs/V2/delivery/qwen-integration/pre-inference.json` 외 1곳 | Google 약관 및 기사/언론사 저작권 |
| 동적 API·배포 경로 | `https://fcm.googleapis.com/v1/projects/{project}/messages:send` | `src/bonghwajigi/notifications/providers.py` | 본문 API 표의 상태·조건 적용 |
| 동적 API·배포 경로 | `https://{bucket}.s3.amazonaws.com/{key}` | `training/src/bonghwa_training/goes_download.py` | 본문 API 표의 상태·조건 적용 |
| 동적 API·배포 경로 | `https://github.com/wmgeolab/geoBoundaries/raw/9469f09/releaseData/gbOpen/KOR/ADM0/geoBoundaries-KOR-ADM0.geojson` | `training/src/bonghwa_training/korea_download.py` | 본문 API 표의 상태·조건 적용 |

추가 검사 범위는 원본 URL 51개와 동적 경로 3개, 일반 서버 52개·GPU 4개 HTTP 동작, CUDA/NVIDIA 36개 패키지·버전이다. API의 동작 수는 메서드와 경로 조합으로 세었으며 동일 경로의 GET/PUT/DELETE를 각각 구분했다. [기존 전체 출처 JSON](external-resources/data-and-content-sources.json)과 [보충 검증 JSON](external-resources/supplemental-verification-20261101.json)을 함께 제공한다. 저장소에 새 자료가 들어오면 해당 자료의 출처·실제 사용 여부·조건을 갱신해야 한다.

## Android 네이버 지도 연결 자원 — 2026-11-01

사용자가 승인한 Android 실지도 연결의 추가 조사다. 앱의 지도 소스·고정 npm 패키지·Gradle이 받은 AAR를 대조했다. SDK 초기화 콜백은 타일 로딩 또는 인증 성공의 증거로 취급하지 않는다. 최종 단말 확인과 APK 출처는 [지도 연결 검증](../../../apps/mobile/docs/11-naver-map-integration.md)과 [메인 배포 기록](mobile-submodule-deployment.md)에 남긴다.

| 구분 | 명칭 | 용도 | 라이선스 |
| --- | --- | --- | --- |
| 오픈소스 | `@mj-studio/react-native-naver-map` 2.9.1 | React Native 화면과 Android 네이버 지도 SDK 연결, 위치 마커·정확도 원·서버 사건 영역 표시 | 설치 패키지 `LICENSE`의 **MIT**, Copyright (c) 2024 MJ Studio. 저작권·허가 고지 유지. [공급자 저장소](https://github.com/mym0404/react-native-naver-map). 이 MIT는 래퍼 코드에 적용되며 네이버 SDK·지도 데이터 이용권과 구분 |
| 기타 | NAVER Maps Android SDK `com.naver.maps:map-sdk:3.23.2` | Android 네이티브 지도 렌더링과 SDK가 수행하는 지도 요청. 2D 화면에서 사용 | [공식 Maven AAR](https://repository.map.naver.com/archive/maven/com/naver/maps/map-sdk/3.23.2/map-sdk-3.23.2.aar)의 `assets/navermap-sdk/LICENSE`: **NAVER Corp., All rights reserved.** SDK 자체 고지와 동봉 `NOTICE`의 구성요소별 조건을 유지. 데모 저장소의 Apache-2.0 또는 래퍼 MIT를 SDK 전체 라이선스로 표시하지 않음 |
| 외부 API | NAVER Cloud Platform Maps · Dynamic Map (Android Mobile Dynamic Map) | 등록된 Android 앱의 배경 지도 표시. 앱은 발급된 Key ID를 SDK에 전달하며 서버가 지도 API를 대행하지 않음 | **상용 서비스 이용약관** — [공식 Maps 서비스 이용약관](https://xv-ncloud.pstatic.net/images/provision/%5B%EB%AF%BC%EA%B0%84%5DMaps%EC%84%9C%EB%B9%84%EC%8A%A4%EC%9D%B4%EC%9A%A9%EC%95%BD%EA%B4%80_v0.4_%28CLEAN%29_1742433558704.pdf), [공식 Android 시작 가이드](https://navermaps.github.io/android-map-sdk/guide-ko/1.html). 무료 이용량 여부와 별개로 약관·등록 앱 범위·표시 조건 적용. API 결과의 별도 DB화·재배포 허가를 뜻하지 않음 |

지도 로고와 기본 법적 공지 접근을 유지한다. SDK 내부 `NOTICE`에 포함된 Mapbox/MapLibre·Boost·ICU 등 제3자 고지는 SDK의 소유권 표기와 별개다. 앱이 Maps 결과를 수집해 별도 지도 DB를 구축하거나 타일을 재호스팅하지 않는다. 사건 사각형과 사용자 위치는 앱의 기존 서버 입력이며 네이버가 산불 확산·대피로를 판정한 결과가 아니다. Directions·Geocoding·Reverse Geocoding·Static Map·Web Dynamic Map API는 이번 연결에서 사용하지 않는다.

설치 패키지의 `LICENSE` SHA256은 `52fd4ae7199af5b0b348fc3b870a3e0f7d2070e159923e3baec969677fb539e3`이다. 실제 SDK 3.23.2 AAR SHA256은 `ab7452952c2da1aa111ebf57a8accfe9a4beaa3fa63a3217ada2d606ea2a03f7`, 그 안의 `assets/navermap-sdk/LICENSE`는 `e0cb568489be575b91b39762d071060101609f129c0d4e02a74f019e96839263`, `assets/navermap-sdk/NOTICE`는 `16b6c4e325f85b78eb7f49917c6507fd3627b2b5176bf999b29582889164967a`다. 기존 서버/Python 의존성 전수 검증 JSON은 이 Android 배포물까지 검사한 것으로 해석하지 않는다.

새 Maps의 Key ID는 래퍼 2.9.1 Expo plugin의 `client_id` 옵션으로 주입한다. plugin은 Android `com.naver.maps.map.NCP_KEY_ID`를 설정한다. 실제 값은 문서·Git에 기록하지 않으며 Client Secret은 이 네이티브 지도 연결에 사용하지 않는다. 앱 등록 방법은 [공식 Application 가이드](https://guide.ncloud-docs.com/docs/application-maps-app-vpc)를 따른다.
