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
- Task count: `9`

## Task

- Title: 국내 산불 적용을 위한 원인 분석과 공개 정답·입력 확보 및 개선 실험
- Description: 사용자가 쓸만한 수준까지 계속 개선하라고 직접 지시했고 최종 목표를 국내 사용자 대응 판단에 연결할 수준으로 명시했다. 기존 모델의 임계값·희소 양성·표본·시공간·확률 보정 문제를 측정하고, 국내 시각/좌표가 있는 공개 관측 정답과 일치하는 기상/지형 입력을 실제 확보한다. 사용 가능성이 검증되지 않은 미국 점수 개선을 국내 적용 성공으로 보고하지 않는다.
- Expected output: 원인 진단과 precision/recall/오경보 곡선, 국내 실제 원본·provenance·입력/정답 계약 및 사건 분할, 재현 가능한 수집/구축/학습/평가 실험과 한계·진행 기록
- Done condition: 원인과 개선 효과를 수치로 확인하고 확보 가능한 국내 자료의 실제 다운로드·품질·시점·좌표·정답 적합성을 검증한다. 독립 평가 구획을 사전에 고정해 가능한 학습 개선을 실행하고, 국내 연결 가능 여부와 미확보 조건을 정직하게 기록한다. 운영 정책/레벨을 임의 결정하거나 누출로 점수를 높이지 않는다.
- In scope: training/과 자료 전용 경로, 국내 공식/공개 데이터 확보와 정답·입력 시점 검증, 연구용 목표/지표 사전 명세, 반복 개선·확률/임계값 진단, 독립 검증과 Loom 기록, 필요시 GPU 학습과 기존 서비스 복구
- Out of scope: 앱·다른 작업자의 RAG 파일·운영 배포·사용자 알림·대응 레벨 결정·유료 서비스·자격정보 커밋·test에 맞춘 튜닝과 국내 검증 없는 운영 성능 주장·원격 push
- Validation hint: 원본 SHA·공식 출처/이용조건·지역/시각/좌표·관측불가/QC·미래 정보 누출·사건/시기 분리·미사용 최종 평가·오경보/누락과 calibration·CPU reload·서빙 복구·Loom strict
- Required docs: `docs/V2/delivery/xgboost-training-verification.md`, `docs/V2/delivery/xgboost-training-data.md`
- Memory refs: -
- Document outputs: `docs/V2/delivery/korea-wildfire-improvement.md`
- Document output exceptions: -
- Source proposal: `-`
- Status: RUNNING
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
## 2026-10-31T10:55:42+00:00

사용자가 직접 시작한 NDWS CUDA run ndws-20261031T104838Z-528483를 확인했다. 실제 모델 SHA256 14a988b3b8e2755c54bc89f82a00d4babee2c3c24970df57df10973112809cb5가 보고서와 일치하고 64회 이력의 최고 검증 회차는 index 33이다. Qwen active/ready와 GPU 프로세스 복구를 확인했다. 원본 모델을 고정하고 CPU validation 재현 및 첫 test 평가만 진행하며 재학습·임계값 결정은 하지 않는다.

- Task: `task-20261031-105243-cuda-b5a38b8b`
- Tags: `verification`, `frozen-model`, `holdout`

## Context References

No explicit context references recorded for this job.

## Required Documents and Memory

### required-doc: docs/V2/delivery/xgboost-training-verification.md

- Path: `docs/V2/delivery/xgboost-training-verification.md`
- Status: present

# 첫 CUDA 학습 완료와 저장 모델 검증

2026-10-31 KST. Task `task-20261031-105243-cuda-b5a38b8b`. 사용자가 실행한 `ndws-20261031T104838Z-528483`의 원본 파일과 서비스 상태를 서버에서 직접 확인하고, 모델을 고정해 CPU 재추론했다. 재학습·파라미터 변경·서빙 중단은 하지 않았다.

## 완료 판정

정상 완료했다. 학습 보고서의 장치는 `cuda:0`, XGBoost는 3.4.1이다. 데이터 3,957,875행·20개 입력을 사용했고 64회 실행한 뒤, 최고 validation AUC-PR 시점인 **0부터 시작하는 index 33, 즉 34번째 모델**을 저장했다. 그 뒤 30회 동안 최고 점수가 개선되지 않아 조기 종료했다. 최고 AUC-PR은 0.14471228293604이고 실제 저장 모델은 34개 트리를 가진다. 300회를 채우지 못한 오류가 아니다.

실측 학습·검증 파이프라인은 **24.869초**다. journal 기준 전체 wrapper는 19:48:38 시작부터 19:49:09 서비스 복구 명령까지 약 31초다. 이전 5~10분 예상은 실측보다 길었다. journal의 `50.673s CPU time`은 여러 CPU 작업의 누적 시간이며 경과 시간이 아니다.

모델 SHA256은 다음과 같으며 원본 보고서·서버 파일·로컬 사본·검증 종료 후 원본 파일에서 모두 일치했다.

```text
14a988b3b8e2755c54bc89f82a00d4babee2c3c24970df57df10973112809cb5
```

원본 서버 경로는 `/home1/ncloud/bonghwajigi/data/artifacts/xgboost/ndws-20261031T104838Z-528483/`다. 모델·원본 보고서·학습 이력·별도 audit·서비스 상태·journal과 데이터 보고서 사본은 `training/reports/ndws-20261031T104838Z-528483/`에 보존했다. 모델은 연구용이며 자동 운영 배포되지 않는다.

## 재계산한 성능

원본 모델을 CPU로 새로 로딩해 **validation 3,978,515행의 지표가 기존 보고서와 일치함을 확인**했다. 이후 학습과 조기 종료에 쓰지 않은 test 3,817,137행을 처음 평가했다. 원본 학습 report의 `test_evaluated=false`는 당시 사실로 보존하고, 별도 `audit.json`에 이번 test 평가를 기록했다. 검증을 위해 모델을 재학습하지 않았다.

| 전체 관측 행 기준 | validation | test |
| --- | ---: | ---: |
| 화재 관측 정답 픽셀 | 45,096 | 51,540 |
| 모델 AP (클수록 좋음) | 0.144925 | 0.237273 |
| 상수 예측 AP | 0.011335 | 0.013502 |
| 모델 ROC-AUC | 0.840350 | 0.882856 |
| 모델 Brier (작을수록 좋음) | 0.010346 | 0.011377 |
| 상수 예측 Brier | 0.011208 | 0.013321 |

현재 화재 상태를 그대로 다음 날 예측하는 persistence와는 **이전 화재 관측이 알려진 동일한 행**에서 비교해야 한다.

| 동일 평가 행 기준 | validation | test |
| --- | ---: | ---: |
| persistence AP | 0.046246 | 0.112542 |
| 모델 AP | 0.145378 | 0.237916 |
| 모델 / persistence AP | 3.144배 | 2.114배 |
| 평가 행 수 | 3,922,548 | 3,784,611 |

단순 기준선보다 화재 관측 픽셀을 높은 순위에 배치하는 신호는 확인됐다. AP 배수는 탐지율이나 정확도의 배수를 뜻하지 않는다. AP 0.237은 정확도 23.7%라는 뜻도 아니다. XGBoost 학습 로그의 `aucpr`은 연속 보간을 사용하는 PR 면적이고 최종 sklearn AP와 계산이 달라 두 수치가 약간 다른 것은 오류가 아니다. [XGBoost 정의](https://xgboost.readthedocs.io/en/stable/parameter.html), [sklearn AP 정의](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.average_precision_score.html).

## 임계값 0.5의 진단 결과

| 진단 항목 | validation | test |
| --- | ---: | ---: |
| 실제 화재 관측 픽셀 | 45,096 | 51,540 |
| 탐지한 화재 픽셀 (TP) | 209 | 12 |
| 놓친 화재 픽셀 (FN) | 44,887 | 51,528 |
| 오경보 픽셀 (FP) | 326 | 55 |
| precision | 39.065% | 17.910% |
| recall | 0.4635% | 0.0233% |

이는 **0.5를 바로 경보 기준으로 쓰기 어렵다는 결과**다. 순위 예측 성능 개선과 특정 임계값의 탐지율은 다른 평가다. 낮은 임계값을 선택하면 탐지와 오경보가 함께 달라지므로, 허용할 오경보와 누락의 비용을 정하고 validation에서 검토해야 한다. 이번에는 임계값이나 대응 레벨을 정하지 않았다.

확률 보정은 아직 하지 않았다. Brier 개선만으로 확률 보정이 입증된 것도 아니다. test 결과를 보고 계속 튜닝하면 해당 test는 이후 모델의 최종 독립 평가 자료로 재사용할 수 없다. 후속 튜닝 시 별도 평가 구획이 필요하다.

## 서비스와 사용 한계

학습 후 Qwen 서비스는 `active`, 생성·임베딩 두 모델 모두 실제 `ready` 응답을 확인했다. GPU 프로세스 PID 528588은 `.venv-gpu/bin/python`, 사용 메모리는 약 9GB였다. 사용자가 첨부한 화면의 GPU 사용률 0%는 학습 종료 후 시점이며 모델 상주 메모리와 모순되지 않는다. 검증 과정에서는 CPU만 사용하고 GPU 서비스를 재시작하지 않았다.

이 결과는 미국 1km 다음 일별 위성 화재 관측 연구용 데이터 일부에서의 결과다. 수백만 행은 독립 산불 사건 수가 아니라 서로 관련된 픽셀 수다. 날짜·사건 ID·좌표가 없어 사건/공간 독립성은 검증하지 못했고, 국내 외부 검증·운영 시점 입력 가용성·개인 영향·경보 임계값·확률 보정은 남아 있다. 국내 개인 대응원칙의 판단 근거로 승인한 모델이 아니다.

현재 이력에서 최적 회차 이후 train 점수는 상승했지만 validation은 개선되지 않았다. 이 실행 결과만으로 학습 상한을 1,000회로 늘릴 근거는 없다. 후속 개선은 목표에 맞는 국내 자료와 입력·정답 정렬, 기준선·누락/오경보 및 확률 검증을 우선한다.

## 재현 명령

GPU 서버의 원본 모델을 바꾸지 않고 CPU로 다시 검증한다. 출력 경로는 새 파일이어야 한다. 아래 명령은 test도 평가하므로 이후 튜닝/최종 평가 이력에서 이를 숨기지 않는다.

```bash
cd /home1/ncloud/bonghwajigi
training/.venv/bin/python -u training/tools/verify_model.py \
  --run data/artifacts/xgboost/ndws-20261031T104838Z-528483 \
  --dataset data/processed/ndws-v2-bootstrap \
  --output data/artifacts/xgboost/audits/new-verification.json
```

실제 이번 출력은 서버 `data/artifacts/xgboost/audits/task-105243.json`이다. Ruff 검사·Python 구문 검사·실제 CLI의 전체 자료 무결성 검사, validation 재현과 test 재추론을 통과했다.

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

## Verified Team Policies

No verified Team Policy Snapshot is active.

## Active Workflow Memory

No active workflow memory recorded.
