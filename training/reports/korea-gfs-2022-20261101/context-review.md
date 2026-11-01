GFS 2022 입력 변환 독립 검토 — 2026-11-01

**판정: 이번 고정된 2022년 기상 교체 실험을 막을 변환 오류는 발견하지 못했다.** 실제 원본·중간 배열·최종 입력을 읽기 전용으로 대조했다. 이는 모델 성능이나 개인 영향 확률의 유효성을 승인하는 검토가 아니다. 모델 학습·2023 검증/보정·2025 시험 자료에는 접근하지 않았고, 코드나 기존 산출물을 수정하지 않았다.

검토 코드는 `training/src/bonghwa_training/korea_gfs_context.py`, 메타데이터 해석은 `kma_weather_alignment_probe.py`의 `gfs_metadata`, 획득 절차는 같은 파일의 `acquire_gfs_2022_current`다. 변환기 작성자와 별도로 검토했으며, 이번 모델 수치 감사는 다른 검토자가 담당한다.

| 확인 항목 | 독립 확인 결과 |
| --- | --- |
| 획득 범위 | 2022년 학습 사건 10개, cycle/lead 조합 71개 × UGRD/VGRD/TMP/RH 4개. 기록된 HTTP 요청 355회, 응답 244,226,387바이트 |
| 원본 무결성 | GRIB 284개 및 색인 71개의 실제 파일 SHA-256을 모두 획득 report와 대조, 불일치 0 |
| 중간·최종 무결성 | NPZ 71개, 사건별 Parquet 10개의 실제 SHA-256을 각 report와 대조, 불일치 0. context plan SHA도 report와 일치 |
| 행·후보 식별 | 최종 79,612행, 10개 사건, 사건 내 `(issue_epoch_seconds, row, col)` 중복 0. 원래 1/3/6시간 반복을 포함한 후보 수는 238,836행 |
| 최근접 셀 | 사건별 고유 좌표 5,581개를 37×37 전체 원시 격자의 구면 Geod 거리와 대조. 선택 셀 모두 일치; 거리 최대 절대 차이 `2.028599510595086e-12 km` |
| 실제 기상 입력 비교 | 79,612행 × 4개 = 318,448개 값을 저장된 NPZ에서 별도로 인덱싱해 비교. TMP는 273.15를 한 번 빼고, RH/u/v는 그대로 비교하여 최대 차이 모두 0 |
| 결측·공간 정보 | 전 행 `gfs_sample_valid=true`, 비유한 기상값 0. 전체 사건이 공유하는 실제 기상 격자 67개. 지점과 격자 중심 거리 0.2972337031~17.7305924551km |
| 시간 | 전 행 reference/valid/assumed availability/lead/age를 독립 계산해 일치. reference age 6.25~11.9166666667시간, valid age 0.25~0.9166666667시간 |

좌표·풍향·단위 계약은 다음과 같이 확인했다.

- 원본 284개 GRIB의 section 3을 직접 읽어 모두 earth shape code 6, scan mode 0, component flag 48임을 확인했다. 시작 좌표는 북위 90도·경도 0도, 끝 좌표는 남위 90도·경도 359.75도다. code 6은 반지름 6,371,229m 구면이며, WGS84 타원체와 동일하다는 뜻이 아니다. 코드도 native CRS의 두 축 반지름을 검사하고 EPSG:4326으로 바꾸지 않는다. [NCEP GRIB2 Table 3.2](https://www.nco.ncep.noaa.gov/pmb/docs/grib2/grib2_doc/grib2_table3-2.shtml)
- component flag의 5번째 비트가 0이므로 u/v는 동쪽·북쪽 성분이다. `grid[54] & 8` 검사는 이 비트와 일치한다. 풍속은 10m, 온도·상대습도는 2m 높이를 원본 product metadata와 GDAL tag 양쪽에서 검사한다. [NCEP GRIB2 Table 3.3](https://www.nco.ncep.noaa.gov/pmb/docs/grib2/grib2_doc/grib2_table3-3.shtml)
- GDAL의 `GRIB_NORMALIZE_UNITS=NO`, `GRIB_ADJUST_LONGITUDE_RANGE=NO`를 설정한 뒤 `[K]`, `[%]`, `[m/s]`, 721×1440, 원래 0.25도 transform을 검사한다. 따라서 이미 섭씨로 자동 변환된 값을 다시 빼거나, 경도 재배열 뒤 잘못된 열을 읽는 경로를 막는다. 실제 저장 NPZ와 최종 값의 대조도 통과했다. 이번 검토에서 284개를 별도 GDAL 구현으로 전부 다시 디코딩한 것은 아니다. [GDAL GRIB 문서](https://gdal.org/en/stable/drivers/raster/grib.html)
- 현재의 샘플링은 WGS84 경위도 숫자를 native 구면의 angular coordinate로 간주하는 근사다. 변환기 문서가 이 사실과 downstream WGS84 화재 방위각 계산의 별도 근사를 명시한다. 0.25도 자료를 작은 후보 격자에 반복 배치해도 새로운 국지풍 정보를 만들지는 않는다.

예보 시각은 `reference=floor((issue−6h)/6h)×6h`, `valid=floor(issue/1h)×1h`로 고정한다. 실제 모든 행에서 `reference+6h≤issue`, `valid≤issue`, lead 6~11시간을 확인했다. 원본 필드의 S3 Last-Modified도 모두 valid보다 2.2827777778~7.3577777778시간 앞선다. 이는 기록된 객체 시각을 뒷받침하지만 당시 최종 사용자에게 실제 배포된 시각을 증명하지 않는다. 따라서 6시간은 가정이고 `historical_publication_time_verified=false`를 유지하는 것이 맞다. GFS는 00/06/12/18 UTC의 6시간 주기를 제공한다. [NOAA GFS 공개 자료 등록부](https://registry.opendata.aws/noaa-gfs-bdp-pds/)

누수와 연결 계약도 점검했다. 변환기는 2022년 사건 allowlist만 열고, 원본 Parquet에서는 `cohort_primary_clear60`, issue/row/col/latitude/longitude 여섯 열만 읽는다. 미래 정답·관측 결과를 읽어 날씨 후보를 고르지 않는다. 각 후보가 원본에서 세 번 반복되었는지와 좌표 일치도 검사하며, 원본 10개 Parquet SHA를 획득 계획의 사건별 SHA와 연결한다. 이 검토의 독립 수치 재계산은 최종 context와 NPZ만 읽었고, 로컬에 없는 원본 cohort Parquet를 추가로 열거나 정답을 재검산하지 않았다.

출처 연결에서 주의할 두 사항은 현재 차단 사유가 아니다.

- 획득 단계의 `source_cohort_plan_sha256=f2151cad…e0c6b`는 `gfs_primary_cohort_acquisition_plan_v1` 요청 목록 계획을 가리킨다. context의 같은 이름 `170a1f40…f3a38`은 원래 first-observation-v2 데이터셋 계획을 가리킨다. 같은 필드명이 다른 단계 계획을 뜻하지만, 사건별 원본 Parquet SHA와 별도 acquisition plan/report SHA로 연결된다. 두 SHA가 같아야 한다고 해석하면 안 된다.
- converter 재검사 목록에는 원본 284개 GRIB가 있으나 색인 71개는 포함되지 않는다. 이번 독립 감사에서 색인 실제 파일도 전부 검증했다. 향후 재현 실행의 포괄적 무결성 감사에는 이 색인 검사를 포함하는 편이 좋다. 현재 원본 GRIB 선택은 별도로 내용 메타데이터를 검사하므로 색인만 신뢰하는 구조는 아니다.

| 단계 | 파일/코드 | 확인된 SHA-256 |
| --- | --- | --- |
| 획득 | `data/raw/korea-source-alignment-20261101/weather/gfs-2022-current-v1/report.json` | `af8b3f281df1509d325ced02cc7070589684f7c9d7c46a9d69b732ebc649caa1` |
| 획득 계획 | 같은 디렉터리 `plan.json` | `f82c3c23458d85e2e61375ee90e132ec1e1ca5da621451f3adc8cedb8664a508` |
| 디코딩 | `data/processed/korea-gfs-native-windows-2022-20261101/report.json` | `2680de18111531cc6f27273a1ab38762431063eccf27bc04ece41515e7a0af03` |
| context | `data/processed/korea-gfs-context-2022-primary-20261101/report.json` | `63cf122fa327b15820e3b57e7638a56c487f4fbfdf6ea1afaafa6f40930d6350` |
| context 계획 | 같은 디렉터리 `plan.json` | `f9aad36dbb4437424524ba9a03befc23903dee1fde951729a94b6a5284ab52ff` |
| 변환 코드 | `training/src/bonghwa_training/korea_gfs_context.py` | `e1d171887a70cab4c652073fb98d4300381aee37e55f88f07eaa8d8cccbc088c` |
| 획득·메타데이터 코드 | `training/src/bonghwa_training/kma_weather_alignment_probe.py` | `c00908a10fe95110c920aba010cccace53827fd7ed9a1cb0786431299aa1b4e8` |
| SHA helper 코드 | `training/src/bonghwa_training/download.py` | `e61e0c300ce70fdb53151b73e44f34caf4f3f27663b791ba6efb137f67879bd3` |

서버 절대경로로 기록된 세 코드 SHA는 동일한 로컬 상대경로로 매핑해 실제 파일과 일치를 확인했다. 디코딩 receipt의 환경은 rasterio 1.5.2/GDAL 3.12.2/NumPy 2.5.4이며 context build는 NumPy 2.5.4/PyArrow 26.0.0이다. 코드에 기록된 recheck 수는 디코딩 290개, context 385개이며 서로 다른 단계의 입력·계획·산출물 집합을 센다.

NOAA NODD 공개 자료는 공개 이용 가능 조건과 출처 표기 요청을 따른다. 변환한 입력을 원래의 수정되지 않은 NOAA 자료로 표시하거나 NOAA의 보증을 암시하지 않는다. 이번 확인은 저해상도 과거 예보 입력의 재현성과 정합성에 한정하며 `operational_use=false`, `probability=null`의 해석을 유지한다. [NOAA 자료 이용 조건](https://registry.opendata.aws/noaa-gfs-bdp-pds/)
