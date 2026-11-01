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
## 2026-10-31T15:19:14+00:00

2026-11-01 모델 개선 재개. v4 수집이 00:04 KST에 Hongseong/Gangneung 원본 manifest split과 이미 고정한 학습 분할 차이로 중단된 것을 확인했다. 원본 바이트와 메타데이터는 보존하고 비시험 split만 달라진 캐시를 재사용하며 config/manifest SHA 완료 영수증을 검증하도록 복구했다. 00:15 KST 수집→구축→GPU 학습→순위 진단 unit 재시작. 완료16창 재사용, 남은5창 수집 중. 새 5후보 날짜그룹 CPU CV(1·3·6h AP, 양성가중/사건가중/깊이) 및 같은 validation행의 이전v3/v4 대조를 준비했다. 120 training tests와 Ruff 통과. 2025 잠금 및 운영 미연결 유지. 실제 개선 결과는 아직 대기 중이며 완료 처리하지 않는다.

- Task: `task-20261031-111807-task-9a960503`
- Tags: `model-improvement`, `recovery`, `group-cv`
## 2026-10-31T15:27:42+00:00

v4 결과 열람 전 추가 실험 고정: 기간그룹 CV로 선택된 후보의 학습 OOF 예측만으로 단일 전역 sigmoid(logit 1입력, LogisticRegression C=1/class_weight=None/lbfgs/seed47/max_iter1000)를 적합한다. 2023 검증으로 보정 방법·계수를 선택하지 않으며 양의 기울기 및 기간 단조성을 검사하고 원점수/학습prior와 같은 검증행의 Brier/logloss/AP를 보고한다. 순위 AP 개선 방법이 아니며 확률 보정의 개선 여부만 확인한다. OOF는 보정 학습에 쓰여 독립평가가 아니고 선택편향 및 2023 기존 노출을 명시한다. 2025/보정 구획 미열람 유지, 운영 미연결.

- Task: `task-20261031-111807-task-9a960503`
- Tags: `experiment-plan`, `oof-calibration`
## 2026-10-31T15:38:34+00:00

v4 실제확보 완료: 21비시험창/1949고유NC/1,349,810,523bytes, train14창315490행1767양성, val6창217604행1079양성. GPU7후보42.28초, 학습11기간그룹5후보CV140.394초 모두완료, Qwen두모델ready복구. 동일val14적격event×h셀 macroAP 기존v3 .356335→v4CV .432810이나 최근거리 .471403 미달, top10% pooled recall .661724→.646895. OOF단일sigmoid29.988초: AP불변, 행가중Brier .015086→.004248 개선이나 사건×기간균등Brier .012697→.030589 악화(함평3/6h), 운영승격보류. 추가 3후보 계획: 거리4개 monotone -1+기간+1의 전체피처/환경·시각제외/현재·최근거리+기간3피처 후보를 같은학습그룹CV로만 기존선택과비교하고 선택후validation1회. 새로운2023기존노출 명시, 보정/2025미열람. 기존artifact불변, 별도모듈/경로 사용.

- Task: `task-20261031-111807-task-9a960503`
- Tags: `results`, `comparison`, `distance-prior`
## 2026-10-31T15:52:32+00:00

v4 수집·구축·모델 비교 완료. 학습 14창 315,490행, 검증 6창 217,604행(3날짜 그룹). 동일 14개 적격 사건×기간 평균 AP 기존 v3 0.356335 → 학습 그룹 CV 선택 0.432810; 최근 거리 기준 0.471403. 상위 약10% 검토 recall 기존66.17% → 새64.69%, 최근거리67.10%이므로 운영 승격하지 않음. OOF sigmoid는 micro Brier 0.015086→0.004248이나 사건 균등 Brier 0.012697→0.030589 악화, 채택하지 않음. 마지막 거리 제약 3후보/신규34fits/64.618초: CV0.397664이나 검증AP0.405077, recall65.62%로 교체하지 않음. 실패 결과 포함 모델·선택 기록·해시 보존. 2025 시험 미열람; operational_use=false. 훈련 테스트146개, JSON35개/문서 링크/모델-plan-selection SHA/diff 검사 통과. Qwen 생성·임베딩 ready, L4 9080MiB/0%. 이번 실행 모두 종료; Task RUNNING은 미달성 국내 대응 목표를 뜻함. 다음 과제: 실제 관측 간격/이력 가용성 및 관측 정답·입력 시점 정합 개선. 결과 문서 docs/V2/delivery/korea-wildfire-improvement.md.

- Task: `task-20261031-111807-task-9a960503`
- Tags: `model-improvement`, `v4`, `validation`, `no-promotion`
## 2026-10-31T16:11:17+00:00

사용자가 모델 교체를 포함해 개인 영향 확률 가능성의 넓은 검토를 요청. 공식 자료 조사 결론: 특정 위치의1/3/6h 최초 화재 접근 확률은 개발 가능한 연구 목표. 국내 접근 시간 정답·미래 기상 확보 후 작은 시간 모델(AFT/이산hazard)과 물리 확산 앙상블을 같은 사건 분할로 비교하는 방향 권고. 시공간CNN/AI대리모델·기관/상용API·연기HYSPLIT도 비교. 신체피해확률/시나리오빈도/위성관측확률은 구분. ELMFIRE AGPLv3+Commons Clause 상업별도계약, Spark Research 평가제한, WiDS대회용자료 제한 확인. KIML/KIMR API 존재/보유권한미확인; 시간별국내화선/연료가 병목. 상세근거는 docs/V2/delivery/korea-wildfire-improvement.md. 이번에는 조사·설계 검토만 수행했고 설치/추가훈련/운영변경은 없음. 2025미열람 및 기존operational_use=false 유지.

- Task: `task-20261031-111807-task-9a960503`
- Tags: `feasibility`, `model-alternatives`, `impact-target`, `sources`
## 2026-10-31T16:16:07+00:00

사용자가 검토안 즉시 준비·실행을 지시. 이번 실행은①기존 서버키를 노출하지 않는 KMA 미래기상/과거예보 소량 권한·내용 확인②CC-BY-4.0 확인된 GOFER 시간별 경계로 국외 재구성 최초접근시간 pilot자료 구축③사전고정 lognormal AFT(전체7피처/거리1피처, depth3·100rounds·sigma1·seed47·CPU2threads)와 거리/접근속도 기준 비교④격리 ELMFIRE 빌드·공식 synthetic검증. 한국2025정답/앱/운영정책/기존모델 변경없음. GOFER는 사후위성재구성 자료이며 국내/개인피해/실시간입력가용성 증거가 아님. 후보·계획은 validation결과 전 고정; 사건/연관화재group분리와구간검열 사용. simulation 비율은보정확률아님. 연구용 설치만,유료서비스신청없음.

- Task: `task-20261031-111807-task-9a960503`
- Tags: `approach-pilot`, `execution`, `forecast`, `physics`
## 2026-10-31T16:30:10+00:00

즉시실행 연구 완료: GOFER28사건153325행, 고정 AFT2모델 학습6.124s. 이력모델 macroAP0.259488로 단순거리0.262214 미달, 국내정책승격없음. ELMFIRE격리설치와 공식합성/9개풍속풍향조합 모두성공22.944s; probability=null. KMA지점예보403은원인미확정, 사용자에게정확한1.5.2활용신청안내. 공개GFS현재예보6정시확보. 231테스트, 원본/모델/plan/source해시, Qwen생성/임베딩ready확인. 결과·이용조건·재현명령은 improvement문서와 training/reports/approach-pilot-20261101에보존. 국내2025미열람, 모든이번계산종료, 장기Task는RUNNING이며백그라운드학습중의뜻아님. 수동commit정책유지.

- Task: `task-20261031-111807-task-9a960503`
- Tags: `research`, `approach`, `elmfire`, `validation`
## 2026-10-31T16:43:42+00:00

KIML 접속 해결: 사용자1.5.2주소후 같은서버키의샘플200확인. 이어2026-11-01 01:41KST 현재예보cycle2026103112/6개미래정시×U10,V10,T2,RH2=24회 모두200·CSV/좌표/범위검증. float32요청좌표echo 실제회귀수정, 최초실패원본보존. 새kiml_point_forecast.py(최대24회·1초간격·오류즉시중단),전체273테스트통과. source발행시각/단위/변수echo없음과풍향축미확인 명시,풍향null. training/reports/kiml-forecast-access-20261101과delivery문서에원본·SHA·계획·결과보존. 국내2025미열람,모델재학습·운영정책연결·commit/push없음.

- Task: `task-20261031-111807-task-9a960503`
- Tags: `forecast`, `kma`, `validation`
## 2026-10-31T16:51:54+00:00

사용자 진행 승인 후 다음 고정 연구: 129.3E/37N 주변10km·100m UTM52 국내DSM/CCI2015, 가정점화(중심500m이내최근접forest셀중심)와상수연료181/183/185 세시나리오,dead수분6/7/8%·수관화/비화비활성. KIML발행2026103112의18UTC~다음00UTC 7시각을사용하되 실제풍향축/높이확인없이는실행차단. sourceNC/GRIB검증및CSV동일값대조를진행. 실제화선/국내연료보정/영향확률검증이아니며 probability=null. 국내2025미열람,서비스정책미연결. 기존28값중최종두시각8값추가수신성공(기존24와합계32값),기상수집실행은제한된요청으로종료.

- Task: `task-20261031-111807-task-9a960503`
- Tags: `research`, `terrain`, `weather`, `simulation`
## 2026-10-31T17:03:29+00:00

국내 10km×10km/100m UTM52 지형 확보·서버 업로드 완료. DEM 유효100%, CCI 미상0, forest8083셀. KIML 추가8값 포함 총32개 원변수 값 보존. 사용자1.1.3 신청 완료 뒤에도 원본NC403; 동일endpoint의 NC/TEXT 진단2회 모두 활용신청 필요라는 명시응답. 사용자 계정/활용현황 확인 질문 pending. 방향축 미확인 KIML을 강행하지 않고 별도 OpenMeteo GFS 7시각 공개입력 경로 준비. 3연료 가정 시나리오, 실제 화선·국내 연료 보정 없음; probability=null/operational_use=false 유지. 2025 holdout 미열람.

- Task: `task-20261031-111807-task-9a960503`
- Tags: `research`, `weather`, `terrain`, `provenance`
## 2026-10-31T17:14:58+00:00

국내 지형+공개 GFS7시각+3가정연료 ELMFIRE 실험 완료. 처음 nodata0/초기0 충돌을 검출해 -9999 입력으로 수정하고 같은 물리조건 재실행3/3 전체6h완료(2.873초). 181/183은초기1셀만,185는6h추가3셀; 실제화선검증이나개인확률아님. probability=null/operational_use=false. 전체365테스트통과·출력/SHA·코드동일성·Qwenready확인. KMA파일형API는같은계정활용현황미등록으로403유지,더요청안함. 증거 training/reports/korea-scenario-20261101/, 결과/자원문서/Loom서술갱신. 국내운영성능목표는미달성으로RUNNING유지,이번실험은종료되어백그라운드학습없음.

- Task: `task-20261031-111807-task-9a960503`
- Tags: `research`, `elmfire`, `validation`, `weather`
## 2026-10-31T17:21:59+00:00

사용자 이어서해 지시에 따라 실제사건 hindcast준비 시작. 성능/미래확산을보지않고 학습2019/2020 중 최초GOES메타시각 Walker2019고정. 최초공개경계20190904T22Z를t0로사용(07Z발화메타시각혼동금지),+1/+3/+6 정답분리. 초기경계bbox+고정20km확장만으로419x411/100m/UTM10N영역고정. 실제과거NOAA HRRR20Z h2..8 원예보접근/index확인,실제LF2016연료+DEM공개수집 준비. 3사전고정수분/지표화실험;후향GOFER및자료배포가용성미검증,국내2025미열람,개인확률null유지. 국내2019~2023공개화선자료별도조사병행.

- Task: `task-20261031-111807-task-9a960503`
- Tags: `research`, `hindcast`, `provenance`
