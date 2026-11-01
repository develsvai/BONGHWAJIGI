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
