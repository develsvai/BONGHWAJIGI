# Previous Results

## 6. 산불 XGBoost 학습용 공개 원본 확보와 재현 가능한 데이터셋 구축

# 결과

국내 수집 담당 브랜치의 카탈로그·검수 자료를 확인하고, 사용자가 허용한 국외 공개 NDWS v2 원본 3개를 실제 확보했다. 다운로드 원본은 639,939,000바이트이고 전체 19개 중 첫 train/eval/test 파일만 확보한 bootstrap이다. 원본 3,000패치에서 같은 입력·정답 중복 46개를 제거하고 관측 불가 정답을 제외해 11,753,527행의 XGBoost 학습 자료를 생성했다.

- train 3,957,875행(양성 50,502), validation 3,978,515행(45,096), test 3,817,137행(51,540).
- 목표는 미국 1km 격자의 다음 일별 위성 화재 관측 0/1. 국내 개인 영향·60분 도달·대응 레벨 학습 결과가 아니다.
- training 전용 uv 프로젝트에 다운로드, TFRecord CRC 파싱, QC, 파생 입력 8개, 전체 20개 피처, 공식 분할 보존·중복 검증·Parquet·배치 로더를 구현했다.
- 원본 data/raw/ndws-v2, 변환 data/processed/ndws-v2-bootstrap은 Git 제외. 재현 코드·SHA manifest·품질/검증 보고서는 training/에 보존했다.
- docs/V2/delivery/xgboost-training-data.md와 training/README.md에 국내 인증 경로·미확보 상태, 사용자 제안 입력의 역할, 실제 정답·한계·실행법을 기록했다.

# 검증

- `training/.venv/bin/python -m pytest training/tests`: 11 passed.
- `training/.venv/bin/ruff check training`: 통과.
- `training/.venv/bin/bonghwa-dataset verify --output data/processed/ndws-v2-bootstrap`: 전체 11,753,527행 스키마·SHA256·라벨·무한대 검사 통과.
- `training/.venv/bin/python training/tools/verify_release.py --raw data/raw/ndws-v2 --processed data/processed/ndws-v2-bootstrap --reports training/reports`: 독립 재생성 보고서 및 3개 Parquet 해시 일치, 재생성 전체 배치 검증 통과, XGBoost 3.4.1 DMatrix에 각 분할 65,536행·20개 열 로딩 성공.
- 미래 정답 변경 시 입력 불변, 마스크 -1 제외/보존, 잘린/변조 TFRecord와 Parquet 거부, 분할 간 중복 격리와 동일 입력·다른 정답 보존을 검사했다.

# 제한과 인계

원본에 날짜·사건 ID·위경도가 없어 사건/공간 독립성과 국내 위치 연결은 증명되지 않았다. 물리적 이상 입력은 NaN과 QC 개수로 처리했고 원본은 보존했다. 일별 사후 집계 입력의 실시간 가용성과 한국 적용·확률 보정은 미검증이다. 실제 산불 모델 학습이나 운영 성능을 주장하지 않는다. GPU 서빙과 다른 작업자의 분석 큐 구현은 변경하지 않았다. 기존 C1~C5는 별개 PENDING 작업으로 유지했다.

## 7. 실데이터 XGBoost 학습 실행기와 GPU 수동 시작 절차 준비

# 결과

사용자가 직접 실행할 NDWS XGBoost 학습 진입점 `training/src/bonghwa_training/train.py`와 `training/tools/train_gpu.sh`를 준비했다. 기본값은 최대 300회, validation AUC-PR 30회 조기 종료, 최적 회차 저장이다. train/validation 분리를 유지하고 test 평가는 기본적으로 하지 않는다. 상수·persistence 기준선, AP/Brier/ROC-AUC/logloss와 진단용 precision/recall, 모델 해시·피처 순서·CPU 재로딩 일치 검사를 저장한다.

GPU 서버 `/home1/ncloud/bonghwajigi`에 전용 코드와 `training/.venv` 환경, NDWS 원본 3개 및 train/validation/test Parquet를 준비했다. 사용자는 docs/V2/delivery/xgboost-training-run.md의 systemd-run 명령으로 시작할 수 있다. 해당 명령을 직접 실행하면 Qwen 서비스를 잠시 내리고 학습 종료 후 복구한다. 이번 작업에서 전체 GPU 학습과 Qwen 중단은 실행하지 않았다.

# 검증

- `training/.venv/bin/python -m pytest training/tests`: 15 passed. 실제 tiny 학습·최적 회차 저장·test 미평가·기존 출력 덮어쓰기 거부·GPU 잠금·서비스 복구(성공/실패) 검사.
- Ruff check/format 및 `bash -n training/tools/train_gpu.sh`: 통과.
- 실제 공개 자료의 train/validation 첫 131,072행 CPU 사전 실행: 로컬 4개 트리, GPU 서버 CPU 12개 트리, 각각 저장 후 재로딩 차이 0. 제한 표본이므로 전체 학습 성능으로 해석하지 않는다.
- GPU 서버 원본 SHA256 3개 일치, 11,753,527행 자료 검증 통과. train/test Parquet SHA256은 로컬과 일치. validation은 wind_direction_cos만 바이트 차이가 있고 소수 6자리 반올림 값은 해시 일치, 나머지 19개 입력 및 정답 열 해시 일치. 서버 품질 보고서를 별도로 보존했다.
- systemd 사용자 unit의 `/usr/bin/true` 실행 성공, Linger=yes, 기존 Qwen GPU 잠금이 학습 진입을 거부함을 확인.
- 준비 종료 후 Qwen 서비스 active 및 실제 gpu_client ready 확인. 모델 서빙 환경은 변경하지 않았다.

# 산출물과 제한

문서: docs/V2/delivery/xgboost-training-run.md. 작은 근거: training/reports/{training-cpu-preflight,gpu-dataset-report,gpu-training-readiness}.json. 서버 산출물은 학습 실행 시 data/artifacts/xgboost/ndws-<UTC>-<PID>에 생성된다.

전체 GPU 학습·메모리·시간·최종 성능은 아직 미측정이다. 국내 개인 영향 모델, 확률 보정, 대응 레벨, 운영 배포는 범위 밖이다. 미국 다음 일별 위성 관측 연구 모델로 한정한다. 기존 C1~C5는 완료로 바꾸지 않았다. 다른 작업자의 Qwen 통합 코드를 수정하지 않았다.
