# 산불 XGBoost 학습 자료

첫 CUDA 학습 모델·이력·재평가 사본은 `reports/ndws-20261031T104838Z-528483/`에 있으며, [실제 검증 결과](../docs/V2/delivery/xgboost-training-verification.md)에서 연구용 성능과 사용 한계를 확인할 수 있다.

GPU 서버에서 실제 학습을 시작하는 명령과 로그·결과 확인은 [학습 실행 문서](../docs/V2/delivery/xgboost-training-run.md)를 따른다. 실행기는 `python -m bonghwa_training.train`이며 GPU용 서비스 중지/복구 스크립트는 `training/tools/train_gpu.sh`다.

분석 큐 구현과 독립된 Python 3.12/uv 프로젝트다. 현재 산출물은 실제 공개 관측 자료를 변환한 **미국 NDWS v2 일부 데이터**이며, 국내 개인 영향 예측 모델은 아직 학습·검증하지 않았다.

## 현재 자료

| 구분 | 위치 |
| --- | --- |
| 다운로드 원본 3개, SHA256 manifest | `../data/raw/ndws-v2/` |
| 학습·검증·평가 Parquet와 품질 보고서 | `../data/processed/ndws-v2-bootstrap/` |
| Git에 보존하는 원본 목록·품질 통계 | `reports/source-manifest.json`, `reports/dataset-report.json` |
| 국내 수집 경로 및 입력·정답 판단 | [설계·수집 문서](../docs/V2/delivery/xgboost-training-data.md) |
| 수집 경로별 확보 상태 | `sources/source-audit.json` |

원본과 Parquet는 용량 때문에 Git에서 제외한다. 위 경로는 저장소 루트 기준 명령으로 재생성한다.

## 실행

저장소 루트에서 실행한다. 루트 서비스의 의존성이나 GPU 서빙 환경을 바꾸지 않는다.

```bash
uv sync --project training --frozen
uv run --project training --frozen bonghwa-dataset download \
  --destination data/raw/ndws-v2 --shards-per-split 1
uv run --project training --frozen bonghwa-dataset build \
  --raw data/raw/ndws-v2 --output data/processed/ndws-v2-bootstrap
uv run --project training --frozen bonghwa-dataset verify \
  --output data/processed/ndws-v2-bootstrap
uv run --project training --frozen pytest training/tests
uv run --project training --frozen ruff check training
```

`--all-shards`로 전체 19개 파일(원본 약 3.96 GB)을 확보할 수 있다. 전체 자료는 `data/raw/ndws-v2-full`, `data/processed/ndws-v2-full`처럼 별도 디렉터리에서 생성한다. 현재 보존한 보고서는 첫 파일 3개만의 결과다. 발행 버전이 바뀌면 다운로드를 중단하고 재검토한다.

## 학습 입력 읽기

학습 의존성은 `uv sync --project training --frozen --extra train`으로 설치한다. 아래 코드는 로더 사용 예이며 모델 학습이나 성능 측정을 실행하지 않는다.

```python
from pathlib import Path
import xgboost as xgb
from bonghwa_training.build import FEATURES, iter_training_batches

x, y = next(iter_training_batches(Path("data/processed/ndws-v2-bootstrap/train.parquet")))
batch = xgb.DMatrix(x, label=y, feature_names=list(FEATURES), nthread=2)
```

이 예시는 첫 65,536행만 읽는다. 전체 학습에서는 모든 배치를 순회하는 XGBoost iterator/external memory 또는 서버 메모리에 맞는 로딩을 사용해야 한다. `FEATURES`는 정답, 파일명, 패치 ID, 행·열 인덱스를 제외한 입력 목록이다. 같은 전처리를 추론에도 적용해야 한다.

전체 원본 재생성·해시 비교와 각 분할의 실제 DMatrix 로딩 검사는 다음 명령으로 반복할 수 있다. 임시 재생성 파일은 검사 후 정리하며, 작은 보고서 3개를 `--reports` 경로에 쓴다.

```bash
uv run --project training --frozen --extra train python training/tools/verify_release.py \
  --raw data/raw/ndws-v2 --processed data/processed/ndws-v2-bootstrap \
  --reports training/reports
```

## 출처와 변경

Fantine Huot, R. Lily Hu, Nita Goyal, Tharun Sankar, Matthias Ihme, Yi-Fan Chen, **Next Day Wildfire Spread**. [원본 데이터](https://www.kaggle.com/datasets/fantineh/next-day-wildfire-spread), [논문](https://arxiv.org/abs/2112.02447), [공식 코드](https://github.com/google-research/google-research/tree/master/simulation_research/next_day_wildfire_spread). 데이터 버전 2, CC BY 4.0. 이번 변환은 픽셀 테이블화, 관측 불가 정답 제외, 물리적 입력 QC, 파생 피처 추가와 동일 표본 중복 제거를 수행했다. 원본 저자의 보증이나 국내 적용 승인을 의미하지 않는다.
