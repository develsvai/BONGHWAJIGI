# 국내 화선·산림 공개 자료 추가 조사 및 실제 확보

조사일: 2026-11-01 KST. 대상은 **2019~2024년 국내 사건**이며, 기존 [국내 정답 조사](../gofer-hindcast-20261101/domestic-label-sources.md)에 새 배포 경로와 정적 입력 확보 결과를 추가했다. 이번 조사에서 재사용 조건·좌표계·관측 시각을 확인한 **시간별 실측 화선 GIS를 새로 받지는 못했다.** 대신 2021년 ESA 토지피복 원본과 작은 국내 절취본을 확보했다. 모델 학습·평가나 기존 자료 교체는 수행하지 않았다.

기계 판독 결과, 원본별 SHA256, 접근 상태, 수신 규격은 [public-label-sources.json](public-label-sources.json)에 있다. 실제 보존 파일은 `data/raw/korea-source-alignment-20261101/public-labels/` 아래 **17개, 합계 7,755,593 bytes**다. 여기에는 메타데이터·영수증·파생 절취본이 포함되며 100MB 한도 이내다.

## 1. 실제 확보한 정적 입력

| 항목 | 확인 결과 |
| --- | --- |
| 자료 | ESA WorldCover 2021 v200, `N36E129` 원본 GeoTIFF |
| 용도 | 토지피복·수목 피복의 정적 입력 후보. 실제 연료량·수분·산불 도달 정답을 제공하지 않음 |
| 이용조건 | CC BY 4.0. 출처와 가공 사실 표시 필요 |
| 관측·공개 시점 | 2021년 연간 자료, **2022-10-28 공개**. 2022년 3월 당시 사용 가능했다고 볼 수 없음 |
| 파일에서 확인한 좌표계 | EPSG:4326, 36,000 × 36,000, 1밴드 uint8, nodata=0 |
| 공간 범위·격자 | 경도 129~132°, 위도 36~39°, 픽셀 간격 1/12,000°. 명목 10m이며 미터 단위 정방형 격자는 아님 |
| 원본 크기 | 6,602,194 bytes |
| 원본 SHA256 | `c824fd6d591124a4d92ba909ea636f6c62e966c60426f69a3cbc7d90f95ee948` |
| 절취본 | `esa-worldcover-2021-korea-fixed-scenario-clip.tif`, 41,499 bytes |
| 절취본 SHA256 | `99e14f4847b47afedcd290c2b37d4d96682b7aa83ceb6d6604af08ffbc2ee8df` |

기존 시연 중심 129.3°E, 37°N에서 미리 정한 경위도 범위 `[129.24, 36.955, 129.36, 37.045]`만 원래 픽셀 그대로 잘랐다. 화재 정답을 보고 위치를 고르지 않았으며 재표본화·분류 변경도 없다. 절취본은 1,080 × 1,440셀, 결측 코드 0은 0셀, 수목 피복 코드 10은 1,467,174셀이다. **이는 해당 절취 범위의 검사이며 전체 타일의 무결측을 주장하지 않는다.** 이 절취본은 기존 UTM 100m 실행 격자와 다르므로 실제 결합 시 범주형 최근접 변환과 범위·결측 검사를 다시 해야 한다.

공식 근거: [자료·라이선스·배포 안내](https://esa-worldcover.org/en/data-access), [2021판 공개일](https://esa-worldcover.org/en/release-worldcover-map-2021), [확보한 공식 S3 원본](https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_N36E129_Map.tif). 공식 안내 HTML, 원본 URL·응답 헤더·취득 시각·SHA는 원본 폴더에 보존했다.

출처 표기: **© ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data (2021) processed by ESA WorldCover consortium.** 데이터 인용: [Zanaga 등, 2022, ESA WorldCover 10 m 2021 v200](https://doi.org/10.5281/zenodo.7254221). 이번 가공은 고정 지역의 원래 픽셀 절취다.

## 2. 새로 확인한 직접 배포·공식 경로

| 후보 | 직접 확인한 내용 | 현재 확보·권리 상태와 적합성 |
| --- | --- | --- |
| **산림청 1:5000 임상도 2019판·2024판** | 공식 포털에 2019판(2015~2019 조사), 2024판(2020~2024 조사)이 있다. 수종·임상·경급·영급·수관밀도·임분고 등의 정적 속성을 제공한다. | 공공데이터포털은 무료·이용허락범위 제한 없음으로 표시한다. 실제 배포는 개인정보·보안서약·목적 입력을 포함한 신청 절차다. **신청·외부 제출은 하지 않았고 SHP는 미확보**, CRS는 파일 확인 전까지 미정이다. |
| **FIRED South Korea, 2000년 11월~2024년 7월** | 공식 저자 저장소의 **2024-11-13 커밋**에 한국 자료 직접 링크가 있다. 현재 메인 대신 2025 이전 커밋을 고정해 README를 확보했다. | CU Scholar 레코드 요청이 **HTTP 403**으로 종료됐다. 우회하지 않았다. 실제 한국 압축파일의 daily 레이어·CRS·재사용 조건은 미확인이다. 설령 확보되어도 MODIS 일별 재구성이지 시간별 실측 화선이 아니다. |
| **JRC GlobFire v2 DailyPerimeters** | 공식 카탈로그: 2001-01-01~2021-01-01, MODIS MCD64A1 기반의 일별 화재영역 재구성, CC BY 4.0. | 2019~2020 보조 검증 후보. 안내된 부분 추출 경로는 Earth Engine 등록이 필요해 실행하지 않았다. 전 지구 GWIS 대용량 묶음도 받지 않았다. `InitialDate`는 사건 시작일이므로 실제 snapshot 관측일과 혼동하면 안 된다. |
| **국내 14건 Sentinel-2 연구, 2019~2023** | 2024년 논문은 국내 14건의 화재 피해영역 탐지를 다룬다. | 검색된 공식 메타데이터까지만 확인했으며 출판사 열람은 429로 중단했다. 공개 가공 GIS·원자료 라이선스는 확인하지 못했다. 사후 피해 범위는 1~6시간 화선 정답을 대체하지 않는다. |
| **JRC Global Forest Cover 2020** | 공식 10m 산림 피복 자료. 현재 v4는 2026년 개정판이며 공식 안내는 출처 표기를 요구하는 자유 이용 조건을 설명한다. | 전 지구 약 50GB 자료는 미확보. 2020 기준년과 개정·공개 시점이 다르다. WMS RGB는 분석용 분류 래스터가 아니며 수목 피복만으로 연료모델이 정해지지 않는다. |

공식 링크:

- [산림청 임상도 공공데이터 카탈로그](https://www.data.go.kr/data/15093362/fileData.do?recommendDataYn=Y), [산림공간정보서비스](https://map.forest.go.kr/forest/). 포털에는 본인인증 필수 안내와 일반인 무인증 안내가 함께 있어 실제 인증 필요 여부를 확정하지 않았다. 기관·연구 신청에는 별도 절차가 있다. 2024판은 2022년 산불 이후 상태가 섞일 수 있으므로 당시 입력으로 바로 사용할 수 없다.
- [FIRED 고정 커밋 README](https://raw.githubusercontent.com/earthlab/firedpy/6376e3f91852287d54f629e663177fd6d2031bbf/README.md), [한국 2024 레코드 — 이번 접근 403](https://scholar.colorado.edu/concern/datasets/kw52j990z). README SHA는 `819f60cc643ea57dc9a2ec6ffdfce9cd8579bf6cbef8aaa3eb7aaec8933fa6f9`다. 코드·논문의 라이선스를 미확인 데이터에 전용하지 않는다.
- [GlobFire 공식 카탈로그](https://developers.google.com/earth-engine/datasets/catalog/JRC_GWIS_GlobFire_v2_DailyPerimeters), [원 논문](https://doi.org/10.1038/s41597-019-0312-2).
- [14건 Sentinel-2 논문](https://www.mdpi.com/2072-4292/16/5/884).
- [JRC 산림 피복 공식 안내](https://forobs.jrc.ec.europa.eu/GFC).

## 3. 요청형 국내 화선 자료를 받으면 적용할 수신 규격

시간별 정답의 우선 후보는 기존 조사에서 확인한 [NIFOS 2023년 4개 사건 자료](https://www.mdpi.com/2571-6255/9/1/31)다. 논문 표에는 발화점 4개와 비영 면적 경계 31행이 있지만, 이는 실제 제공 파일의 검증 완료를 뜻하지 않는다. 외부 연락이나 신청은 하지 않았다.

권장 전달 묶음은 **원본 GeoPackage 또는 SHP 전체 구성 파일 + snapshot별 메타데이터 JSON + 이용허락 증거**다. 아래는 아직 받은 자료가 아니라 수신 시 적용할 구체 계약이다.

| 필수 필드 | 의미와 검증 |
| --- | --- |
| `schema_version`, `event_id`, `snapshot_id` | 사건·관측을 안정적으로 식별. 2019~2024 사건 허용 목록과 중복 검사 |
| `geometry`, `geometry_kind` | 진행 화선, 진화 완료 선, 연소 영역, 추정 경계, 발화점을 구별. 점·부분선을 전체 면적으로 임의 변환하지 않음 |
| `crs_epsg`, `crs_wkt`, `axis_order`, `horizontal_units` | 원본 좌표계·축·단위. EPSG가 없으면 명시 WKT 필요. 좌표계 추측 금지 |
| `observation_time_original`, `observation_start_utc`, `observation_end_utc`, `source_timezone`, `time_precision_seconds` | 원문 시각을 보존하고 관측 구간·시간대 증거로 UTC 정규화. 날짜·시간대 불명확 시 격리 |
| `created_at_utc`, `transmitted_at_utc`, `available_at_utc`, `availability_evidence`, `availability_known` | 작성·전파·실제 이용 가능 시각을 관측 시각과 분리. 모르면 null. 이용 가능 시각이 없는 사후 정답은 실시간 입력으로 승격 불가 |
| `revision_id`, `revised_at_utc`, `supersedes_snapshot_id`, `retrospective_reconstruction`, `uses_final_perimeter` | 사후 수정·최종 경계 의존 여부와 모든 원본 버전 보존 |
| `sensor_or_method`, `platform`, `source_image_ids`, `observation_footprint` | 헬기·드론·현장·상황도·위성 구분과 실제 관측 범위 |
| `horizontal_uncertainty_m`, `temporal_uncertainty_seconds`, `uncertainty_method`, `coverage_status`, `cloud_or_occlusion_mask` | 위치·시간 오차와 미관측 범위. 모르는 오차를 0으로 쓰지 않음. 수작업 지도는 기준점 잔차·경계 판독 오차 필요 |
| `polygon_completeness`, `unburned_islands`, `front_state`, `suppression_observations` | 부분 경계·내부 미연소지·진행/진화 상태와 진화 개입 증거 |
| `provider`, `source_url`, `source_file`, `source_sha256`, `source_bytes`, `retrieved_at_utc` | 원본의 불변 식별자. 파생자료는 원본 SHA와 변환 기록에 연결 |
| `license_id`, `license_url`, `rights_evidence_file_sha256`, `attribution`, `permissions` | 학습·검증·파생 GIS·모델 공개·시연·상업 이용·원본 재배포의 허용 범위 각각 확인. 미확인 권리는 학습 차단 |
| `event_group_id`, `split_role`, `approved_use` | 연관 사건·기간을 같은 분할로 묶고 `metadata_only` / `retrospective_label` / `asof_feature`를 구별 |

수신 직후에는 해시·권리 → CRS·좌표 범위·기하 유효성 → 시간대·관측 순서 → 관측 범위·오차 → 이용 가능 시각 순으로 검사한다. NIFOS 논문 사례 4의 발화일과 첫 경계 날짜 불일치는 원자료 확인 전 자동 정정하지 않는다. 미관측·구름·부분 지도 영역을 음성으로 채우지 않는다.

사용자 위치가 관측 A에서 화재 밖, B에서 안쪽인 경우 도달 시각은 원칙적으로 **두 관측 사이의 구간 정답**이다. 일별 자료를 선형 보간해 1시간 실측 도달로 만들지 않는다. 예측 후보 지역과 피처는 예측 시점에 사용 가능한 자료로만 구성하고, 미래·최종 경계는 별도 정답으로 둔다.

## 4. 이번 단계의 사용 판단

새 토지피복은 정적 입력 보강에 사용할 수 있다. 국내 임상도 원본을 확보하면 수종·구조 정보의 추가 가능성이 있지만, 실측 연료량·수분·수관 구조와 국내 검증 없이 수종을 Scott–Burgan 모델 번호로 단정 매핑하지 않는다.

**국내 1~6시간 개인 영향 확률을 검증할 시간별 정답은 여전히 확보 단계다.** 이번 파일 확보만으로 개인 대응 판단이나 경보 수준에 확률값을 연결할 근거가 추가된 것은 아니다.

2025년 국내 사건이 포함된 검색 결과는 추가 논문·저장소·원자료 열람과 다운로드를 중단했다. 산림 포털의 일반 HTML에는 2025 메뉴·서비스 공지가 포함되어 있으나 해당 연도 사건 자료는 선택하거나 받지 않았다. 기존 국내 보류 정답, 소스 코드, 다른 에이전트 결과물은 변경하지 않았다.
