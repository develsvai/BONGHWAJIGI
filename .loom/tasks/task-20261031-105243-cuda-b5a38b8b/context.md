# Context

## Loom 코드 계약

아래 항목은 Loom 코드에 고정된 runtime 동작 계약입니다. 관련 흐름을 바꾸기 전 `loom contract show <id>`로 확인합니다.

- `task-execution`: Task 실행 전 prompt/context/previous-results에 들어가는 입력 경계입니다. 명령: `loom contract show task-execution`. Source: `loom/application/context_pack.py`, `loom/application/team_policy.py`
- `done-guardrail`: Task를 DONE으로 인정하기 전에 필요한 산출물과 상태 전이를 검증하는 계약입니다. 명령: `loom contract show done-guardrail`. Source: `loom/application/services.py`

## Project Memory

# 프로젝트 분석: BONGHWAJIGI

## 루트

`/Users/hongyongjae/Desktop/helloworld/BONGHWAJIGI`

## 요약

- 주요 스택: 확인 필요
- 패키지 / 런타임 파일: -
- 테스트 진입점: -
- 앱 진입점: docs/

## 최상위 구조

- ./
  - .gitignore
  - AGENTS.md
  - CLAUDE.md
  - README.md
-   docs/
    - README.md
    - ai-and-infrastructure.md
    - architecture-and-data-flow.md
    - decisions-and-meeting-review.md
    - product-and-scenarios.md
    - ui-ux-handoff.md

## 레포 규칙

- 기존 프로젝트 스타일과 로컬 helper API를 우선합니다.
- 수정 전에 관련 파일을 먼저 확인합니다.
- 변경 범위는 현재 Loom Task 계약 안에 유지합니다.
- 사용자 변경분을 버리는 destructive git reset/checkout을 사용하지 않습니다.
- 넓은 리팩터링이나 cross-domain 변경이 필요하면 먼저 boundary warning을 기록합니다.

## 실행 힌트

- 설치 / 런타임: -
- 테스트 / 검증: -
- 개발 서버: -

## 위험 영역

- 주의가 필요한 경로:
  - `No obvious sensitive path detected`

## Loom Task 가이드

- 좋은 Task는 예상 산출물, 완료 조건, 작업 범위, 검증 힌트를 가져야 합니다.
- repo 맥락이 약하면 architecture docs를 보강한 뒤 `loom analyze-repo`를 다시 실행합니다.
- agent 실행 전 `loom task validate <task-id>`로 경계를 확인합니다.
- 중단 이후에는 `loom resume`으로 현재 workflow 상태를 복구합니다.

## 보완할 맥락

- 아키텍처 ownership boundary는 수동 note가 필요할 수 있습니다.
- 배포, credential, 외부 서비스 정책은 자동으로 추론하지 않습니다.
- 프로젝트별 규칙은 Job note 또는 context reference에 추가합니다.

## Workspace Policy

- Output language: `ko`
- Agent provider: `claude`
- Agent model: `adapter-default`
- Reasoning effort: `high`
- Required branch: `develop`
- Dirty branch switch: `blocked`
- Commit policy: `manual`
- Include `.loom` metadata in Git: `yes`
- Read-only parallel execution: `allowed`
- Validation environment: `auto`
- Previous Task result limit: `2`
- Workspace required docs: -
- Loom fixed guardrails and verified Team required policies take precedence over this Workspace Policy.

## Job

- Title: 영향 확률 데이터셋과 모델
- Goal: 산불 영향의 입력·목표 격자·기간·관측 정답을 먼저 고정하고 GPU XGBoost 설치·학습·결과 확인과 일반 서버 CPU 연결을 준비한다. 실제 정답이 없으면 합성 연결검증과 실제 예측 보류를 명시하고 실제 성능을 주장하지 않는다. 이 갱신은 사용자 지시에 따른 계약 재고정이며 구현 실행·Queue 등록은 포함하지 않는다. 기존 완료 이력과 Task ID를 보존한다.
- Branch: HeoNey
- Task count: `8`

## Task

- Title: 사용자가 실행한 CUDA 학습 산출물과 독립 재추론 검증
- Description: 사용자가 제공한 완료 로그와 GPU 화면을 바탕으로 실제 서버의 고정 모델·보고서·학습 이력·데이터 해시를 확인한다. 모델을 새로 학습하지 않고 CPU 재로딩으로 validation 점수를 재계산하고, 고정한 모델에 대해 첫 holdout test 평가를 기록한다. Qwen 복구 상태를 확인한다.
- Expected output: 고정 모델 SHA256과 실제 산출물 사본, 재현 가능한 재추론 검증 코드, validation 일치 및 첫 test 평가 보고서, 서비스 상태 근거와 해석 문서
- Done condition: 모델 무결성·트리 수·최적 회차·학습 이력·데이터 계약을 검증하고 재추론 validation 지표가 보고서와 일치하는지 검사한다. 고정 모델의 test 결과와 단순 기준선·진단 임계값 성능을 분리해 기록하고 운영 사용 가능 여부 및 남은 한계를 설명한다.
- In scope: training 전용 검증 도구·작은 산출물과 문서, 서버 읽기 전용 상태 조회·CPU 재추론, 원본 모델을 변경하지 않는 검증 보고서, Loom 기록
- Out of scope: 재학습·튜닝·운영 배포·대응 레벨 결정·GPU 서비스 중단·다른 작업자 파일·앱·원격 push
- Validation hint: 모델·데이터 SHA256, 피처 순서·0/1 정답·64회 이력/최적 회차·CPU 재로딩, validation 지표 재계산 일치, test 미사용 상태에서 고정한 모델의 첫 평가, Qwen ready, Loom strict
- Required docs: `docs/V2/delivery/xgboost-training-data.md`, `docs/V2/delivery/xgboost-training-run.md`
- Memory refs: -
- Document outputs: `docs/V2/delivery/xgboost-training-verification.md`
- Document output exceptions: -
- Source proposal: `-`
- Status: PENDING
- Assigned agent: foreground

## Advisor Source Prompt

No Advisor source prompt recorded for this Task.

## Inclusion Policy

- Mandatory execution files: `prompt.md`, `context.md`, and `previous-results.md`.
- Always included: project memory, current Job/Task metadata, and Job notes.
- Previous results: up to the latest 2 recorded results from earlier Tasks in this Job.
- Job context refs: explicit Job-scoped references selected by the controlling agent or user.
- Task required docs: mandatory Task-scoped documents; missing refs block validation and execution.
- Task memory refs: mandatory Task-scoped workflow memory references; missing or non-memory refs block validation and execution.
- Repository documents, validation documents, and skill rules: included only through explicit Job context refs, Task required docs, or Task memory refs.
- Verified Team Policy Snapshot: included before Active Memory; required policy cannot be overridden by lower-priority context.
- Active workflow memory with an `always` category is included automatically while its status is `ACTIVE`.
- `task_selected` and `reference_only` memory is included only through explicit Task memory refs.
- Consumed proposals, rejected proposals, resolved memory, superseded memory, and archived memory are excluded.
- Unreferenced repository files and results from other Jobs are not included.
- `AGENTS.md` and `CLAUDE.md` remain session-level controlling-agent entrypoints and are not treated as task context artifacts by default.

## Job Notes

# Notes

## 2026-10-31T00:26:26+00:00

설계 기준은 docs/V2이며 HeoNey는 참고다. 앱 구현은 제외하고 앱팀에 API 명세를 제공한다. 이 등록은 작업 계약 고정이며 후속 구현 Task를 지금 실행하거나 Queue에 넣지 않는다. 기준 원문은 docs/V2/01, 02, 03 문서이고 실행 작업표는 docs/V2/04-execution-backlog.md이다. 등록 시 의존관계는 Job 경계를 넘어 적용한다.
- Tags: `v2`, `scope`, `backlog`
## 2026-10-31T01:30:15+00:00

검증 전부 실행 지시를 확인했다. 계약 형식 검증은 통과했지만 실제 검증에 필요한 선행 작업 C3의 산출물이 아직 없어 기능 검증은 실행할 수 없다. 모델 또는 API가 완성된 것으로 간주하지 않고 PENDING 유지하며 선행 구현 완료 후 이 Task를 실행한다. 현황은 A2 환경 검증 보고서에 함께 정리한다.

- Task: `task-20261031-002629-task-2b63fdb8`
- Tags: `validation`, `prerequisites`
## 2026-10-31T08:01:46+00:00

# 2026-10-31-wildfire-mvp 작업 계약 재고정

사용자 지시: “오케 우선은 그거대로 loom에 타스크를 재고정 해”.

2026-10-31 KST 사용자 재고정: 오늘 MVP는 산불 한 종류이며 3D와 서버 STT/TTS·오디오 스트리밍을 제외하고 서버는 텍스트를 제공한다. 공식 경보는 출처·원문·발령 대상을 확인해 개인별 정책 계산과 GPU를 기다리지 않고 우선 전달한다. 일반 분석은 정형 파싱 또는 필요한 Qwen 문서 추출·저장 문서의 임베딩 검색, 사건 통합·위치 관련성·입력 검사, 영향 확률 또는 예측 불가, 검토된 개인별 정책 순서다. 공식 등급·환경 영향 확률·개인 대응 단계를 분리하고 정책은 검토·버전 관리하며 입력 변경 때 재적용한다. 실제 자료·과거 재생·합성 시나리오를 구분하고 실제 정답이 없으면 학습·추론 연결은 simulation으로 검증하며 실제 예측은 unavailable로 둔다. 이 지시는 작업 계약 재고정만 승인하며 구현 실행·Queue 등록·서버 설치·원격 push를 지금 승인한 것으로 취급하지 않는다. 오늘 범위는 이 계약과 Job 재고정 노트를 우선하고 기존 V2 문서는 배경 설계로 참조한다.

이 갱신은 재고정만 수행하며 Task 실행 또는 Queue 등록을 시작하지 않는다.

미정: 시연 지역·사례, 모델의 실제 정답 출처·격자·예측 기간, 개인 대응 단계 매핑, 2D 실제 경로 계산 채택 여부. 60분은 예시이며 실제 확정값이 아니다. 실제 정답 부족은 C4에서 실제 예측 보류로 판정한다.

착수 순서: A1 → B1 → B2 및 C1 → A3·D1·D6 → 수집/긴급 전달·개인 정책·모델 준비 → 안내 갱신 → E2·A4 통합 검증. 공식 원문 전달 D4는 개인 정책 D1/D2와 모델 준비를 선행 조건으로 삼지 않는다.

- C1 `task-20261031-002627-task-cc78619e`: 산불 영향 확률의 입력·목표 격자·예측 기간·관측 정답 및 시연 경계 고정. 선행: A1, B1. 현재 PENDING.
- C2 `task-20261031-002628-task-71b2ed3b`: 산불 학습·평가 데이터와 명시적인 합성 연결검증 데이터 준비. 선행: B2, C1. 현재 PENDING.
- C3 `task-20261031-002629-xgboost-c44c6d79`: GPU 서버에 XGBoost 설치 후 기준선·학습·추론 연결 검증. 선행: A2, A3, C2. 현재 PENDING.
- C4 `task-20261031-002629-task-2b63fdb8`: 산불 모델의 독립 평가·확률 보정 또는 실제 예측 보류 판정. 선행: C3. 현재 PENDING.
- C5 `task-20261031-002629-cpu-0d28f70c`: 일반 서버의 XGBoost CPU 추론과 예측 불가·모의 모드 및 모델 복구 구현. 선행: A3, C4. 현재 PENDING.

구체적 완료 조건은 각 Task의 재고정 계약을 따른다. 기존 docs/V2/04-execution-backlog.md는 이전 계획이며 실제 계약 정본은 현재 Task와 이 노트다.
- Tags: `mvp`, `산불`, `2026-10-31`, `계약재고정`
## 2026-10-31T08:33:37+00:00

2026-10-31 구현 기술 스택 결정: docs/V2/delivery/implementation-stack.md; Task task-20261031-082929-mvp-3188b68a. Python 3.12 + FastAPI/Pydantic 2 + SQLAlchemy 2.x/psycopg 3/Alembic + PostgreSQL 16/PostGIS/pgvector + Celery/Redis + Transformers/Sentence Transformers + XGBoost. 일반 서버 API/정책/CPU 추론, GPU 서버 모델/별도 학습, K8s 수집으로 배치한다. XGBoost GPU 학습과 일반 서버 CPU Predictor를 분리하고 실제 정답·기간·평가/보류를 C1~C4에서 고정한다. 스택 선정은 실제 예측 성능 검증이 아니다. 이번 실행은 스택 문서와 계약 연결만 수행하며 다른 구현 Task·Queue·서버 설치는 시작하지 않는다.
- Tags: `기술스택`, `산불`, `MVP`
## 2026-10-31T10:13:51+00:00

사용자는 국외 공개 데이터도 활용하도록 명시했다. XGBoost 데이터 작업은 training/ 및 xgboost-training-data 문서에 격리한다. 다른 작업자의 분석 큐·검색 파일과 GPU 서빙은 변경하지 않는다. 국내 인계 자료는 출처·연결 검증 표본이고 시간별 확산 정답이 부족하여 NDWS v2의 다음 날 1km 위성 화재 관측을 첫 연구용 목표로 사용한다. 개인 영향·60분 도달·대응 레벨과 동일시하지 않는다.

- Task: `task-20261031-100122-xgboost-1f6a6032`
- Tags: `dataset`, `xgboost`, `scope`
## 2026-10-31T10:20:24+00:00

NDWS v2 원본 3개(639,939,000바이트) 확보, 중복 46패치 제거와 unknown/QC 처리 후 11,753,527행의 train/validation/test 학습 테이블을 구축했다. 독립 원본 재생성에서 Parquet SHA256과 보고서가 일치했고 실제 XGBoost DMatrix 각 65,536행·20열 검증 및 11개 테스트를 통과했다. 모델 학습은 아직 수행하지 않았다. 자료와 한계·국내 수집 경로는 docs/V2/delivery/xgboost-training-data.md와 training/에 보존한다.

- Task: `task-20261031-100122-xgboost-1f6a6032`
- Tags: `dataset`, `result`, `validation`
## 2026-10-31T10:36:35+00:00

학습 시작 방법 질문에 맞춰 training 전용 실자료 실행기와 GPU 시작 스크립트를 준비한다. GPU 서빙 잠금을 존중하고 Qwen 중단·전체 CUDA 학습은 자동 실행하지 않는다. CPU 131,072행/분할 사전 학습에서 조기 종료·4개 트리 저장·CPU 재로딩 차이 0을 확인했으며 test 평가는 하지 않았다. 전체 학습 결과로 주장하지 않는다.

- Task: `task-20261031-102643-xgboost-gpu-63a490e2`
- Tags: `training`, `preflight`, `scope`

## Context References

No explicit context references recorded for this job.

## Required Documents and Memory

### required-doc: docs/V2/delivery/xgboost-training-data.md

- Path: `docs/V2/delivery/xgboost-training-data.md`
- Status: present

# XGBoost 학습 데이터 확보와 첫 데이터셋

2026-10-31. Loom Task `task-20261031-100122-xgboost-1f6a6032`. 사용자는 국외 공개 데이터 활용을 허용했고, 분석 큐·검색 구현은 다른 작업자가 이어간다. 이 작업은 `training/`에 격리했다.

## 입력에 대한 판단

사용자가 제시한 자료는 서비스 전체에 필요하다. 다만 산불 환경 예측과 개인별 대응 매뉴얼 생성은 입력·정답이 다르다.

| 자료 | 활용 위치와 추가 조건 |
| --- | --- |
| 사용자 프로필 | 이동 제약, 연령, 호흡기 취약성, 동반자 등 개인별 대응 원칙 생성. 해당 피해·대피 결과 정답 없이 프로필만 넣어 개인 피해 확률을 학습할 수 없다. 첫 환경 모델에 민감 프로필을 넣지 않는다. |
| 사용자 위치 | 예측 격자와 사용자를 연결한다. 최신 위치의 시각·정확도와 이동 상태가 필요하다. 첫 원본에는 실제 위·경도 메타데이터가 없으므로 국내 사용자 좌표와 연결할 수 없다. |
| DB 기본 대응 매뉴얼 | 근거·버전·적용 조건이 있는 정책 자료. 검색과 Qwen의 안내 정리 및 정책 검증에 사용한다. 산불 확산의 실제 정답은 아니다. |
| 공식 재난 경보 | 발령 시각·원문·대상 구역을 보존해 공식 알림 경로에 사용한다. 문자 수신 지역을 화재 경계나 피해 정답으로 바꾸지 않는다. |
| 추가 뉴스 | 시점·출처·위치·신뢰도를 확인한 보조 증거. 뉴스만으로 음성/양성 정답을 만들거나 예측 시점 이후 기사를 입력에 넣지 않는다. |
| **추가: 현재 산불 관측** | 현재 화재 위치/영역, 관측 시각, 위성 품질·구름, 가능하면 FRP·진행 이력. 현재 불과의 공간적 관계가 필요하다. |
| **추가: 기상** | 풍향·풍속, 온도, 습도, 강수와 건조도. 향후 기상을 사용할 때는 당시 발행된 예보를 사용하고 미래 실측치를 섞지 않는다. |
| **추가: 지형·연료** | 고도·경사·사면, 산림/토지피복·식생·연료 습윤 상태. 첫 자료의 고도·NDVI·PDSI·ERC는 일부 대리 변수이고 국내 연료 지도 전체를 대체하지 않는다. |
| **추가: 이후 관측 정답** | 입력 시각 이후 같은 위치의 실제 화재 관측과 관측 불가 마스크. 이것이 있어야 지도학습이 가능하다. |

환경 예측을 사용자 위치에 결합한 뒤, 프로필·공식 경보·기본 지침·현장 근거를 함께 고려해 개인별 정책을 만든다. 대피 경로까지 안내하려면 도로 통제·대피소 위치/수용 상태·이동 시간도 별도로 확보해야 한다. 확률 하나에서 대응 레벨이 자동 결정된다고 가정하지 않는다. 레벨과 알림 방식은 회의 결정 사항이다.

## 첫 학습 목표

`P(다음 일별 위성 합성에서 해당 1km 격자에 화재가 관측됨 | 현재 일별 입력)`을 예측하는 연구용 이진 분류다. 기존 설계의 단기 도달/영향 목표를 대체한 운영 계약이 아니다. **60분 이내 도달, 개인 피해, 연기 흡입 위험, 대피 필요성, 대응 레벨은 이 데이터의 정답이 아니다.** 현재 이미 불이 있는 격자도 포함하므로 새로 번진 화재만을 예측하는 모델로 부르면 안 된다.

원본은 [Next Day Wildfire Spread](https://www.kaggle.com/datasets/fantineh/next-day-wildfire-spread) 버전 2다. 저자는 Fantine Huot 외 5인이고 CC BY 4.0이다. [논문](https://arxiv.org/abs/2112.02447)과 [공식 데이터 코드](https://github.com/google-research/google-research/tree/master/simulation_research/next_day_wildfire_spread)를 함께 확인했다. 변환·결측 처리·파생 입력 추가·중복 제거 사실과 저자 표시는 `training/README.md`에 남겼다.

미국 2012~2020년 자료의 64×64 격자 패치를 사용한다. 자료에 이미 불이 관측된 주변 패치가 중심이므로 전국 임의 위치의 산불 발생 빈도를 대표하지 않는다. 다양한 원본 해상도를 1km 격자로 맞춘 자료이며, 보간으로 세부 지형 정보가 새로 생긴 것은 아니다. 미국 자료에서 얻은 확률을 국내 개인 영향 확률로 제공할 수 없다.

## 실제 확보 결과

전체 발행 목록은 19개 파일, 3,955,889,585바이트다. **이번에는 공식 train/eval/test 각각 첫 파일 1개씩, 총 3개·639,939,000바이트를 확보했다.** 전체 자료 확보 완료로 표시하지 않는다. 원본마다 1,000패치, 합계 3,000패치이며 다운로드·SHA256·TFRecord CRC 검증을 마쳤다. 개인 실데이터나 합성 프로필을 섞지 않았다.

| 산출 분할 | 유지 패치 | 학습 행 | 화재 정답 1 | 양성 비율 |
| --- | ---: | ---: | ---: | ---: |
| train | 994 | 3,957,875 | 50,502 | 1.276% |
| validation (원본 eval) | 1,000 | 3,978,515 | 45,096 | 1.133% |
| test | 960 | 3,817,137 | 51,540 | 1.350% |
| 합계 | 2,954 | 11,753,527 | 147,138 | 1.252% |

원본은 `data/raw/ndws-v2/`, 변환 자료는 `data/processed/ndws-v2-bootstrap/`에 있다. Git에는 대용량 원본과 Parquet를 넣지 않고 출처·버전·크기·SHA256 목록, 품질 보고서와 변환 코드를 보존한다. `training/reports/source-manifest.json`, `training/reports/dataset-report.json`으로 확보 범위와 각 파일을 확인할 수 있다.

## 입력·정답과 품질 처리

기본 입력 12개는 `elevation, pdsi, NDVI, pr, sph, th, tmmn, tmmx, vs, erc, population, PrevFireMask`다. 온도는 Kelvin, 풍속은 m/s, 풍향은 북쪽 기준 시계 방향 도, 강수는 mm, 비습은 질량비다. NDVI는 배포된 원본 스케일을 유지한다. 인구 밀도는 지역 변수이며 개인 프로필이 아니다.

파생 입력 8개를 더해 총 20개를 사용한다. 이전 화재 관측 불가 여부, 주변 8칸 화재 수와 관측된 칸 수, **패치 내부** 관측 화재까지의 격자 거리, 패치 내 화재 존재 여부, 풍향 sin/cos, 물리적 QC로 결측 처리한 항목 수다. 패치 밖 화재는 거리 계산에 없고 경계 밖 칸은 관측되지 않은 것으로 취급한다. 1km 명목 격자 거리를 실제 대피 이동 거리로 해석하면 안 된다.

정답은 원본 `FireMask`의 0/1을 `fire_next_day`로 옮긴 것이다. `-1`은 구름·미처리 등 관측 불가이므로 제외한다. 유지 패치에서 제외한 정답 불명 픽셀은 train 113,549, validation 117,485, test 115,023개다. 이전 화재 마스크 `PrevFireMask=-1`은 NaN과 별도 플래그로 보존한다. 0은 해당 위성 자료에서 비화재로 분류됐다는 뜻이며 지상의 모든 작은 화재가 없었다는 보증은 아니다.

실제 원본에 음수 강수·풍속과 범위 밖 풍향, 0 Kelvin 등이 있었다. [원본 공식 전처리 상수](https://github.com/google-research/google-research/blob/master/simulation_research/next_day_wildfire_spread/constants.py)도 일부 입력의 범위 문제를 다룬다. 이 변환은 원본을 수정하지 않고 음수 강수·풍속·ERC·인구, 0~1 밖 비습, 0~360도 밖 풍향, 0 이하 Kelvin, 최저>최고 온도 쌍 및 비유한 값을 NaN 처리한다. 해수면 아래 고도와 음수 NDVI는 보존한다. 학습/평가 통계로 새 임계값을 추정하거나 결측을 0으로 대체하지 않는다. 특이하지만 이 규칙에 걸리지 않는 극값은 보고서의 min/max에 남기며 추가 검토가 가능하다.

예를 들어 유지한 train 원본의 음수 강수는 395,503칸이고, 정답 관측이 유효한 행 중 해당 강수가 결측 처리된 것은 387,726행이다. 보고서 `raw_input_qc`는 유지 패치 전체 입력 기준, `features.*.missing`은 정답 불명을 제외한 학습 행 기준이다. 두 수의 모집단이 다르다.

공식 분할을 그대로 매핑하고 픽셀 무작위 재분할을 하지 않았다. 분할 내부에서 입력과 정답이 완전히 같은 패치 46개(train 6, test 40)를 제거했다. 같은 입력에 다른 정답이 있으면 내부 중복으로 삭제하지 않는다. 분할 간 같은 입력은 양쪽 모두 격리하도록 구현했으며 이번 자료에서는 0건이다. 미래 정답을 제외한 입력 fingerprint와 별도의 정답 fingerprint를 사용한다.

원 논문의 주 단위 분할을 상속하지만 내려받은 레코드에는 날짜·사건 ID·위경도가 없다. **사건/공간 독립성과 유사 패치 중복은 검증하지 못했다.** 2,954개 패치를 2,954개의 독립 산불 사건이라고 보고하지 않는다. 일별 집계 입력은 과거 분석용이며 실제 예측 시점에 모든 입력이 도착했는지는 증명되지 않았다.

## 국내 수집 경로 확인

수집 담당 브랜치 `hyun02063185`의 `docs/data-collection/README.md`, `data/catalog/데이터카탈로그.csv`, `reviews/20261031/산불MVP_10분갱신_검수가이드.md`를 읽었다. 해당 브랜치를 병합하거나 다른 작업자의 파일을 수정하지 않았다. 이 인계 자료는 연결·파싱 검증 표본이며, 별도 보관 ZIP 원본은 이번 작업에 제공되지 않았다.

| 경로 | 확보할 자료 | 현재 상태/주의 |
| --- | --- | --- |
| [산림청 발생 통계 API](https://www.data.go.kr/data/3070842/openapi.do), [과거 CSV](https://www.data.go.kr/data/15121380/fileData.do) | 국내 사건·발생/진화·면적 | 카탈로그 확인. 이번에 실제 응답/CSV를 수집한 것은 아님. 시간별 확산 경계가 아님. |
| [기상청 ASOS](https://www.data.go.kr/data/15057210/openapi.do), [AWS](https://apihub.kma.go.kr/apiList.do?seqApi=2&seqApiSub=239) | 현장 주변 시간별 기상·QC | 서비스키/API Hub 인증 필요. 서울108 일자료 2일 표본은 산불 현장 풍장 학습 자료가 아님. |
| [천리안 GK2A 산불](https://apihub.kma.go.kr/apiList.do?seqApi=6&seqApiSub=271) | 화재 탐지 시각·위치·품질 | 인증 후 과거 제품 확보 필요. 제품 생성 간격과 실제 도착 지연을 구분해야 함. |
| [NASA FIRMS](https://firms.modaps.eosdis.nasa.gov/content/academy/data_api/firms_api_use.html) | 위성 탐지·FRP·관측시각 | 최근 7일 CSV는 공개. 기간/영역 API는 MAP_KEY 필요. 인계의 광역 379건은 탐지점 수이고 국내 독립 산불 사건 수가 아님. |
| [공식 긴급재난문자](https://www.safetydata.go.kr/disaster-data/view?dataSn=228) | 발령 원문·시간·수신 구역 | 승인키 필요, 인계에 사건 원문 미확보. 문자 구역을 화재 경계로 쓰지 않음. |

Sentinel 카탈로그 9건은 영상 픽셀 확보와 다르고, 일부 FIRMS 사례 기간의 0건은 비화재 정답이 아니다. 구룡마을 도시 화재 표본을 산림 화재 확산 정답으로 쓰지 않았다. 경로별 세부 상태는 `training/sources/source-audit.json`에 남겼다.

국내 학습에는 같은 사건의 시간·좌표가 있는 진행 관측/경계와 그 이전에 이용 가능했던 기상·식생·지형 자료를 결합해야 한다. 특히 국내 1시간 도달 확률에는 그 시간 해상도의 정답이 필요하며, 다음 날 위성 자료를 복제해서 만들 수 없다.

## 재현·검증과 다음 학습 조건

[training/README.md](../../../training/README.md)의 download → build → verify 명령으로 재생성한다. 별도 uv lock을 사용한다. 전체 19개 자료는 `download --all-shards`로 별도 디렉터리에 확장할 수 있다.

이번 검증은 TFRecord CRC·형식·마스크 값, 원본/Parquet SHA256, 공식 분할·동일 표본 검사, 전체 11,753,527행 배치 로딩, 정답 분포, 미래 정답을 바꿔도 입력이 바뀌지 않는 검사, 결측/QC 및 파일 변조 검출을 포함한다. XGBoost 3.4.1의 실제 DMatrix에 첫 65,536행·20개 입력을 읽는 검사도 수행했다. 모델 학습 성능을 측정한 결과는 아니다.

독립 임시 디렉터리에서 원본 3개를 다시 변환해 보고서 전체와 Parquet 3개 SHA256이 일치함을 확인했다. 단위·통합 검사 11개와 training Ruff 검사도 통과했다. 재생성과 DMatrix 로딩의 실제 버전·행 수는 `training/reports/validation-summary.json`에 보존했다.

후속 학습은 먼저 `PrevFireMask`를 그대로 예측하는 persistence 기준선과 비교하고, PR-AUC·재현율·Brier score·확률 보정을 확인해야 한다. 약 99%의 음성 비율 때문에 정확도 하나로 판단하지 않는다. test는 튜닝에 쓰지 않는다. 보정에는 튜닝과 독립된 자료가 필요하며, 국내 실사용 전에는 날짜/사건/좌표를 보존한 국내 외부 검증과 서비스 입력 가용성 검증이 필요하다. 대응 레벨 임계값은 여기서 결정하지 않았다.

### required-doc: docs/V2/delivery/xgboost-training-run.md

- Path: `docs/V2/delivery/xgboost-training-run.md`
- Status: present

# XGBoost 학습 시작 방법

2026-10-31, Task `task-20261031-102643-xgboost-gpu-63a490e2`. 실제 자료 일부로 CPU 학습 실행기를 검증했다. GPU 전체 학습과 Qwen 서비스 중단은 이번 준비 작업에서 실행하지 않았다.

GPU 서버 `/home1/ncloud/bonghwajigi/`에 코드·`training/.venv`·원본 `data/raw/ndws-v2/`·변환 `data/processed/ndws-v2-bootstrap/`을 준비했다. 대용량 Tailnet 전송이 느려 서버에서 같은 원본을 직접 다운로드하고 재생성했다. 원본 SHA256 3개와 train/test Parquet 해시는 맥과 일치한다. validation은 코사인 파생 열에서만 플랫폼에 따른 바이트 차이가 있고, 소수 6자리 반올림 값의 해시는 일치한다. 나머지 19개 입력과 정답의 열 해시는 일치한다. 서버 보고서는 `training/reports/gpu-dataset-report.json`에 별도로 보존해 전체 바이트가 같다고 주장하지 않는다.

## 서버에서 시작

```bash
ssh inno-gpu-011
cd /home1/ncloud/bonghwajigi
systemd-run --user --unit=bonghwajigi-xgboost --collect \
  --working-directory=/home1/ncloud/bonghwajigi \
  /bin/bash training/tools/train_gpu.sh
```

위 명령을 사용자가 실행하면 **Qwen 생성·임베딩 서비스를 잠시 멈추고 GPU 학습 후 복구한다.** 학습 중 두 모델 API는 일시 사용할 수 없다. SSH가 끊겨도 학습은 유지된다. 같은 이름의 unit이 이미 실행 중이면 재시작이 거부된다.

별도 터미널에서 로그와 GPU 사용률을 확인한다.

```bash
journalctl --user -u bonghwajigi-xgboost -f
```

```bash
nvidia-smi -l 1
```

로그의 `train-aucpr`, `validation-aucpr`, `logloss`가 진행 상황을 보여 준다. 로그 보기의 Ctrl+C는 학습을 중단하지 않는다. 실제 중단 명령은 다음과 같다.

```bash
systemctl --user stop bonghwajigi-xgboost
```

스크립트는 정상 종료·오류·INT/TERM 때 기존에 켜져 있던 Qwen 서비스를 복구한다. SIGKILL·전원 차단에서는 쉘 복구를 보장하지 못한다. 시작 전 꺼져 있던 서비스는 자동으로 켜지 않는다. 복구 확인은 다음 명령으로 수행한다.

```bash
systemctl --user status bonghwajigi-gpu.service
systemctl --user start bonghwajigi-gpu.service
.venv-gpu/bin/python tools/gpu_client.py ready
```

서비스 start 성공과 두 모델의 로딩 완료는 구분한다. 실제 준비 완료는 ready로 확인한다.

## 설정과 산출물

서버의 `data/processed/ndws-v2-bootstrap/`에서 train 3,957,875행과 validation 3,978,515행을 사용한다. 기본 설정은 최대 300회, validation AUC-PR이 30회 개선되지 않으면 조기 종료, depth 6, learning rate 0.05, seed 47, CPU thread 4다. 최적화된 설정이라는 뜻은 아니다. validation에서 가장 좋은 회차를 저장한다.

[공식 GPU 사용법](https://xgboost.readthedocs.io/en/stable/gpu/index.html)의 hist/cuda 설정을 사용한다. 실제 장치가 CPU로 대체되면 성공으로 기록하지 않는다. 서빙과 같은 `/home1/ncloud/.cache/bonghwajigi/gpu.lock`을 사용하며 외부 CUDA 프로그램까지 격리하지는 않는다.

결과는 `data/artifacts/xgboost/ndws-<UTC시각>-<PID>/`에 저장되고 경로가 로그에 출력된다.

| 파일 | 내용 |
| --- | --- |
| `model.ubj` | 최적 회차의 모델 |
| `report.json` | 평가·기준선·데이터 해시·장치·피처 순서·CPU 재로딩 일치 검사 |
| `parameters.json` | 학습 설정 |
| `history.json` | 회차별 지표 |
| `feature-gain.json` | 피처 중요도 |
| 디렉터리 옆 같은 이름의 `.log` | 표준 출력·오류 |

성공 시에만 report.json을 기록한다. 실패한 디렉터리를 완성 모델로 취급하지 않는다. 학습 이력의 XGBoost aucpr과 최종 보고서 sklearn average_precision은 계산 정의가 다르다. 기준선은 학습 양성 비율의 상수 예측과 이전 화재 관측을 유지한 persistence다. persistence는 이전 관측이 알려진 행에서만 평가하며 같은 행에서의 모델 점수도 기록한다. 불명 관측은 0으로 바꾸지 않는다.

test는 기본 실행에서 모델 평가에 쓰지 않는다. 설정 고정 후 최종 평가 때만 `--evaluate-test`를 지정한다. validation은 조기 종료에 사용됐으므로 독립 최종 성능 근거가 아니다. 확률 보정은 수행하지 않았고 `operational_use=false`다. 0.5 기준 precision/recall은 진단용이며 대응 레벨 기준이 아니다.

## 환경 준비와 CPU 사전 실행

서버의 독립 환경은 training/.venv다. 다른 체크아웃에서 준비하려면 코드·변환 자료를 먼저 옮긴 뒤 실행한다.

```bash
~/.local/bin/uv sync --project training --frozen --extra train
training/.venv/bin/python -m bonghwa_training.train --help
```

일부 자료로 실행기를 확인하는 CPU 예시다. Qwen을 중단하지 않으며 출력 경로는 매번 새 경로를 지정한다.

```bash
training/.venv/bin/python -u -m bonghwa_training.train \
  --dataset data/processed/ndws-v2-bootstrap \
  --output data/artifacts/xgboost/cpu-preflight-new \
  --device cpu --max-rows 131072 --rounds 12 --early-stopping 4 --threads 2
```

로컬 사전 실행은 각 분할 첫 131,072행으로 조기 종료·4개 트리 저장·CPU 재로딩 최대 차이 0을 확인했다. 제한 표본은 순서에 따른 편향이 크며 최종 성능이 아니다. GPU 전체 학습의 시간·메모리·성능은 아직 측정하지 않았다. [데이터 한계](xgboost-training-data.md)에 따라 미국 1km 다음 일별 위성 관측 연구 모델로만 해석한다.

GPU 서버에서도 CPU 사전 실행을 완료했고 12개 트리 저장·재로딩 차이 0을 확인했다. 서로 다른 플랫폼에서 같은 seed가 동일 모델을 보장하지는 않는다. `/usr/bin/true`의 systemd 사용자 unit 실행과 기존 Qwen 잠금에 의한 학습 진입 거부도 검사했다. training 테스트 15개, Ruff와 bash 문법 검사를 통과했다. 실행 근거는 `training/reports/gpu-training-readiness.json`에 남겼다.

## Verified Team Policies

No verified Team Policy Snapshot is active.

## Active Workflow Memory

No active workflow memory recorded.
