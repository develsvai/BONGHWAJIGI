# 산불 XGBoost 학습 자료

국내 1·3·6시간 목표에 대한 원인 진단, 실제 GOES GPU 비교·독립 평가, 기상청 FF 연결과 국내 검증 진행은 [국내 산불 모델 개선 기록](../docs/V2/delivery/korea-wildfire-improvement.md)을 따른다. 국내 FF 715개를 사용한 v2·v3 학습을 완료했고, v4는 21개 지역 창으로 수집·후속 학습을 진행 중이다. 현재 결과는 연구용이며 개인 대응 판단에 적용하지 않는다.

v3의 홍성 튜닝 AP는 1·3·6시간 각각 **0.0336/0.0334/0.0488**로 v2보다 소폭 개선됐지만, 양성 가중 모델의 Brier 점수는 악화됐다. AP는 분류 정확도가 아니며 원점수를 확률로 해석할 수 없다. 독립 보정 검증과 국내 최종 평가는 아직 남아 있다. v4의 학습 14·튜닝 6·보정 1은 요청 지역 창 수이며 독립 사건 수나 유효 표본 수가 아니다.

첫 CUDA 학습 모델·이력·재평가 사본은 `reports/ndws-20261031T104838Z-528483/`에 있으며, [실제 검증 결과](../docs/V2/delivery/xgboost-training-verification.md)에서 연구용 성능과 사용 한계를 확인할 수 있다.

기존 NDWS GPU 학습은 [학습 실행 문서](../docs/V2/delivery/xgboost-training-run.md)를 따른다. 실행기는 `python -m bonghwa_training.train`, GPU용 서비스 중지/복구 스크립트는 `training/tools/train_gpu.sh`다. 국내 시간별 학습은 `bonghwa_training.goes_train`과 `training/tools/train_hourly_gpu.sh`를 사용하며 설정·재현 명령은 위 개선 기록에 있다.

분석 큐 구현과 독립된 Python 3.12/uv 프로젝트다. 미국 NDWS 일별·GOES 시간별 자료와 국내 GK2A 시간별 관측 자료를 다룬다. 국내 모델의 정답은 미래 위성 화재 관측이며 개인 피해나 대응 단계가 아니다. 원본·Parquet·국내 모델은 GPU 서버 `/home1/ncloud/bonghwajigi` 아래에 보관한다. 인증키와 승인 사용자용 KMA 원본은 Git에 넣지 않는다.

## 현재 자료

| 구분 | 위치 |
| --- | --- |
| 다운로드 원본 3개, SHA256 manifest | `../data/raw/ndws-v2/` |
| 학습·검증·평가 Parquet와 품질 보고서 | `../data/processed/ndws-v2-bootstrap/` |
| Git에 보존하는 원본 목록·품질 통계 | `reports/source-manifest.json`, `reports/dataset-report.json` |
| 국내 FF 원본과 현재 제품 메타데이터 | `../data/raw/korea-wildfire/gk2a-ff/`, `../data/raw/korea-wildfire/gk2a-live/` |
| 국내 v3 기본·환경 결합 Parquet | `../data/processed/korea-gk2a-hourly-v3/`, `../data/processed/korea-gk2a-context-v3/` |
| 국내 v2·v3 실제 학습·품질 보고서 | `reports/kma-audit-20261031/`, `reports/kma-recent-audit-20261031/` |
| 공식 위경도 조견표 대조 | `reports/kma-audit-20261031/projection-audit.json` |
| 현재 FF 수신·알고리즘 메타데이터 | `reports/kma-audit-20261031/live-metadata/` |
| 국내 수집 경로 및 입력·정답 판단 | [설계·수집 문서](../docs/V2/delivery/xgboost-training-data.md) |
| 수집 경로별 확보 상태 | `sources/source-audit.json` |

원본과 Parquet는 Git에서 제외한다. 현재 제품은 2026-10-31 22:40 KST 관측을 22:46:16에 수신했으나, 과거 재처리본과 알고리즘 버전이 달라 실시간 성능 검증은 별도로 필요하다. 공식 900×900 위경도 조견표와 현재 투영 계산의 대조는 완료했다.

`python -m bonghwa_training.prediction_evidence`로 과거 원본에서 당시 후보 전체의 1·3·6시간 점수·좌표·관측 근거·누락을 JSON/GeoJSON으로 내보낼 수 있다. [실제 출력 예시](reports/kma-recent-audit-20261031/replay/summary.json), [실행법](../docs/V2/delivery/korea-wildfire-improvement.md#예측-자료를-활용할-경계)을 참고한다. 홍성 재생 739개 후보와 기존 입력 일치를 확인했다. `bonghwa_training.ranking_audit`는 같은 시점 안에서 모델·현재 거리·최근 거리 기준의 검토 효율을 비교한다. 현재 모델이 최근 화재 거리 기준보다 확실히 우수하지 않아 세 기준을 계속 비교한다.

내부 API는 단일 모의 확률만 지원하고 앱은 예측 연결을 비활성화하므로, 연구 산출물 생성과 앱·개인 정책 연결은 별도다. v4 완료 후 `bonghwajigi-kma-utility-v4` 작업이 사건별 평가·재생 자료를 `data/artifacts/xgboost/kma-utility-v4/`에 자동 생성한다. 2025년 최종 정답은 열지 않는다.

## 기존 NDWS 자료 재현

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
