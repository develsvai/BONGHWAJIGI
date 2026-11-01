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
