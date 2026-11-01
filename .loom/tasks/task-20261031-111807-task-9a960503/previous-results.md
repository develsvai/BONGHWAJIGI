# Previous Results

1 older recorded result(s) were omitted. Promote durable context to Job Notes or explicit Context References.

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

## 8. 사용자가 실행한 CUDA 학습 산출물과 독립 재추론 검증

# 결과

사용자가 실행한 `ndws-20261031T104838Z-528483`는 정상 완료했다. 서버 원본 모델·보고서·학습 이력과 사용자 로그를 대조했다. 실제 학습 장치 cuda:0, 3,957,875행·20개 입력, 64회 실행, 최고 validation 회차 index 33과 저장 34개 트리, 이후 30회 개선 없음이 일치한다. 학습·validation 파이프라인 실측은 24.869초이고 wrapper 전체는 약 31초다. 이전 5~10분 예상은 실측보다 길었다.

모델 SHA256 `14a988b3b8e2755c54bc89f82a00d4babee2c3c24970df57df10973112809cb5`가 서버·원본 report·로컬 사본·검증 종료 후 파일에서 일치한다. 재학습이나 설정 변경 없이 CPU로 새로 로딩해 validation 전체 지표를 재현했고, 학습·조기 종료에 사용하지 않은 test를 첫 평가했다.

- validation AP 0.144925, ROC-AUC 0.840350, Brier 0.010346.
- test AP 0.237273, ROC-AUC 0.882856, Brier 0.011377.
- 동일한 이전 관측 유효 행의 AP: validation persistence 0.046246 → 모델 0.145378, test 0.112542 → 0.237916.
- 진단 임계값 0.5: validation 45,096개 화재 관측 픽셀 중 209개 탐지(재현율 0.4635%), test 51,540개 중 12개 탐지(0.0233%). 임계값·확률·대응 정책은 승인하지 않았다.

# 검증과 보존

`training/tools/verify_model.py`의 실제 서버 CLI 실행으로 모델/데이터 SHA256, 피처 순서·정답 계약·최적 회차·트리 수, 전체 Parquet 무결성·행 수·validation 재현·고정 모델 test 평가를 검증했다. Ruff와 Python 구문 검사를 통과했다. 원본 학습 결과는 변경하지 않고 별도 audit.json으로 평가 이력을 남겼다.

모델·원본 report/history/parameters/feature-gain·audit·journal·데이터 보고서·서비스 상태 사본은 training/reports/ndws-20261031T104838Z-528483/에 보존했다. 해석과 재현 명령은 docs/V2/delivery/xgboost-training-verification.md에 기록했다.

Qwen 사용자 서비스 active, 생성·임베딩 실제 ready와 PID 528588의 GPU 상주를 확인했다. 검증은 CPU만 사용했고 GPU 서비스 중단·재시작을 하지 않았다.

# 판단과 제한

이번 자료에서 기준선 대비 순위 예측 개선은 확인했으나 임계값 0.5의 탐지율은 매우 낮다. 모델 학습 완료와 실제 경보/국내 개인 대응원칙 적용 가능성을 분리한다. 확률 보정·국내 외부 검증·입력 시점 가용성·사건/공간 독립성은 미검증이다. 수백만 행은 독립 산불 건수가 아니다. 이 test 결과를 본 뒤 튜닝하면 새로운 최종 평가 자료가 필요하다. 재학습·배포와 기존 C1~C5 완료 처리는 하지 않았다.
