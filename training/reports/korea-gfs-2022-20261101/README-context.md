# 2022년 훈련 후보에 과거 GFS 입력 연결

작성·확인일: 2026-11-01 KST. 이 문서는 **기상 입력 구축 결과**를 기록한다. 모델 비교 결과는 별도 보고서에서 확인한다.

국내 2022년 산불 훈련 창 10개의 primary 입력 후보에 GFS 기온·상대습도·바람을 연결했다. **79,612개 고유 위치·시각 모두 생성했고 결측·범위 밖 입력은 0개**다. 원래 세 예측 구간에 대응하면 238,836행이다. 입력이 같으면 1·3·6시간 구간 모두 같은 기상값을 사용한다. 2023년 검증·보정, 2025년 테스트 자료 및 미래 정답·감사 열을 읽지 않았다.

## 원자료와 입력 선택

- 원자료: NOAA GFS 운영예보의 0.25° GRIB2. 2022년 71개 cycle/lead 조합 × UGRD·VGRD·TMP·RH 네 필드 = 284개 파일. [실제 수집 보고서](../korea-source-alignment-20261101/weather/gfs-2022-current-v1/report.json).
- 기존 first-observation-v2 원본은 변경하지 않았다. 읽은 Parquet 열은 `cohort_primary_clear60`, `issue_epoch_seconds`, `row`, `col`, `latitude`, `longitude`의 여섯 개뿐이다.
- 입력 시각에 결정된 primary flag로 선택하고, `(issue,row,col)` 키의 정확히 세 번 반복 및 동일 좌표를 확인한 뒤 중복을 제거했다. 미래 관측 가용성·양성·음성에 따른 추가 행 선택은 없다.
- 2020·2021년의 공개 GFS 객체 접근 실패 후 2022년 10개 창을 고정한 비교다. 결과를 전체 14개 훈련 창이나 독립 국내 서비스 검증으로 확장하지 않는다.

| 훈련 창 | 고유 위치·시각 수 |
|---|---:|
| hapcheon_2022 | 4,599 |
| uljin_2022 | 11,794 |
| yeongdeok_2022 | 12,063 |
| yeongwol_2022 | 4,041 |
| gangneung_donghae_2022 | 7,965 |
| bonghwa_2022 | 1,060 |
| yanggu_2022 | 17,672 |
| gunwi_2022 | 329 |
| uljin_may_2022 | 868 |
| miryang_2022 | 19,221 |
| **합계** | **79,612** |

## 시각·단위·좌표 계약

예보 기준 시각은 `floor((issue−6h)/6h)×6h`, 유효 시각은 `floor(issue/1h)×1h`로 고정했다. 따라서 현재 시간대에 유효한, 이전 cycle에서 생성된 예보를 사용한다. **기준 시각+6시간은 발행 지연 가정**이다. 원본 객체의 `LastModified≤valid≤issue`도 별도로 검증했지만 최초 공표 시각까지 검증한 것은 아니다. `historical_publication_time_verified=false`를 유지한다.

GRIB 원본의 변수·높이·시각·바람 축과 GDAL 디코딩 태그가 일치해야 통과한다. U/V는 지상 10m의 true east/north 성분(m/s), 기온·습도는 지상 2m 값이다. `GRIB_NORMALIZE_UNITS=NO`로 읽은 Kelvin 기온에서 273.15를 정확히 한 번 빼고, 상대습도는 %를 유지한다. 범위 검사에서 벗어나거나 마스킹된 값은 NaN과 `gfs_sample_valid=false`로 남기며 0으로 대체하지 않는다.

`GRIB_ADJUST_LONGITUDE_RANGE=NO`를 사용하며 원래 721×1440, 0.25° 격자를 보존했다. 원 CRS는 **반지름 6,371,229m인 구면**이고 EPSG:4326으로 덮어쓰지 않는다. 입력 WGS84 위·경도의 수치를 원구면의 각좌표로 쓰는 근사다. 주변 네 격자 중심 중 구면 대권거리가 가장 가까운 값을 선택하며 보간하지 않는다. 이후 모델에서 사용하는 WGS84 화재→사용자 방향 계산은 별도의 근사로 구분한다.

한국 영역의 37×37 원격자 창을 저장한 뒤 위치를 연결했다. 실제 후보는 원격자 **67개**를 공유한다. 예보를 약 1km 후보 좌표에 붙여도 예보 해상도가 1km가 되는 것은 아니다. 격자 거리 최댓값 17.73km는 국지풍·지형풍을 충분히 표현하지 못할 수 있음을 보여준다.

| 입력·진단 | 최솟값 | 최댓값 | 결측 |
|---|---:|---:|---:|
| 기온 °C | -10.7935 | 30.0389 | 0 |
| 상대습도 % | 15.7 | 89.3 | 0 |
| 동쪽 바람 성분 m/s | -1.6879 | 12.6758 | 0 |
| 북쪽 바람 성분 m/s | -5.4618 | 8.3351 | 0 |
| 원격자 거리 km | 0.2972 | 17.7306 | 0 |
| 예보 기준 시각 경과 h | 6.25 | 11.9167 | 0 |
| 예보 유효 시각 경과 h | 0.25 | 0.9167 | 0 |

## 실행과 감사

서버 ELMFIRE 연구 환경에는 rasterio 1.4.4가 있지만 GRIB 드라이버 `gdal_GRIB.so`가 없어 기존 네 필드 사전 확인이 실패했다. 원본·환경을 수정하거나 패키지를 설치하지 않았다. 기존 로컬 `training/.venv`의 rasterio 1.5.2 / GDAL 3.12.2에서 같은 네 필드 검증을 통과한 후 전체 자료를 디코딩했다. [사전 확인 기록](context/preflight-check.json)을 보존한다.

1. 수집 완료 원본을 로컬 ignored `data/raw/`로 복사하고 전체 파일 해시와 완료 보고서를 검증했다.
2. 로컬 기존 환경에서 71개 묶음의 네 필드를 작은 원격자 NPZ로 디코딩했다. [디코딩 계획](context/decoded-plan.json), [결과](context/decoded-report.json).
3. 작은 NPZ와 출처 기록만 서버로 전송했다. 서버의 기존 `.venv-ml`에서 10개 원본 Parquet와 GFS 계획의 해시를 대조한 뒤 [입력 연결 계획](context/plan.json)을 먼저 동결했다.
4. 동일 계획으로 구축하고 원자료·코드·계획·출력 **385개 파일**의 해시를 다시 검사했다. [완료 보고서](context/report.json), [필드 감사](context/input-audit.json).
5. 새 변환기 테스트 8개와 Ruff를 통과했다. 좌표 최근접은 독립 `pyproj.Geod` 구면 계산과 전체 주변 격자 비교로 검증했다. 단위·시각·높이·CRS 불일치, 미래 시각, 반복 행 좌표 충돌, 결측, 소스 변조와 출력 덮어쓰기를 거부하는 검증을 포함한다.

서버 프로젝트 루트에서 입력 연결 재현 명령은 다음과 같다. 산출물은 덮어쓰지 않으므로 재실행할 때는 새 출력 디렉터리를 지정한다.

```sh
# 로컬 기존 GRIB 환경에서 수행
PYTHONPATH=training/src training/.venv/bin/python -m bonghwa_training.korea_gfs_context decode \
  --raw data/raw/korea-source-alignment-20261101/weather/gfs-2022-current-v1 \
  --decoded data/processed/korea-gfs-native-windows-2022-20261101

# 검증된 NPZ를 서버의 같은 상대경로로 옮긴 뒤, plan → build 순서
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 PYTHONPATH=training/src \
  .venv-ml/bin/python -m bonghwa_training.korea_gfs_context plan \
  --raw data/raw/korea-source-alignment-20261101/weather/gfs-2022-current-v1 \
  --decoded data/processed/korea-gfs-native-windows-2022-20261101 \
  --cohort data/processed/korea-first-observation-train-20261101-v2 \
  --output data/processed/korea-gfs-context-2022-primary-20261101
# 위 명령의 plan을 build로 바꾸어 같은 고정 계획 실행
```

출처 단계의 같은 이름인 `source_cohort_plan_sha256`는 의미를 구분한다. 수집 보고서에서는 입력 전용 GFS 요청 inventory 계획(`gfs_primary_cohort_acquisition_plan_v1`)의 해시이고, context 보고서에서는 원래 first-observation-v2 데이터셋 구축 계획의 해시(`170a1f4008de6160d0c7e514895daa78fcd568ca7fb12c0502d7316b024f3a38`)다. 두 단계는 정확히 같은 2022년 10개 원본 Parquet SHA로 연결된다. context는 수집 계획·수집 완료 보고서 해시도 별도 필드로 기록한다.

서버 산출물: `/home1/ncloud/bonghwajigi/data/processed/korea-gfs-context-2022-primary-20261101/`. 로컬 ignored `data/`에도 같은 상대경로로 보존했다. 원본 GRIB·NPZ·Parquet는 Git 보고서에 넣지 않았으며 보고서와 코드 스냅샷만 보관한다.

| 증거 | SHA-256 |
|---|---|
| 원본 수집 완료 보고서 | `af8b3f281df1509d325ced02cc7070589684f7c9d7c46a9d69b732ebc649caa1` |
| 입력 연결 계획 | `f9aad36dbb4437424524ba9a03befc23903dee1fde951729a94b6a5284ab52ff` |
| 입력 연결 완료 보고서 | `63cf122fa327b15820e3b57e7638a56c487f4fbfdf6ea1afaafa6f40930d6350` |
| 변환기 코드 | `e1d171887a70cab4c652073fb98d4300381aee37e55f88f07eaa8d8cccbc088c` |

공식 근거: [GDAL GRIB 옵션·단위](https://gdal.org/en/stable/drivers/raster/grib.html), [NCEP 지구 형상 코드](https://www.nco.ncep.noaa.gov/pmb/docs/grib2/grib2_doc/grib2_table3-2.shtml), [NCEP 바람 성분 축 플래그](https://www.nco.ncep.noaa.gov/pmb/docs/grib2/grib2_doc/grib2_table3-3.shtml), [NOAA GFS 공개 자료](https://registry.opendata.aws/noaa-gfs-bdp-pds/). 이 파생 자료는 NOAA 원자료에서 변환한 연구 산출물이며 NOAA의 보증·승인을 뜻하지 않는다. **물리적 화선 도달·개인 피해 확률이나 운영 경보를 검증한 결과는 아니다.**
