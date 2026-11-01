# 국내 GK2A 첫 미래 화재 관측 연구 자료

2026-11-01 KST에 기존 국내 훈련 창 14개(2020~2022)만으로 구축했다. **위성의 화재 관측을 예측하기 위한 자료이며 실제 첫 발화·화선 도달·개인 피해 정답이 아니다.** 2023 validation/calibration 및 2025 test 원본·정답은 열지 않았다. 모델 학습·평가 결과는 이 디렉터리의 별도 `README.md`에서 다룬다.

성공한 서버 데이터 경로는 `/home1/ncloud/bonghwajigi/data/processed/korea-first-observation-train-20261101-v2`다. 사건별 Parquet 14개와 `config.json`, `plan.json`, 사건별 보고서 및 `report.json`이 있다. [전체 생성 보고서](report.json), [사전 동결 계획](plan.json), [입력·정답 스키마 설정](config.json), [집계·제외 내역](cohort-counts.json)을 함께 보존했다.

## 기존 자료와 달라진 점

기존 v4는 미래 관측이 불명확한 행을 저장하지 않았지만, 불명확 값을 음성으로 채우는 구현은 아니었다. 새 자료는 현재 입력으로 정한 후보를 모두 남긴다. 원래 규칙인 현재 명확 관측 비화재 셀, 현재 화재 관측까지 30km 이내, 20분 입력 간격, 사건당 12시간 창, 관측 시각에 15분을 더한 가정 판단 시각을 유지했다. **후보·이력 집단·환경 입력을 먼저 만들고 미래 정답은 마지막에 붙였다.**

- 전체 **466,710행**: 각 1·3·6시간에 동일한 입력 후보 155,570행씩이다.
- 기존 v4 **315,490행 전부**의 사건·판단 시각·예측 기간·격자 키와 정답이 동일하다. 기본 입력 34개의 NaN 위치도 동일하고 최대 절대 차이는 **0**이다.
- 이전에 저장하지 않았던 **151,220개의 미래 관측 불명확 행**을 `observed_fire_within_horizon=-1`, `target_known=false`로 보존했다.
- 기존 v4 Parquet 및 정답은 변경하지 않았다. 정적 격자와 과거 기상은 새 후보 전체에 다시 계산했다. 정답이 알려진 기존 행의 환경 열만 조인하는 방식은 사용하지 않았다.

행 수는 사건·판단 시각·격자·예측 기간 조합이다. 동일 화재·위치·시간대가 여러 예측 기간과 판단 시각에 반복되므로, 독립 사건 수나 고유 화재 수가 아니다.

## 입력만으로 정하는 두 집단

시간 이력은 판단 시각이 아닌 **마지막 가용 스캔 시각**에서 거슬러 계산한다. 15분 지연 가정 때문에 60분 이력은 판단 시각의 75~15분 전, 120분 이력은 135~15분 전 범위다. 원본은 사건 시작 60분 전부터 확보돼 있다. 120분 이력 전체는 사건 시작 후 충분한 시간이 지난 시점부터만 확보될 수 있다. 파일 간격은 기본 10분이며 일부 사건에 20~30분 누락 간격이 있다.

| 집단 | 입력 시점의 조건 | 각 예측 기간의 후보 수 |
|---|---|---:|
| 주 분석 `cohort_primary_clear60` | 과거 60분의 예정 스캔 7개가 모두 명확 비화재이고, 확보된 과거 120분 스캔에서 화재 관측이 없음 | 134,710 |
| 민감도 분석 `cohort_sensitivity_clear120` | 과거 120분의 예정 스캔 13개가 모두 명확 비화재 | 111,505 |
| 과거 탐지 이력 `history_fire_observed_120m` | 과거 120분에 하나 이상의 화재 관측이 있음 | 454 |

주 분석의 “과거 120분 화재 관측 없음”은 120분 전체가 명확했다는 뜻이 아니다. 주 분석 후보 중 예측 기간마다 **11,814행(8.77%)**은 120분 source 파일 범위가 불완전하다. 이 여부를 `history_120m_source_complete`로 보존하고, 완전한 120분 명확 관측 집단을 별도 민감도 분석에 사용한다. 파일이 없거나 픽셀이 구름·불확실 상태이면 clear로 보간하지 않는다.

## 정답과 관측 불명확 비중

`observed_fire_within_horizon`은 판단 시각 이후 예정된 10분 간격 스캔에 대한 값이다. 확정 화재 관측이 하나라도 있으면 `1`, 예정 스캔이 모두 존재하고 모두 명확 비화재이면 `0`, 그 외에는 `-1`이다. `0`은 연속된 물리적 비화재를 증명하지 않는다. 판단 시각이 10분 스캔 격자 사이에 있으므로 첫 미래 스캔과 마지막 미래 스캔 사이의 공백도 남는다.

| 기간 | 전체 후보 양성 / 음성 / 불명확 | 전체 불명확 비중 | 주 분석 양성 / 음성 / 불명확 | 주 분석 불명확 비중 | 120분 집단 불명확 비중 |
|---|---|---:|---|---:|---:|
| 1시간 | 250 / 130,497 / 24,823 | 15.96% | 117 / 118,374 / 16,219 | 12.04% | 11.50% |
| 3시간 | 603 / 105,293 / 49,674 | 31.93% | 376 / 96,387 / 37,947 | 28.17% | 27.78% |
| 6시간 | 914 / 77,933 / 76,723 | 49.32% | 576 / 71,994 / 62,140 | 46.13% | 46.64% |

기존 양성 **1,767행** 중 주 분석 집단에 남는 양성은 **1,069행**이다. 아래 제외 사유는 겹치지 않게 분해했다. 과거 120분 화재 관측이 있으면 첫 번째 제외 항목으로 분류하고, 그 이력이 없으면서 60분 명확 관측 조건을 충족하지 못하면 두 번째로 분류한다. 불명확한 과거 때문에 제외된 행을 비화재로 바꾸지 않는다.

| 기간 | 기존 양성 | 주 분석 양성 | 과거 120분 탐지 이력으로 제외 | 120분 탐지 이력은 없으나 60분 명확 이력이 부족해 제외 |
|---|---:|---:|---:|---:|
| 1시간 | 250 | 117 | 64 | 69 |
| 3시간 | 603 | 376 | 98 | 129 |
| 6시간 | 914 | 576 | 110 | 228 |
| 합계 | **1,767** | **1,069** | **272** | **426** |

“탐지 이력이 있음”은 같은 물리적 불이 지속 또는 재발했다는 현장 검증을 뜻하지 않는다. 반대로 주 분석 집단도 처음 발화한 위치라고 단정할 수 없다. 위성의 비탐지·구름·격자 해상도와 확인 가능한 과거 범위의 한계가 있다.

## 스키마와 입력 누출 방지

`config.json`의 `feature_names` 및 `input_feature_allowlist`만 학습 입력으로 사용한다. 기본 34개에 아래 12개를 추가하여 총 46개다. 기존 `closing_speed_*` 열은 보존했다.

- `actual_history_30m_minutes`, `actual_history_60m_minutes`: 실제 현재/과거 스캔 간격. 예를 들어 완전한 10분 cadence와 15분 가정 지연에서는 기존 30·60분 조회가 실제로 20·50분 간격의 스캔을 선택한다.
- `actual_closing_speed_30m_kmh`, `actual_closing_speed_60m_kmh`: 해당 실제 간격으로 나눈 거리 변화. 가장 가까운 화재 관측이 바뀔 수 있어 물리적 화선 전파 속도가 아니다.
- `history_{60,120}m_{clear_count,fire_count,unknown_count,source_coverage_fraction}`: 당시 가용한 스캔만 사용하는 이력 값. 누락된 예정 파일도 unknown으로 센다.

미래 진단 열은 모두 `audit_` 접두사로 분리했다. 정답·`target_known`·cohort flag·`audit_*`·`survival_training_eligible`은 feature allowlist에 없다. 특히 `audit_blind_gap_fire_observed`는 마지막 가용 스캔과 판단 시각 사이에 관측됐으나 당시에는 아직 가용하지 않았던 스캔의 사후 진단이다. **입력·cohort 선정·후보 제외에 사용하지 않는다.** 주 분석에서 이 값이 참인 입력 후보는 예측 기간마다 15행이고, 세 기간에 같은 입력 후보가 반복된다.

`audit_first_future_fire_observed_*`는 첫 미래 **화재 관측** 시각이다. `audit_observation_transition_lower/upper_*`는 마지막 명확 비화재 관측과 첫 미래 화재 관측의 구간을 보존한다. lower가 판단 시각 이전이면 음수 lead를 그대로 남긴다. 중간에 관측 불명확 상태가 있어도 물리적 상태 변화 시각을 보장하지 않는다. `audit_contiguous_clear_followup_*`는 **판단 시각 이후 예정 스캔만** 대상으로 첫 unknown/fire에서 멈추며, 뒤의 clear로 공백을 메우지 않는다. 판단 전 15분 blind gap은 이 보조 follow-up 계산에 포함하지 않는다.

이 구간과 censor audit는 생존 모형의 엄밀한 도달 시각 정답이 아니다. 모든 행과 설정에 `survival_training_eligible=false`, `operational_use=false`를 유지했다. 재처리 위성 자료와 사후 QC 기상으로 만든 hindcast이며, 가정 지연은 당시 실제 수신 시각의 증거가 아니다.

## 추가 입력의 실제 변동 감사

[별도 입력 감사](feature-variation.json)는 train 14개 Parquet의 `cohort_primary_clear60` 및 추가 입력 12개 열만 읽었다. 미래 정답·미래 audit 열은 읽지 않았다. 데이터셋 SHA를 확인하고 주 분석 **404,130행**에서 유효 최솟값·최댓값·고유값 수·결측을 집계했다. 같은 입력이 세 예측 기간에 반복되어 있으며, 아래 수를 독립 표본 수로 해석하지 않는다. 코드와 데이터셋은 이 감사로 변경하지 않았다.

| 추가 열 | 주 분석의 유효 범위 | 유효 고유값 수 | 결측 행 수 |
|---|---|---:|---:|
| `actual_history_30m_minutes` | 20만 존재 | 1 | 0 |
| `actual_history_60m_minutes` | 50만 존재 | 1 | 0 |
| `actual_closing_speed_30m_kmh` | −81.180 ~ 157.416 | 39,198 | 17,316 (4.28%) |
| `actual_closing_speed_60m_kmh` | −31.678 ~ 65.426 | 41,171 | 29,973 (7.42%) |
| `history_60m_clear_count` | 7만 존재 | 1 | 0 |
| `history_60m_fire_count` | 0만 존재 | 1 | 0 |
| `history_60m_unknown_count` | 0만 존재 | 1 | 0 |
| `history_60m_source_coverage_fraction` | 1만 존재 | 1 | 0 |
| `history_120m_clear_count` | 7 ~ 13 | 7 | 0 |
| `history_120m_fire_count` | 0만 존재 | 1 | 0 |
| `history_120m_unknown_count` | 0 ~ 6 | 7 | 0 |
| `history_120m_source_coverage_fraction` | 약 0.538462 ~ 1 | 5 | 0 |

**12개 열이 12개의 독립적인 새 정보를 뜻하지 않는다.** 주 분석 조건 때문에 7개 열은 상수다. 실제 간격이 항상 20·50분이므로 보정된 두 거리 변화율은 기존 식의 각각 1.5배·1.2배에 해당하는 재표현이다(저장된 float32 반올림 차이는 별개). 기왕의 입력에 없던 새로운 화재 동역학 측정이 아니다. 120분 clear와 unknown 개수의 합은 모든 주 분석 행에서 13으로, 이 두 열도 중복 정보다.

실제로 추가되는 이력 정보는 주로 **120분의 명확 관측 개수와 source 파일 확보 비율**이다. 이 둘은 관측 가용성·구름 등에 관한 정보이며 물리적 확산을 직접 설명하는 변수가 아니다. 보정 거리 변화율의 큰 값 역시 최근접 탐지 위치 변경을 포함하므로 실제 화선 속도로 해석하지 않는다. 입력 감사 결과만으로 성능 향상을 주장하지 않으며, 모델 비교는 별도의 동결된 평가 결과로 판단한다.

## 실행과 감사

생성기: [`korea_first_observation.py`](../../src/bonghwa_training/korea_first_observation.py). 테스트: [`test_korea_first_observation.py`](../../tests/test_korea_first_observation.py). 시간 순서, 누락 파일·구름, 첫 양성, 판단 전 음수 lower, future/blind-gap 입력 비개입, 실제 사건 생성 함수의 기존 행 재현을 포함한 **9개 테스트**와 lint가 통과했다.

서버 프로젝트 `/home1/ncloud/bonghwajigi`에서 새 출력 경로로만 실행한다. 완료된 디렉터리는 덮어쓰지 않는다.

```bash
FIRST_OBSERVATION_OUTPUT=data/processed/korea-first-observation-train-new-run
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 PYTHONPATH=training/src
training/.venv/bin/python -m bonghwa_training.korea_first_observation \
  --raw data/raw/korea-wildfire/gk2a-ff \
  --weather-raw data/raw/korea-wildfire \
  --static data/processed/korea-hindcast-v2 \
  --reference data/processed/korea-gk2a-context-v4 \
  --config training/configs/korea-gk2a-context-v4.json \
  --output "$FIRST_OBSERVATION_OUTPUT" --plan-only

training/.venv/bin/python -m bonghwa_training.korea_first_observation \
  --raw data/raw/korea-wildfire/gk2a-ff \
  --weather-raw data/raw/korea-wildfire \
  --static data/processed/korea-hindcast-v2 \
  --reference data/processed/korea-gk2a-context-v4 \
  --config training/configs/korea-gk2a-context-v4.json \
  --output "$FIRST_OBSERVATION_OUTPUT" --build-frozen
```

첫 시도 `korea-first-observation-train-20261101`는 context 함수에 필요한 현재 화재 dx/dy 열을 전달하지 못해 첫 사건에서 실패했다. 원본과 기존 v4 자료는 변경되지 않았다. [실패 기록](failed-attempt-v1/failure.json)과 당시 동결 계획을 보존했다. base geometry를 원래 v4와 동일하게 float32로 전달하고 실제 생성 함수 통합 테스트를 추가한 뒤, 새 `-v2` 디렉터리에 계획을 다시 동결하여 성공했다.

원본·기존 참조자료·기상·정적 격자·코드·계획 **1,776개 경로의 SHA를 생성 완료 직전에 재검사**했다. 실제 dataset Parquet별 SHA는 [전체 보고서](report.json)에 있다. 아래 값은 로컬에 회수한 파일과 동일하다.

| 항목 | SHA-256 |
|---|---|
| 성공 계획 `plan.json` | `170a1f4008de6160d0c7e514895daa78fcd568ca7fb12c0502d7316b024f3a38` |
| 성공 설정 `config.json` | `5b89472738b19e88ee5683ef31ed79191e4f559d58ae71b59d917afcbdfe5107` |
| 성공 보고서 `report.json` | `d067bb9491faeacbe1cece1a9ba615f89a0882aae90760941bfbe749c76fffa8` |
| 기존 정적 격자 | `e31c0ed8bc1df421f6201b0aca0af0ea1f9e52b1a878d3fa93cfeb0086f9c60a` |
| 기존 기상 관측소 목록 | `df0645691d7c1ff7d7457b46b16636f37cce73b98f3a908c20428b230d1f8927` |

이번 작업에서 외부 API를 호출하거나 추가 원본을 수집하지 않았다. 기존 KMA GK2A FF, ISD 기상, 정적 격자의 이용 조건은 [기존 외부 자원 문서](../../../docs/V2/delivery/external-resources-and-licenses.md)를 따른다. 데이터셋 정합성 향상만으로 국내 사용자 위험 확률의 유효성이 입증되지는 않는다.
