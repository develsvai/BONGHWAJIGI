# 국내 산불 1·3·6시간 모델 개선 기록

2026-10-31 KST. Loom: `task-20261031-111807-task-9a960503`.

**국내 사용자 대응 판단에 사용할 수준은 아직 검증되지 않았다.** 국내 FF 6개 지역 창으로 v2·v3를 실제 GPU에서 학습했다. 최근 화재 관측 이력을 추가한 v3의 순위 성능은 조금 개선됐지만 확률 품질은 나빠졌다. 현재 v4는 21개 지역 창으로 수집·학습 범위를 넓히는 중이다. 모든 산출물의 `operational_use`는 `false`다.

## 목표와 역할

- 사용자 확정 목표: 국내 사용자의 앞으로 1~6시간 산불 영향·접근 위험.
- 현재 학습 가능한 좁은 정답: 현재 비화재로 관측되는 육지 격자에서 향후 1·3·6시간 내 위성의 확실한 화재 관측이 생기는지.
- 위성 관측 확률은 실제 화선 도달, 개인 피해, 연기 노출, 대피 필요성의 확률과 다르다. 관측 불가를 안전으로 해석하지 않는다.
- 프로필·이동 제약·보호 대상·기본 대응 지침은 검토된 개인 정책 조합의 입력이다. 화재 관측 정답 대신 XGBoost에 넣지 않는다. Qwen의 설명 생성도 부족한 정답·검증을 대체하지 못한다.
- 공식 경보는 이 모델을 기다리지 않는 우선 경로다. 대응 단계와 알림 방식은 별도 [정책 계약](response-policy.md)을 따르며 이 연구에서 정하지 않는다.

## 기존 모델의 원인 진단

기준 모델: `ndws-20261031T104838Z-528483`, SHA256 `14a988b3b8e2755c54bc89f82a00d4babee2c3c24970df57df10973112809cb5`.

검증 양성 비율은 1.1335%, AP는 0.144925였다. 임계값 0.5에서 precision은 39.07%지만 recall은 **0.463%**라 대부분의 양성을 놓친다. AP는 분류 정확도가 아니다.

| 검증 임계값 | Precision | Recall | 비화재 표본의 오경보율(FPR) |
| --- | ---: | ---: | ---: |
| 0.01 | 7.17% | 59.55% | 8.85% |
| 0.05 | 16.43% | 40.95% | 2.39% |
| 0.10 | 20.56% | 31.81% | 1.41% |
| 0.50 | 39.07% | 0.46% | 0.0083% |

[검증 표본만의 임계값 진단](../../../training/reports/threshold-diagnosis.json). 임계값을 낮추면 누락과 함께 오경보가 증가한다. 64회 실행 중 검증 최적은 34개 트리였고 이후 학습 점수만 좋아졌다. 학습 시간을 늘리는 것만으로 해결되지 않는다. 미국·일별 관측·첫 shard 일부라는 자료 범위도 국내 1~6시간 목표와 다르다. 기존 test00은 이미 평가했으므로 새로운 개선의 미사용 최종 평가로 재활용하지 않았다.

## 실제 확보한 자료와 저장 위치

GPU 프로젝트 루트는 `/home1/ncloud/bonghwajigi`다. 원본·Parquet는 Git에서 제외하며 각 파일의 SHA, 출처, 관측 시각, 제작/수신 정보와 누락을 별도로 남긴다.

| 자료 | GPU 경로 | 확보/용도 |
| --- | --- | --- |
| 국내 MODIS FireMask/QA/MaxFRP | `data/raw/korea-wildfire/fire/` | 2018~2024와 2025 일부. 2025는 원본 확보·메타데이터 확인만 수행 |
| 국내 VIIRS 국가별 연간 CSV | `data/raw/korea-wildfire/firms/` | 2018~2024, 14개, 9,581,988 bytes. 관측점의 부재를 음성으로 쓰지 않음 |
| 국내 ISD-Lite 시간 기상 | `data/raw/korea-wildfire/weather/` | 2018~2025, 연도별 누락 목록 포함. 사후 QC 자료 |
| 토지피복·지형·국가 경계 | `data/raw/korea-wildfire/static/`, `boundary.geojson` | CCI 2015 한국 창, Copernicus DSM90 44타일, 공개 경계 |
| 국내 일별 자료 감사 | `data/processed/korea-hindcast-v2/` | 2018~2024 실제 Parquet. 1~6시간 모델의 대체 자료가 아님 |
| 공개 GOES 5분 원본 | `data/raw/goes-hourly/` | 6개 사건, 2,135개, 903,057,983 bytes |
| GOES 학습/튜닝/보정 | `data/processed/goes-hourly-v3/` | 학습 3개 사건, 튜닝 1개, 보정 1개 |
| GOES 최종 평가 | `data/processed/goes-hourly-final-v1/` | 고정 후 수집·열람한 Smith River 2023 사건 1개 |
| 국내 GK2A FF | `data/raw/korea-wildfire/gk2a-ff/` | v2·v3 기준 715개, 437,469,041 bytes, 누락 5시각. v4 추가 수집 중 |
| 국내 시간별 v3 | `data/processed/korea-gk2a-hourly-v3/`, `korea-gk2a-context-v3/` | 과거 60분 화재 이력과 지형·기상을 결합한 실제 Parquet |

[확보 목록의 해시와 크기](../../../training/reports/improvement-audit-20261031/inventory.json), [국내 일별 품질 보고서](../../../training/reports/improvement-audit-20261031/korea-daily/report.json).

국내 일별 자료는 현재 화재 근처의 산림 격자만 대상으로 한 제한 표본이다. 2018~2024의 양성 수는 각각 59/80/114/7/591/22/6개다. 2024년의 6개 양성으로 안정적인 확률 보정을 주장할 수 없다. 일별 자료에 시간별 정답을 만들어 붙이지 않았으며 별도의 일별 모델 학습도 실행하지 않았다.

국내 MODIS의 STAC 항목 시각과 내부 제작 정보가 다른 사례가 있어 내부 `Dates`, 실제 `PRODUCTIONDATETIME`을 기준으로 정합화했다. 원본 격자는 명목 1km와 달리 약 926.625m sinusoidal 격자다. 한국 위치에서의 전단 때문에 격자 수×픽셀 폭으로 지상 거리를 계산하지 않고 국내 미터 좌표계에서 거리·경사를 계산한다. 기상 누락은 0으로 채우지 않으며, 관측된 강수량 합은 하루 총강수량이 아니다.

일별 설정의 초기 `frozen_before_label_inspection` 표기는 자료 구조 설계의 초기 의도이며, 이후 파일 가용성·양성 수를 보고 VIIRS 병합과 분할 계획을 수정한 탐색 과정 전체가 사전 등록됐다는 뜻으로 해석하면 안 된다. 사용한 당시 설정과 해시는 보고서 사본에 보존한다. 이 자료의 성능을 최종 사전 등록 평가로 제시하지 않는다.

## GOES 시간별 실제 비교 결과

모든 시점·격자·기간을 사건 단위로 분리했다. 현재 비화재 육지이며 관측 화재에서 30km 이내인 후보만 평가한다. 미래 고신뢰 화재가 있으면 양성, 미래 5분 관측이 전부 존재하고 모두 명백한 비화재일 때만 음성이다. 나머지는 검열한다. 입력에는 발행 proxy 이전에 공개된 관측만 사용한다. proxy는 실제 시스템 수신 이력과는 다르다.

| 분할 | 사건 | 행 수 | 양성 수 |
| --- | --- | ---: | ---: |
| 학습 | Dixie/Bootleg/Caldor | 255,478 | 3,976 |
| 튜닝 | Mosquito | 147,367 | 1,221 |
| 보정 | Oak | 119,578 | 500 |
| 최종 평가 | Smith River | 105,758 | 1,114 |

| 튜닝 AP | 1시간 | 3시간 | 6시간 |
| --- | ---: | ---: | ---: |
| 현재 공간 정보, depth 3 | 0.1625 | 0.3101 | 0.4086 |
| 과거 30·60분 정보 추가, depth 3 | 0.3396 | 0.4142 | 0.5111 |
| 과거 정보 추가, depth 5 — 선택 | 0.3374 | 0.4517 | 0.5079 |
| 양성 가중, depth 4 | 0.2764 | 0.4203 | 0.5103 |

튜닝 사건의 기간별 AP 평균으로 선택했다. 공통 기간 입력에 단조 제약을 걸어 동일 상황에서 1시간보다 6시간 누적 관측 확률이 낮아지지 않게 했다. 선택 모델은 49개 트리, SHA256 `d21c26f5ddbaaffcb9581016e2481b421f650a4f3380caecd8687adbc323cd72`다. 4개 비교는 실제 CUDA에서 4.49초 소요했다. 데이터 수집·품질 검사가 학습보다 오래 걸린다. 저장 모델의 CPU 재로딩 일치도와 기간 단조성을 검사했다.

모델·보정·튜닝 임계값·설정을 먼저 [고정](../../../training/reports/improvement-audit-20261031/hourly/frozen-release.json)하고, 그 뒤에 최종 사건 원본을 수집했다.

| 미사용 사건 AP | 1시간 | 3시간 | 6시간 |
| --- | ---: | ---: | ---: |
| 거리 기준선 | 0.0381 | 0.0945 | 0.1895 |
| 선택 모델 | 0.1426 | 0.1969 | 0.3390 |

튜닝에서 FPR 약 1%가 되도록 정했던 임계값을 그대로 적용한 최종 사건의 recall은 31.51%/21.63%/22.22%, precision은 17.69%/26.10%/53.13%다. 여전히 누락이 크다. FPR과 '경보 중 오경보 비율'은 다른 지표다. 같은 픽셀의 반복 예측을 독립 사용자 경보 수로 해석하지 않는다.

Oak 1개 사건의 sigmoid 보정은 최종 사건에서 logloss를 전 기간 악화시켰다. 보정이 성공했다고 판단하지 않는다. 미사용 사건 결과를 본 뒤 이 사건에 맞춰 다시 튜닝하지 않았다. 국내 결과와의 직접적인 성능 비교도 하지 않는다.

원본 [학습 보고서](../../../training/reports/improvement-audit-20261031/hourly/report.json), [독립 평가](../../../training/reports/improvement-audit-20261031/hourly/final-evaluation.json), 4개 모델과 이력은 같은 보고서 디렉터리에 있다. GPU 실행 원본은 `data/artifacts/xgboost/hourly-20261031T125336Z-542399/`다. Qwen 생성·임베딩 모델은 학습 후 모두 `ready` 확인했다.

## 국내 FF 연결과 검증 경계

사용자 제공 인증키는 GPU의 `~/.config/bonghwajigi/training.env`에 권한 600으로 저장했다. 키를 저장소·다운로드 URL 기록·로그에 넣지 않는다. 실제 허용된 API는 다음 경로다.

```text
GET https://apihub.kma.go.kr/api/typ05/api/GK2A/LE2/FF/KO/data
date=YYYYMMDDHHMM  (UTC), authKey는 요청할 때만 메모리에서 추가
```

사용자가 전달한 `CI/ELA`는 대류운 발생 탐지 예시다. 실제 수집은 `FF/KO`로 바꿨다. `typ01` FF 경로는 이 키에서 403, `typ05` FF/KO는 200과 실제 NetCDF가 확인됐다. 404 시각은 누락으로 기록한다.

실제 2022-03-04 00:00 UTC 응답은 900×900, 2km LCC 격자, `FF`, `DQF_FF`를 담는다. 원본 내부에는 `file_creation_time=2022-11-03`, `processing_environment=reprocess`가 있어 당시 입력 가용 시각의 증거로 쓸 수 없다. 원본 파일명의 `ela020ge`와도 달리 실제 투영 변수는 Lambert다. WGS84 LCC 계산을 공식 모서리와 확인한 뒤 **공식 900×900 위경도 조견표 전체와 대조**했다. 최대 차이는 위도 0.00000691°, 경도 0.00001261°였다. [투영 대조 기록](../../../training/reports/kma-audit-20261031/projection-audit.json)에 출처와 SHA를 보존한다. 참고 PDF의 구면 반경 표기는 이 좌표와 불일치해 채택하지 않았다.

현재 제품도 메타데이터만 확인했다. **2026-10-31 22:40 KST 관측을 22:46:16에 수신**했고 HTTP 200, `processing_environment=operation`, 제작 시각 22:43:14였다. [수신 기록](../../../training/reports/kma-audit-20261031/live-metadata/probe-20261031T1340.json)의 알고리즘은 `GK2A_FF_v1.2024.01.3`으로, 과거 재처리본의 `GK2A_FF_v1.2022.02.3`과 다르다. 이 한 번의 확인은 해당 시점의 다운로드 가능성을 보여주며 최초 공개 지연이나 모든 시점의 수신 성능을 보장하지 않는다. 현재 제품의 픽셀 정답은 이 확인에 사용하지 않았다.

공식 ATBD 표 2.9 기준 `FF=1,DQF=8/9`만 양성, `FF=0,DQF=2`만 관측 비화재 육지로 읽는다. 구름·물·도심/배제·저신뢰·산업열·fill을 비화재로 바꾸지 않는다. 원본 파일의 `FF=0`만 보고 안전으로 판정하지 않는다.

국내 v1은 안동 2020/2021, 합천 2022, 울진 2022를 학습, 강릉 2023을 튜닝, 홍성 2023을 보정으로 정했다. 실제 구축 뒤 강릉의 6시간 구획은 양성 4개·음성 0개여서 검사가 학습을 중지했다. 이 자료 품질을 본 뒤 **v2는 홍성을 튜닝, 강릉을 보정 부족 진단으로 바꾼 탐색 재설계**다. 모델 성능을 본 뒤 사건을 바꾼 것은 아니지만, 정답을 전혀 보기 전 고정한 정식 최종 평가라고 주장하지 않는다. 강릉 보정은 총 양성12/390행으로 부족하다. 2025년 최종 관측은 계속 잠근다.

원본 제작/수신 시간이 늦으므로 **관측 시각+15분이라는 명시적인 실험 가정**으로 과거 관측을 재현한다. Parquet 각 행의 `input_time_basis=assumed_delay_not_actual_release`로 실제 공개 시각과 구분한다. 이 실험의 좋은 점수도 실시간 성능을 입증하지 않는다.

환경 결합 단계는 기확보 DSM/CCI의 고도·경사·산림 비율, 과거 기온·습도·풍속·풍향 성분·관측 강수, 관측소 거리·관측 나이, 화재에서 대상 위치로 향하는 바람 성분을 추가했다. ISD-Lite의 반올림 시각을 고려해 입력보다 최소 1시간 이전 자료만 조회하고 3시간보다 오래된 관측은 제외한다. 100km 내 가까운 관측소 중 사용 가능한 과거 바람을 선택한다. 강수 누락은 0mm로 채우지 않는다. 바람 방향은 진북 기준의 측지 방위각과 결합한다. 이 기상도 사후 QC 자료이므로 실제 당시 가용성을 입증하지 않는다. 약 1km 정적 감사 격자의 최근접 값은 정확한 2km 연료/지형 평균과 다르다.

원본 수집 도중 HTTP 429로 한 번 중단됐다. 429를 자료 누락으로 기록하지 않고 요청 간격을 3초로 늘렸으며 `Retry-After`와 제한된 지수 대기를 적용했다. 계속 제한되거나 긴 중지가 요구되면 자동 수집을 종료한다. SHA로 확인된 캐시부터 재개한다.

## 국내 v2·v3 결과와 v4 진행

두 실험의 학습은 4개 지역 창 135,495행·양성 1,001개, 튜닝은 홍성 65,386행·양성 463개다. v3는 최근 60분의 확정 화재 위치·마지막 관측 후 경과 시간 등 7개 입력을 추가했다. [동일 표본 검사](../../../training/reports/kma-recent-audit-20261031/base/cohort-verification.json)로 v2·v3의 행·정답·기존 입력이 같음을 확인했다. 과거에 탐지된 화재가 현재도 연소 중이라고 가정하지 않는다.

| 홍성 튜닝 AP | 1시간 | 3시간 | 6시간 |
| --- | ---: | ---: | ---: |
| 거리 기준선 | 0.0194 | 0.0248 | 0.0320 |
| v2 선택 `context_depth5` | 0.0304 | 0.0317 | 0.0462 |
| v3 선택 `history_weighted` | 0.0336 | 0.0334 | 0.0488 |

**AP는 양성 관측을 앞에 놓는 순위 지표이며 분류 정확도나 개인 피해 확률이 아니다.** v3는 소폭 나아졌지만 양성 가중 학습의 원점수를 확률로 해석할 수 없다. 낮을수록 좋은 Brier 점수는 v2의 0.00398/0.00878/0.01051에서 v3의 **0.01562/0.03095/0.04246**으로 악화됐다. 학습 양성 비율만 내는 상수 기준선은 0.00397/0.00785/0.00929다. 두 모델 모두 독립 보정 검증이 없고, 강릉의 보정 양성 12개로는 보정을 적합하지 않았다. 2025년 최종 관측은 미열람 상태다.

[v2 보고서](../../../training/reports/kma-audit-20261031/run/report.json)는 GPU `data/artifacts/xgboost/hourly-20261031T134134Z-547531/`, [v3 보고서](../../../training/reports/kma-recent-audit-20261031/run/report.json)는 `data/artifacts/xgboost/hourly-20261031T135808Z-549349/`에 대응한다. 실제 CUDA 비교 시간은 각각 5개 후보 13.896초, 7개 후보 23초다. v3 선택 모델 SHA는 `c385777857e34a6b8692772bb4efe3713313041037e35531e496fa6472937d33`이다. CPU 재로딩·기간 단조성을 확인했고, 학습 종료 후 Qwen 생성·임베딩 모델이 모두 준비됐음을 확인했다.

[거리별 진단](../../../training/reports/kma-audit-20261031/distance-strata.json)에서 홍성 양성의 현재 탐지점까지 거리 중앙값은 기간별 약 16~17km였다. 새 발화, 가려졌던 화재의 재관측, 다른 화재 등의 가능성을 아직 구분하지 못했다. 이 정답을 순수한 화선 이동으로 해석할 수 없는 원인이다.

현재 **v4 수집과 후속 학습 작업을 실행 중**이다. [설정](../../../training/configs/korea-gk2a-hourly-v4.json)은 학습 14·튜닝 6·보정 1의 총 21개 비시험 지역 창이다. 기존 6개에 15개 창을 추가하며, 수집 성공 후 구축·환경 결합·GPU 비교를 순서대로 수행한다. 같은 시기 산불은 기상을 공유하므로 21개 독립 사건이라고 세지 않는다. 관측 불가 창은 0행으로 남기고 실제 사용 가능한 창 수를 보고한다. v2·v3를 본 뒤 확장한 탐색 실험이며 새로운 사전 등록 최종 검증은 아니다.

```bash
journalctl --user -u bonghwajigi-kma-profile-acquire-v4 -f
journalctl --user -u bonghwajigi-kma-research-v4 -f
```

## 예측 자료를 활용할 경계

우선 **과거 사건 재생, 같은 시점·기간의 격자 우선순위 비교, 추가 자료 확인 대상 선정**에 활용한다. 점수와 함께 관측 화재 거리, 과거 거리 변화, 마지막 관측 시각, 구름·누락, 기상 관측소 거리·나이, 모델·자료 해시를 전달한다. 거리 변화는 화선 속도나 도달 예정 시각으로 이름 붙이지 않는다. 서로 다른 모델·지역·시점의 점수를 공통 위험 등급으로 비교하지 않는다.

별도 연구용 [출력 도구](../../../training/src/bonghwa_training/prediction_evidence.py)를 구현하고 GPU 서버에서 CPU 추론으로 검증했다. JSON에 1·3·6시간의 `raw_model_score`, `calibrated_probability=null`, `operational_use=false`, 적용 범위와 자료 부족 사유를 보존한다. 같은 시점·기간 안의 순위와 확인된 관측을 설명하는 고정 문장을 함께 제공한다. Qwen용 근거 자료로 인계할 수 있지만 현재 Qwen·정책 큐에 자동 투입하지는 않는다.

학습 Parquet는 미래 관측으로 정답을 확인할 수 있는 행만 담는다. 재생 도구는 **미래 정답 유무와 무관하게 그 시점까지의 원본 입력으로 모든 후보를 만든다.** 미래 관측 파일은 픽셀을 열기 전에 제외하며, 같은 격자의 1·3·6시간 점수는 같은 과거 입력에서 기간만 바꿔 계산한다. 관측 불가·범위 밖은 0점이나 안전 대신 예측 불가로 남긴다. 학습 정답의 관측 선택 편향은 여전히 남으므로 전체 후보에 대한 성능이 입증됐다는 뜻은 아니다.

홍성 2023-04-02 06:15 UTC 재생은 영역 내 1,322개 격자 중 739개에 연구 점수를 산출했다. 관측 불가 283개, 현재 화재 관측 7개, 후보 거리 범위 밖 293개는 이 미래 비화재→화재 모델의 점수를 부여하지 않았다. 현재 화재를 관측한 위치는 `CURRENT_FIRE_OBSERVED`로 보존한다. [출력 예시](../../../training/reports/kma-recent-audit-20261031/replay/summary.json), [검증 증거](../../../training/reports/kma-recent-audit-20261031/replay/verification.json)에서 기존 학습 자료의 해당 시각 2,186행과 모든 선택 피처가 정확히 일치함을 확인했다. 이 대조는 출력 생성 후 별도 검사에서만 Parquet를 읽었으며 재생 생성기는 읽지 않는다.

GPU의 `data/artifacts/xgboost/evidence-hongseong-v3-20230402T0615Z-v2/`에 다음 파일이 있다.

| 파일 | 용도 |
| --- | --- |
| `evidence.json` | 모든 격자의 관측 상태·기간별 점수·피처 누락·출처 |
| `cells.geojson` | 2D 지도용 격자 중심점과 예측 불가 상태. 개인 위치나 실제 피해 범위 아님 |
| `summary.json` | 기간별 상위 후보 5개씩과 모델·관측·출처 정보 |
| `verification.json` | 기존 입력과 일치 검사 및 출력 SHA |

실행 명령은 다음과 같다. 기존 산출물은 덮어쓰지 않으므로 새 출력 경로를 지정한다.

```bash
ssh inno-gpu-011
cd ~/bonghwajigi
training/.venv/bin/python -m bonghwa_training.prediction_evidence \
  --run data/artifacts/xgboost/hourly-20261031T135808Z-549349 \
  --dataset data/processed/korea-gk2a-context-v3 \
  --raw data/raw/korea-wildfire --static data/processed/korea-hindcast-v2 \
  --event hongseong_2023 --issue 2023-04-02T06:15:00Z \
  --output data/artifacts/xgboost/my-hongseong-replay
```

검토량을 줄이는 효과도 [별도로 측정](../../../training/reports/kma-recent-audit-20261031/ranking-audit.json)했다. 각 시점에서 정답이 알려진 후보의 상위 약 10%씩을 살펴볼 때 다음 비율의 양성을 찾았다. 시점별 올림 때문에 정확히 10%는 아니다.

| 홍성 검증 recall | 1시간 | 3시간 | 6시간 |
| --- | ---: | ---: | ---: |
| 현재 화재와 가까운 순서 | 29.9% | 23.3% | 24.0% |
| 최근 60분 화재와 가까운 순서 | 36.8% | 27.3% | 33.8% |
| 선택 모델 순서 | 36.8% | 27.3% | 32.4% |

모델 순서는 같은 검토량의 무작위 선택 기대값보다 약 2.7~3.6배의 양성을 찾았지만, 최근 화재 거리 기준보다 확실히 우수하지 않다. 모델 순서로 살펴본 표본의 precision은 1.45%/2.14%/3.01%다. 이 결과를 경보 정확도나 사용자의 위험 확률로 제시하지 않는다. 이미 모델 선택에 사용한 홍성 검증 표본이며 미래 구름으로 검열된 행이 제외돼 있다. 사건별로 모델·현재 거리·최근 거리 기준을 계속 비교한다.

v4 수집→구축→학습 뒤 `bonghwajigi-kma-utility-v4.service`가 자동으로 사건별 순위 진단과 같은 규칙의 재생 자료를 만든다. 재생 시각은 각 검증 창 시작+4시간+가정 지연으로 고정했다. 관측이 없으면 예측 불가로 남긴다. 결과 경로는 `data/artifacts/xgboost/kma-utility-v4/`이며 완료 시 `completion.json`이 생긴다. 학습 성공·Qwen 복구 후 남긴 완료 영수증과 모델/설정 SHA를 확인한 경우에만 실행한다. transient systemd unit이 사라졌다는 사실만으로 성공 처리하지 않는다.

```bash
journalctl --user -u bonghwajigi-kma-utility-v4 -f
```

현재 [내부 예측 계약](../../../src/bonghwajigi/contracts/policy.py)은 단일 `simulation/unavailable`·`probability`만 받으며, 기간별 연구 점수·품질 정보를 받지 못한다. [앱 API](../../../src/bonghwajigi/api/mobile.py)는 예측을 `MODEL_CONNECTION_EXCLUDED`로 표시하고, [정책 실행기](../../../src/bonghwajigi/policy/three_stage.py)는 예측 점수를 대응 단계에 쓰지 않는다. 연구 JSON의 인계와 제품 연결은 별개이며, 기존 모의 확률 필드나 환경 H1~H3로 연구 점수를 자동 변환하지 않는다.

## 재현 명령과 남은 작업

명령은 저장소 루트에서 실행한다. 서빙 환경과 학습 환경은 분리돼 있다.

```bash
uv sync --project training --frozen --extra train --extra geo
training/.venv/bin/python -m bonghwa_training.kma_profile \
  --config training/configs/korea-gk2a-hourly-v2.json
training/.venv/bin/python -m bonghwa_training.goes_build \
  --root data/raw/korea-wildfire/gk2a-ff \
  --output data/processed/korea-gk2a-hourly-v2 \
  --config training/configs/korea-gk2a-hourly-v2.json
training/.venv/bin/python -m bonghwa_training.hourly_context \
  --dataset data/processed/korea-gk2a-hourly-v2 --raw data/raw/korea-wildfire \
  --static data/processed/korea-hindcast-v2 --output data/processed/korea-gk2a-context-v2 \
  --config-output training/configs/korea-gk2a-context-v2.json
BONGHWA_HOURLY_DATASET=data/processed/korea-gk2a-context-v2 \
BONGHWA_HOURLY_CONFIG=training/configs/korea-gk2a-context-v2.json \
  bash training/tools/train_hourly_gpu.sh
```

GPU 학습 스크립트는 자료 계약과 SHA를 먼저 검사하고, Qwen이 실행 중이면 잠시 중지한다. 공용 GPU 잠금을 얻은 뒤 학습하고 종료/실패 시 서빙을 복구한다. `training/.venv/bin/python -m bonghwa_training.goes_train --device cpu ...`는 CUDA 없이 재현할 수 있다.

국내 적용 전에는 다음 증거가 더 필요하다.

1. 실제 입력 발행·수신 이력과 재처리/실시간 알고리즘 버전의 동등성, 지연·장애·구름 범위 검증.
2. 다양한 국내 독립 산불 사건과 시기의 검증. 격자/시점 수를 늘리는 것으로 사건 수를 대신하지 않음.
3. 현재 사후 기상/정적 자료의 결합에 더해, 발행 시각이 보존된 실시간 관측 및 1~6시간 기상 예보, 연료/식생 건조도, 진화 조치 입력 결합. 미래 실황을 과거 예보인 것처럼 쓰지 않음.
4. 실제 화선·현장 피해·연기 노출처럼 사용자 영향과 연결할 별도 정답. 위성 탐지 모델을 곧바로 개인 피해 모델로 명명하지 않음.
5. 검토자가 정한 누락/오경보 허용 조건과 사건별 평가, 확률 보정의 독립 평가. 별도 정책 계약의 대응 단계 결정을 모델 연구자가 대신하지 않음.

## 공식 출처

- [기상청 API허브 — 천리안2A 자료](https://apihub.kma.go.kr/apiList.do?seqApi=6&seqApiSub=271), [국가기상위성센터 FF 정의](https://api.nmsc.kma.go.kr/homepage/html/base/cmm/selectPage.do?page=static.convergence.utilizationProducts).
- [GK2A FF 알고리즘 이론기반기술서](https://api.nmsc.kma.go.kr/resources/common/pdf/%EC%99%B8GK2A_L2_ATBD_%EA%B5%AD%EB%AC%B8_%EC%82%B0%EB%B6%88%ED%83%90%EC%A7%80_FF.pdf), [API 격자 참고](https://apihub.kma.go.kr/getAttachFile.do?fileName=map_info.pdf). 실제 승인 원본의 접근 조건을 따른다.
- [NOAA GOES 화재 산출물](https://vlab.noaa.gov/web/towr-s/goes-fhs), [NOAA 제품 ReadMe](https://www.star.nesdis.noaa.gov/atmospheric-composition-training/documents/G16_ABI_FDC_ReadMe.pdf). 공개 NODD 자료는 NOAA 출처를 표시하고 가공본을 원본으로 표현하지 않는다.
- [NASA FIRMS 국가별 연간 자료](https://firms.modaps.eosdis.nasa.gov/data/country/yearly_summary_files.txt), [속성 설명](https://firms.modaps.eosdis.nasa.gov/data/country/AttributesReadme.txt). 표준 처리 관측점이며 완전한 화선/음성 자료가 아니다.
- [MODIS STAC 컬렉션](https://planetarycomputer.microsoft.com/api/stac/v1/collections/modis-14A1-061), [ESA CCI 토지피복](https://planetarycomputer.microsoft.com/api/stac/v1/collections/esa-cci-lc), [Copernicus DSM](https://planetarycomputer.microsoft.com/api/stac/v1/collections/cop-dem-glo-90). 각 원 제공자의 이용조건과 attribution을 유지하며 원본 대량 재배포를 하지 않는다.
- [NOAA ISD 관측소 등록부](https://noaa-isd-pds.s3.amazonaws.com/isd-history.csv), [ISD-Lite 형식](https://noaa-isd-pds.s3.amazonaws.com/isd-lite/isd-lite-format.txt), [공개 국가 경계 출처](https://www.geoboundaries.org/api/current/gbOpen/KOR/ADM0/).
- [키 없는 NOAA JPSS](https://registry.opendata.aws/noaa-jpss/)의 EFIRE 실제 샘플도 확보했다. 화재 없는 위치의 판별에는 전체 geolocation과 유효 관측 마스크가 추가로 필요하다. 극궤도 통과 간격으로 6시간 연속 음성을 만들지 않는다.
- [키 없는 GK2A 공개 영상](https://registry.opendata.aws/noaa-gk2a-pds/)의 목록을 확인했다. 공개 L1B 영상 자체를 화재 정답이라고 부르지 않는다. [JAXA P-Tree](https://www.eorc.jaxa.jp/ptree/registration_top.html)는 별도 등록·자료 이용조건이 있어 인증 없는 대안으로 사용하지 않았다.
