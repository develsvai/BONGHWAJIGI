# 국내 학습 기상 입력 정합 조사 — 2026-11-01

현재 KMA의 새 조회 경로는 활용신청 필요 응답으로 자료를 받지 못했다. 대신 **2022년 train10개 사건의 공개 GFS 실제 과거 예보71개에서 바람·기온·습도284개 필드를 확보했다.** 이는 기상 입력 보강용 자료 확보이며, 모델 성능 향상을 검증한 결과가 아니다. 앞서 완료된57회 학습 실험에는 이 GFS 자료를 넣지 않았다.2020~2021년 네 사건의 접근 실패와 전체14개 연결 미확보 사실은 그대로 남긴다.

## 요청 범위와 실제 결과

- 최초 상한: 총 20회, 파일별·합계 100MiB 이내, 재시도 없음, 403 뒤 동일 경로 중단.
- KMA: 11건 계획 중 서로 다른 6개 경로를 실제 요청했다. 모두 HTTP403이며 제공자 메시지는 `활용신청이 필요한 API 입니다`였다. 나머지 5건은 건너뛰었다. 응답 합계 894bytes. 인증키는 서버의 비공개 설정 파일에서만 읽고 URL 인자·stdout·산출물에 기록하지 않았다.
- 공개 GFS: 별도 승인된 최대 3요청·16MiB 계획으로 index GET, 본체 HEAD, 정확한 Range GET을 실행했다. 총 3회, 6,878,543bytes. 전체 535,297,839bytes 파일은 내려받지 않았다.
- 과거 GFS 접근성 추가 확인: 별도 승인된 최대4요청·512KiB 안에서 2020~2021년 네 사건의 첫 고정 cycle/lead 인덱스를 각각1회 요청했다. 모두404였고 오류 본문을 읽지 않아 추가 전송 본문0bytes다. 대체 경로·재시도는 하지 않았다.
- 2022년 범위로 축소한 실제 수집: 별도 승인된 최대600요청·400,000,000bytes 안에서 현재 시각 예보71개를 받았다.71개의 모든 인덱스를 먼저 확인한 뒤284개 정확한 필드 Range를 순차 요청했다. 실제355요청·244,226,387bytes로 완료했다. 따라서 이번 조사·수집의 기상 API 총 요청은 KMA6회+GFS362회=368회이며, 합계 수신 본문은251,105,824bytes다. 공식 문서 열람·서버 간 파일 복사는 이 기상 데이터 요청 수에 포함하지 않는다.
- 추가 조회 없이 기존 train 14개 입력을 감사했다. 2023 validation/calibration 및 2025 holdout 파일은 열지 않았다. 정답 열도 디코딩하지 않았다.

| KMA 신청 항목 | 정확한 경로 | 용도와 확인 결과 |
|---|---|---|
| 수치모델 → KIM 경량화 → 1.1.3 국지 단일면 | `/api/typ06/url/nwp_nc_vars_down.php` | U10 작은 영역 NC 1회 재확인, 403. 풍향축 원본 메타데이터 미확보. |
| 수치모델 → 통합모델 UM → 10.3.3 임의 위경도 | `/api/typ06/cgi-bin/url/nph-um_grib_pt_txt1` | UMKR/N512, 2022-03-04 00UTC +1h의 U/V/T/RH 요청, 403. |
| 수치모델 → 9.1 GRIB 격자·변수 참고정보 | `/api/typ06/cgi-bin/url/nph-nwp_header` | UM l015/단일면의 과거 변수·격자 확인, 403. |
| 지상관측 → ASOS → 1.1 시간자료 | `/api/typ01/url/kma_sfctm2.php` | 울진 사건 시각의 전체 지점 단일 시각, 403. |
| 지상관측 → AWS → 1.1 매분자료 | `/api/typ01/cgi-bin/url/nph-aws2_min` | 같은 단일 시각의 분 관측, 403. |
| 지상관측 → 지점정보 → 1.1.1 지상 / 1.1.2 AWS | `/api/typ01/url/stn_inf.php` | 당시 관측소 좌표·장비 높이 확인. SFC가403이어서 AWS 등 동일 경로 후속 요청 생략. |

요청별 비밀값 없는 파라미터·시각·응답 SHA는 [API 계획](api-probe-v1/plan.json)과 [실제 결과](api-probe-v1/report.json)에 있다. KMA의 403은 응답 문구에 근거해 **해당 경로의 활용신청이 필요함**으로 기록한다. 키 전체가 잘못됐다고 단정하지 않으며 재시도하지 않았다.

공식 문서에서 현재 KIML 계열은 2026년 시작 제품이므로 2020~2022 학습 기상을 대신할 수 없다. 과거 UM/LDAPS는 `UMKR/N512`와 `l015` 제품 계약을 따로 사용해야 한다. `nwp_vars_down.php?nwp=l015&sub=unis`도 공식 다운로드 경로이지만 이번에는 호출하지 않았다. 보존기간 안내와 실제 파일 존재는 별도다. [KMA 수치모델 공식 문서](https://apihub.kma.go.kr/apiList.do?seqApi=9)

ASOS의 요청·관측 시각은 KST이고 WD는 **36방위**, WS는 m/s다. AWS 분 자료의 시간도 KST이며 실제 반환 헤더의 변수·품질코드·결측값 검증이 필요하다. 관측소 정보는 당시 시각의 좌표·풍속계 높이를 함께 확인해야 한다. 과거 관측값을 현재 조회할 수 있어도 당시 발행·수신 시각이 입증되지는 않는다. [ASOS](https://apihub.kma.go.kr/apiList.do?seqApi=2), [AWS](https://apihub.kma.go.kr/apiList.do?seqApi=2&seqApiSub=239), [지점정보](https://apihub.kma.go.kr/apiList.do?seqApi=2&seqApiSub=317)

## 기존 ISD 입력에서 확인한 문제

고정 train14개, 315,490행(1/3/6h 반복 포함)을 기상 입력 열만 읽었다. 29,299행, **9.2868%**에 기상 거리/age가 없다. 안동2020의 거리는 최대84.747km, 안동2021은28,370/91,892행에 기상이 빠져 있다. 아래 수치는 행 가중 입력 진단이며 성능 평가가 아니다. [전체 사건별 입력 감사](existing-input-audit.json)

| train 사건 | 관측소 거리 중앙값 / 95백분위(km) | 관측 age 중앙값(h) |
|---|---:|---:|
| 안동2020 | 23.057 / 65.936 | 1.917 |
| 안동2021 | 27.678 / 39.726 | 2.250 |
| 울진2022 | 24.386 / 38.420 | 1.583 |
| 울주2020 | 21.011 / 31.036 | 1.583 |
| 영덕2022 | 40.469 / 51.259 | 1.583 |
| 양구2022 | 34.937 / 51.086 | 1.583 |

기존 구현은 사후 QC된 ISD 자료를 사용하며, issue보다 최소1시간 전 관측만 선택한다. 대체 관측 탐색도 최대3시간·100km 범위다. 따라서 age는 실제 전송 지연의 측정값이 아니라 관측 시각과 issue의 차이다. 새로운 AWS가 더 가깝거나 더 최신일 가능성은 있으나 이번에는 실제 관측을 얻지 못해 개선 폭을 측정할 수 없다.

## 확보한 GFS와 단위·시간 검증

- 원천: NOAA NODD `noaa-gfs-bdp-pds/gfs.20220303/18/atmos/gfs.t18z.pgrb2.0p25.f007`.
- 예보 기준시각2022-03-03 18UTC, lead7h, 유효시각2022-03-04 01UTC. 분석장이나 사후 재분석으로 대체하지 않았다.
- GRIB Section1/3/4에서 NCEP operational forecast, 기준시각·lead, 10m UGRD/VGRD와 2m TMP/RH, grid1440×721·0.25°, component flags48을 확인했다. bit5=0이므로 U/V는 true east/north이며 grid-relative 회전을 적용하지 않는다. [공식 GRIB component 규격](https://www.nco.ncep.noaa.gov/pmb/docs/grib2/grib2_doc/grib2_table3-3.shtml)
- 원 좌표계는 반지름6,371,229m 구면 geographic CRS다. EPSG4326으로 이름을 바꾸지 않았으며, 이 probe의 점 표본 비교는 동일한 수치 경·위도를 사용하는 근사임을 명시했다.
- GDAL의 자동 섭씨 변환을 끄고 원 TMP 단위를 K로 검증했다. 비교할 때만273.15를 한 번 뺐다. 바람 m/s, RH%를 원 메타데이터와 대조했다.
- 울진 bbox에 중심이 들어오는4×4격자16개는 네 변수 모두 finite였다. U=0.176~3.786m/s, V=0.843~7.273m/s, T=278.448~283.148K, RH=19.0~52.5%. [전체 표본 값·단위](comparison-v1/gfs-values.json)
- 객체 `Last-Modified=2022-03-03 21:43:34GMT`는 유효시각 전에 보관됐다는 증거다. 최초 발행·사용자 수신 시각을 직접 검증한 것은 아니므로 `historical_publication_time_verified=false`를 유지했다. 현재 조회 시각을 과거 가용시각으로 쓰지 않는다.

공식 NCEI 소개에는 AWS trailing30days 안내가 있지만 **이번 특정2022 파일은 실제 조회·원본검증에 성공했다**. 한 파일의 성공으로 모든 날짜의 보존을 보장하지 않는다. 2020과2021년2월의 네 고정 과거 경로는 추가 확인에서 모두404였다. 이는 요청한 경로의 파일을 확보하지 못했다는 결과이며 다른 전체 아카이브에도 없다는 뜻은 아니다. [NCEI 안내](https://www.ncei.noaa.gov/products/weather-climate-models/global-forecast), [NOAA GFS 등록·이용조건](https://registry.opendata.aws/noaa-gfs-bdp-pds/)

## 같은 유효시각에서의 제한된 비교

울진의 첫 실제 snapshot issue는2022-03-04 02:35UTC다. 이 시점에서 기존 ISD 관측 시각이 정확히01UTC인 행만 선택하고 horizon 반복을 제거해459개 지점을 비교했다. GFS의01UTC 예보와 동일 시각 관측이다. [비교 결과](comparison-v1/common-time-comparison.json)

| 항목 | 결과 |
|---|---:|
| ISD 관측소 거리 중앙값 / 95백분위 | 25.298 / 38.816km |
| GFS 최근접 격자 중심 거리 중앙값 / 95백분위 | 9.941 / 15.053km |
| 바람 벡터 차이 평균 | 3.368m/s |
| 기온 GFS−ISD 평균 | −4.218°C |
| RH 절대 차이 평균 | 4.240%p |

관측소 거리와 격자 중심 거리는 다른 의미이며 거리 감소가 정확도 향상을 뜻하지 않는다.459개 지점이459개 독립 관측소인 것도 아니다. 서로 다른 지점 대표성, 반복되는 관측소 값, 한 유효시각만 비교한 한계가 있어 예보 skill 또는 모델 성능 검증으로 쓰지 않는다. GFS의0.25°는 대략20~28km 간격으로, 산지 국지풍과 돌풍을 해결하지 않는다. 예보의 유효시각과 cycle age도 관측 age와 구분해야 한다.

## 전체 primary train 연결 규모 — 계산만 완료

**수집 기준은 새 입력 정의 primary 코호트404,130행(134,710개 고유 point/issue)이다.** `data/processed/korea-first-observation-train-20261101-v2`의14개 train에서 `cohort_primary_clear60`, `issue_epoch_seconds`, `row`, `col`만 읽었다. 미래 unknown 행도 보존하며 미래 정답·관측 여부를 읽거나 필터에 사용하지 않았다. 기존315,490개 known-only v4행 기반 계획은 진단 기록으로 보존하되 실제 기상 가용성·수집 기준으로 사용하지 않는다.

고정 계획 가정: issue보다 최소6시간 앞선 최신6시간 cycle을 고르고, 실제 객체 보관시각이 issue보다 앞서는지 별도 검증한다. 현재 기상은 `floor(issue to hour)`, 향후 특성을 만들 경우 같은 cycle의+1/+3/+6h 유효시각을 사용한다. 동일 전구 파일은 사건 간 재사용한다. 아직 다운로드를 실행하지 않았다.

| 범위 | 고유 cycle/lead 파일 | index+HEAD+한 Range 요청 | 한 Range 전송 추정 | 네 정확한 필드만 개별 Range 시 |
|---|---:|---:|---:|---:|
| 현재 기상만 | 105 | 315 | 722,247,015bytes | 525요청 /338,772,525bytes |
| 현재 및+1/+3/+6h | 250 | 750 | 1,719,635,750bytes | 1,250요청 /806,601,250bytes |

단일 성공 파일의 압축 크기로 계산했으므로 날짜별 실제 크기는 달라질 수 있다. 모든 cycle/lead/valid-time 목록과 사건별 issue·행 수는 [새 primary 수집 규모 계획](primary-plan-v1/acquisition-plan.json)에 있다. 이 전체14개 계획은 `execution_authorized=false`인 계산 기록이며 그대로 실행하지 않았다. 아래2022년10개 현재 기상 범위만 별도로 승인·수집했다. [기존 known-only 계산](comparison-v1/acquisition-plan-estimate.json)은 미래 관측 누락에 따라 입력 수집을 제한할 수 있어 새 계획으로 대체되었다.

### 2020~2021년 인덱스 접근 확인

네 사건의 최초 primary issue에서 위 규칙으로 cycle/lead를 정하고, 요청 전 [고정 계획](earlier-index-probe-v1/plan.json)을 썼다. NOAA의 공식 GFSv16 전환 안내에 따라2021-03-22 12UTC 이전 자료는 `gfs.YYYYMMDD/HH/gfs.tHHz.pgrb2.0p25.fFFF.idx` 구조로 조회했다. `/atmos`는 그 이후에 추가된 디렉터리이며 이번에는 대체 경로 탐색을 하지 않았다. [NOAA 2021-03-18 공식 변경 공지, p4–5](https://www.weather.gov/media/notification/pdf2/scn21-20gfs_v16.0_aac.pdf)

| 사건 | 최초 primary issue(UTC) | 고정 예보 cycle(UTC) / lead | 결과 |
|---|---|---|---|
| 안동2020 | 2020-04-25 05:15 | 2020-04-24 18:00 /11h | 404 |
| 안동2021 | 2021-02-21 08:15 | 2021-02-21 00:00 /8h | 404 |
| 고성2020 | 2020-05-01 12:15 | 2020-05-01 06:00 /6h | 404 |
| 울주2020 | 2020-03-19 06:15 | 2020-03-19 00:00 /6h | 404 |

[실제 응답 기록](earlier-index-probe-v1/report.json)에4개 URL·시각·상태가 있다. 따라서14개 사건 전체에 GFS를 공정하게 연결할 수 있는지 아직 확인되지 않았다. 없는 사건·행을 조용히 제거하거나 기상을0으로 채우지 않는다. 후속 범위는 날짜·접근성으로 고정한2022년10개만 별도로 비교하도록 명시했다.

## 2022년 train10개 현재 기상 실제 수집

대상은 봉화·강릉동해·군위·합천·밀양·울진·울진5월·양구·영덕·영월2022다. 모델 결과나 정답 성능으로 사건을 선택하지 않았다. 동일10개 primary 입력 코호트238,836행(79,612개 고유 point/issue)에서 기존 ISD 입력과 새 GFS 입력 구성을 비교하기 위한 자료이며, 전체14개 성능 향상 결과로 해석하지 않는다.

- 계획: 현재 시각만71개 고유 cycle/lead, 예산600요청·400MB, 재시도 없음. +1/+3/+6h 미래 예보 확장은 제외했다. [동결 계획](gfs-2022-current-v1/plan.json)
- 모든71개 인덱스가 존재하고 정확한10m UGRD/VGRD,2m TMP/RH 및 cycle/lead가 일치한 뒤에만 필드를 받았다. 필드마다 정확한 HTTP206 범위를 검증했다.
- 실제 완료:355요청(HTTP200 인덱스71개+HTTP206 필드284개),244,226,387bytes. 글로벌 전체 파일을 내려받지 않았다. 예산400MB 안에서 완료했으며 실패·재시도·누락0채움은 없었다. [완료 검증 보고서](gfs-2022-current-v1/report.json)
- 각 GRIB2의 Section1/3/4에서 operational forecast 기준시각·lead·valid time, 변수·높이·0.25° 격자1440×721·true east/north 성분을 검증했다. 네 변수의 grid SHA와 원 전구 파일 크기도 일치한다. 모든 저장 인덱스·GRIB의 SHA를 마지막에 다시 검증했다.
- 모든 인덱스·필드의 실제 `Last-Modified <= valid hour <= issue`를 확인했다. issue보다 최소6시간 앞선 최신 cycle 선택은 여전히 가용성에 대한 보수적 가정이다. 최초 발행 시각은 직접 입증되지 않아 `historical_publication_time_verified=false`를 유지한다.
- 완료 시각:2026-11-01 03:52:09KST. 보고서 SHA256: `af8b3f281df1509d325ced02cc7070589684f7c9d7c46a9d69b732ebc649caa1`. 실행 코드 SHA256: `c00908a10fe95110c920aba010cccace53827fd7ed9a1cb0786431299aa1b4e8`.

원본은 서버 `data/raw/korea-source-alignment-20261101/weather/gfs-2022-current-v1/` 아래에 보관한다. 보고서 폴더에는 작은 계획·보고서·코드·로그만 두며 GRIB 원본을 중복 보관하지 않는다. 서버 ELMFIRE환경은 rasterio가 있어도 GRIB 드라이버가 없어 실제 디코딩이 불가능했으므로, 변환 담당이 기존에 검증된 로컬 `training/.venv`로 디코딩한 뒤 작은 NPZ만 서버에 돌려보낸다. 새 패키지 설치와 서비스 변경은 없다. 기상 소스 조인과 후속 모델 비교는 별도 산출물이며 이 수집 보고서 자체는 정확도 향상을 주장하지 않는다.

## 보관·재현·이용조건

- 코드: `training/src/bonghwa_training/kma_weather_alignment_probe.py`, 신규26개 테스트 통과 및 Ruff 통과.403/404/429 중단, 모든 인덱스 선검증, 잘못된 과거 가용시각·원본 메타데이터 차단, 미래 unknown 행 보존을 포함한다.
- 실제 원본 GRIB: 로컬·서버 `data/raw/korea-source-alignment-20261101/weather/gfs-probe-v1/`. 보고서에는 중복 GRIB를 두지 않는다.
- KMA 서버 기록: `data/raw/korea-source-alignment-20261101/weather/api-probe-v1/`.
- 로컬 train 복사본: `data/raw/korea-source-alignment-20261101/weather/train-input-snapshot/`.14개 train파일5,542,964bytes와 각 SHA report만 보관하며 비train파일은 없다. 분석은 기상 입력 열만 읽는다.
- 요청 단계별 실행 당시 코드가 각각 `api-probe-v1/source.py`, `gfs-probe-v1/source.py`에 있고, 비교 코드·환경 버전·출력 SHA는 `comparison-v1/`에 있다. 기존 실행 결과를 덮어쓰지 않았다.
- 새 primary 계획과 네 과거 인덱스 결과는 각각 `primary-plan-v1/`, `earlier-index-probe-v1/`에 실행 코드 SHA와 함께 보관했다. 서버 원본은 같은 이름으로 `data/raw/korea-source-alignment-20261101/weather/` 아래에 있다.
- 서버 `.venv-ml`에는 rasterio가 없고 ELMFIRE환경에는 pyarrow/pyproj가 없어 패키지 설치 대신 기존 로컬 training환경에서 비교했다. 실패한 서버 comparison-v1의 입력 감사 산출물은 보존했다. 서비스는 변경하지 않았다.
- KMA자료는 KMA API 이용조건과 출처표기 대상이며 소프트웨어 SPDX 라이선스로 표시하지 않는다. 이번에는 실제 기상 본문을 받지 못했다.
- NOAA NODD는 공개 이용을 허용하고 원자료 출처표기를 요청한다. NOAA의 보증·제휴를 암시하지 않고, 변환·부분추출 자료는 원본과 구분한다. 사용출처: NOAA Global Forecast System, accessed2026-11-01KST. [공식 이용조건](https://registry.opendata.aws/noaa-gfs-bdp-pds/)

추가 네트워크 요청 없이 로컬 입력 감사를 재현하려면 새 출력 디렉터리를 지정한다.

```sh
PYTHONPATH=training/src training/.venv/bin/python -m bonghwa_training.kma_weather_alignment_probe compare-existing \
  --dataset data/raw/korea-source-alignment-20261101/weather/train-input-snapshot \
  --raw data/raw/korea-source-alignment-20261101/weather/gfs-probe-v1 \
  --output data/raw/korea-source-alignment-20261101/weather/comparison-replay
```

이 작업은2022년10개 현재 기상의 원본 확보·검증까지 수행했다. 기존57회 학습이나 운영 모델은 변경하지 않았고, 후속 별도 비교 실험과 개인 위험 확률·알림 정책 연결은 이 보고서에서 성과로 주장하지 않는다.
