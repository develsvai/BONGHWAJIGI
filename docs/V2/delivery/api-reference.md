# API별 경로와 사용법 — 0.1.0 초안

모든 API는 미배포 계약이다. 아래 curl의 `API_BASE`는 발급받은 실제 개발 주소로 교체해야 하며 현재 제공된 주소는 없다. 성공 예제와 조건부 기능의 성공 분기는 화면 연동용 모의 자료다. 인증·버전·오류의 공통 의미는 [계약 문서](app-api-contract.md), 화면별 순서는 [앱팀 인계서](api-handoff.md)를 따른다.

```sh
API_BASE='https://api.example.invalid'
ACCESS_TOKEN='MOCK_ACCESS_TOKEN_NOT_VALID'
```

## 전체 경로

| operationId | 메서드·경로 | 대응 화면 | 범위 |
| --- | --- | --- | --- |
| [getAppConfig](#getAppConfig) | `GET /v1/app-config` | COMMON | 기본 계약 초안 |
| [getProfile](#getProfile) | `GET /v1/me/profile` | S4, S2 | 기본 계약 초안 |
| [replaceProfile](#replaceProfile) | `PUT /v1/me/profile` | S4 | 기본 계약 초안 |
| [deleteProfile](#deleteProfile) | `DELETE /v1/me/profile` | S4 | 기본 계약 초안 |
| [getPreferences](#getPreferences) | `GET /v1/me/preferences` | S4, COMMON | 기본 계약 초안 |
| [replacePreferences](#replacePreferences) | `PUT /v1/me/preferences` | S4 | 기본 계약 초안 |
| [getLocation](#getLocation) | `GET /v1/me/location` | COMMON, S1, S2 | 기본 계약 초안 |
| [putLocation](#putLocation) | `PUT /v1/me/location` | COMMON, S1, S2 | 기본 계약 초안 |
| [deleteLocation](#deleteLocation) | `DELETE /v1/me/location` | COMMON, S4 | 기본 계약 초안 |
| [putDevice](#putDevice) | `PUT /v1/me/devices/{installation_id}` | COMMON, S4 | 기본 계약 초안 |
| [deleteDevice](#deleteDevice) | `DELETE /v1/me/devices/{installation_id}` | COMMON, S4 | 기본 계약 초안 |
| [getHome](#getHome) | `GET /v1/home` | S1, COMMON | 기본 계약 초안 |
| [listDisasters](#listDisasters) | `GET /v1/disasters` | S1 | 기본 계약 초안 |
| [listAlerts](#listAlerts) | `GET /v1/me/alerts` | COMMON, S2 | 기본 계약 초안 |
| [getAlert](#getAlert) | `GET /v1/me/alerts/{alert_id}` | S2 | 기본 계약 초안 |
| [postAlertReceipt](#postAlertReceipt) | `POST /v1/me/alerts/{alert_id}/receipts` | COMMON, S2 | 기본 계약 초안 |
| [getResponse](#getResponse) | `GET /v1/me/responses/{response_id}` | S2 | 기본 계약 초안 |
| [putCurrentContext](#putCurrentContext) | `PUT /v1/me/responses/{response_id}/context` | S2 | 기본 계약 초안 |
| [getUpdates](#getUpdates) | `GET /v1/me/updates` | COMMON, S1, S2 | 기본 계약 초안 |
| [getSafetyRules](#getSafetyRules) | `GET /v1/safety-rules/{disaster_type}` | S5 | 기본 계약 초안 |
| [createSupportDraft](#createSupportDraft) | `POST /v1/me/responses/{response_id}/support-drafts` | S2 | 기본 계약 초안 |
| [getRoute](#getRoute) | `GET /v1/me/responses/{response_id}/route` | S2, S3 | 조건부 제안 |
| [createVoiceTurn](#createVoiceTurn) | `POST /v1/me/responses/{response_id}/voice-turns` | S2 | 조건부 제안 |
| [getVoiceTurn](#getVoiceTurn) | `GET /v1/me/responses/{response_id}/voice-turns/{turn_id}` | S2 | 조건부 제안 |
| [cancelVoiceTurn](#cancelVoiceTurn) | `DELETE /v1/me/responses/{response_id}/voice-turns/{turn_id}` | S2 | 조건부 제안 |

<a id="getAppConfig"></a>

## 기능·갱신 설정 조회

`GET /v1/app-config` · **getAppConfig**

**대응 화면:** COMMON 공통 초기화·알림·갱신

앱 시작 시 조회. false 기능은 호출/버튼 활성화를 하지 않는다. 설정값은 운영 성능 보장이 아닌 초안이다.

**호출 예시**

```sh
curl -sS -X GET "$API_BASE/v1/app-config"
```

**성공:** HTTP 200.
응답 스키마: `ConfigResponse`; `data`는 `Config`.

| data 필드 | 타입/허용값 |
| --- | --- |
| `contract_version` | '0.1.0' |
| `supported_locales` | array<string> |
| `default_locale` | string |
| `features` | object |
| `location_max_age_seconds` | integer |
| `location_max_accuracy_m` | integer |
| `updates_wait_seconds` | integer |
| `home_history_months` | 3 |
| `default_nearby_radius_m` | integer |
| `policy_status` | draft / reviewed |

<details>
<summary>모의 성공 응답 보기</summary>

```json
{
  "meta": {
    "schema_version": "0.1.0",
    "mode": "simulation",
    "request_id": "req_demo_001",
    "generated_at": "2026-10-31T03:00:00Z",
    "data_status": "current"
  },
  "data": {
    "contract_version": "0.1.0",
    "supported_locales": [
      "ko-KR"
    ],
    "default_locale": "ko-KR",
    "features": {
      "impact_prediction": {
        "enabled": false,
        "reason_code": "NOT_ADOPTED"
      },
      "route_3d": {
        "enabled": false,
        "reason_code": "NOT_ADOPTED"
      },
      "voice_turns": {
        "enabled": false,
        "reason_code": "NOT_ADOPTED"
      },
      "guidance_tts": {
        "enabled": false,
        "reason_code": "NOT_ADOPTED"
      },
      "support_draft": {
        "enabled": true,
        "reason_code": null
      }
    },
    "location_max_age_seconds": 300,
    "location_max_accuracy_m": 100,
    "updates_wait_seconds": 20,
    "home_history_months": 3,
    "default_nearby_radius_m": 5000,
    "policy_status": "draft"
  }
}
```

</details>

**오류:** `400`, `422`, `429`, `503`. [공통 오류 처리](app-api-contract.md#오류와-앱-처리)를 따른다.

예제 선택 키: [examples.json](api/examples.json)의 `id=getAppConfig`.

<a id="getProfile"></a>

## 사전 프로필 조회

`GET /v1/me/profile` · **getProfile**

**대응 화면:** S4 프로필 설정, S2 긴급 재난 대응

미등록이면 revision=0, profile={}를 반환한다. 모르는 상태를 정상 보행으로 채우지 않는다.

**호출 예시**

```sh
curl -sS -X GET "$API_BASE/v1/me/profile" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

**성공:** HTTP 200.
응답 스키마: `ProfileResponse`; `data`는 `Profile`.

| data 필드 | 타입/허용값 |
| --- | --- |
| `revision` | integer |
| `updated_at` | string (date-time) |
| `profile` | ProfileInput |

<details>
<summary>모의 성공 응답 보기</summary>

```json
{
  "meta": {
    "schema_version": "0.1.0",
    "mode": "simulation",
    "request_id": "req_demo_001",
    "generated_at": "2026-10-31T03:00:00Z",
    "data_status": "current"
  },
  "data": {
    "revision": 1,
    "updated_at": "2026-10-31T03:00:00Z",
    "profile": {
      "mobility": "independent",
      "stairs": "difficult",
      "communication_preference": "text",
      "sensory_supports": [],
      "dependents": []
    }
  }
}
```

</details>

**오류:** `400`, `401`, `403`, `422`, `429`, `503`. [공통 오류 처리](app-api-contract.md#오류와-앱-처리)를 따른다.

예제 선택 키: [examples.json](api/examples.json)의 `id=getProfile`.

<a id="replaceProfile"></a>

## 사전 프로필 전체 저장

`PUT /v1/me/profile` · **replaceProfile**

**대응 화면:** S4 프로필 설정

base_revision 일치 시 전체 교체. 생략한 필드는 삭제하고 미상 처리한다. 재난 당시 상태에는 쓰지 않는다.

**JSON 본문**

| 필드 | 필수 | 타입/허용값 |
| --- | --- | --- |
| `base_revision` | 예 | integer |
| `profile` | 예 | ProfileInput |

중첩 객체의 필드·허용값은 [OpenAPI](api/openapi.yaml)의 해당 스키마에 정의되어 있다.

**호출 예시**

```sh
curl -sS -X PUT "$API_BASE/v1/me/profile" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H 'Content-Type: application/json' \
  --data '{"base_revision":1,"profile":{"mobility":"independent","stairs":"difficult","communication_preference":"text","sensory_supports":[],"dependents":[]}}'
```

**성공:** HTTP 200.
응답 스키마: `ProfileResponse`; `data`는 `Profile`.

| data 필드 | 타입/허용값 |
| --- | --- |
| `revision` | integer |
| `updated_at` | string (date-time) |
| `profile` | ProfileInput |

<details>
<summary>모의 성공 응답 보기</summary>

```json
{
  "meta": {
    "schema_version": "0.1.0",
    "mode": "simulation",
    "request_id": "req_demo_001",
    "generated_at": "2026-10-31T03:00:00Z",
    "data_status": "current"
  },
  "data": {
    "revision": 2,
    "updated_at": "2026-10-31T03:00:00Z",
    "profile": {
      "mobility": "independent",
      "stairs": "difficult",
      "communication_preference": "text",
      "sensory_supports": [],
      "dependents": []
    }
  }
}
```

</details>

**오류:** `400`, `401`, `403`, `409`, `422`, `429`, `503`. [공통 오류 처리](app-api-contract.md#오류와-앱-처리)를 따른다.

예제 선택 키: [examples.json](api/examples.json)의 `id=replaceProfile`.

<a id="deleteProfile"></a>

## 사전 프로필 초기화

`DELETE /v1/me/profile` · **deleteProfile**

**대응 화면:** S4 프로필 설정

프로필만 삭제하며 계정 탈퇴가 아니다. 서버 revision은 증가시키고 연결된 안내를 재평가한다.

| 위치 | 필드 | 필수 | 타입/허용값 | 사용법 |
| --- | --- | --- | --- | --- |
| query | `base_revision` | 예 | integer | 현재 프로필 버전 |

**호출 예시**

```sh
curl -sS -X DELETE "$API_BASE/v1/me/profile?base_revision=1" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

**성공:** HTTP 204.
응답 본문 없음. 삭제 성공 후 해당 화면의 데이터/설치 등록 상태를 정리한다.

**오류:** `400`, `401`, `403`, `409`, `422`, `429`, `503`. [공통 오류 처리](app-api-contract.md#오류와-앱-처리)를 따른다.

예제 선택 키: [examples.json](api/examples.json)의 `id=deleteProfile`.

<a id="getPreferences"></a>

## 앱 설정 조회

`GET /v1/me/preferences` · **getPreferences**

**대응 화면:** S4 프로필 설정, COMMON 공통 초기화·알림·갱신

미등록이면 서버 기본값과 revision=0을 반환한다. OS 권한과 서버 설정은 별개다.

**호출 예시**

```sh
curl -sS -X GET "$API_BASE/v1/me/preferences" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

**성공:** HTTP 200.
응답 스키마: `PreferencesResponse`; `data`는 `Preferences`.

| data 필드 | 타입/허용값 |
| --- | --- |
| `revision` | integer |
| `updated_at` | string (date-time) |
| `preferences` | PreferencesInput |

<details>
<summary>모의 성공 응답 보기</summary>

```json
{
  "meta": {
    "schema_version": "0.1.0",
    "mode": "simulation",
    "request_id": "req_demo_001",
    "generated_at": "2026-10-31T03:00:00Z",
    "data_status": "current"
  },
  "data": {
    "revision": 1,
    "updated_at": "2026-10-31T03:00:00Z",
    "preferences": {
      "locale": "ko-KR",
      "notifications_enabled": true,
      "nearby_radius_m": 5000,
      "home_area_code": null
    }
  }
}
```

</details>

**오류:** `400`, `401`, `403`, `422`, `429`, `503`. [공통 오류 처리](app-api-contract.md#오류와-앱-처리)를 따른다.

예제 선택 키: [examples.json](api/examples.json)의 `id=getPreferences`.

<a id="replacePreferences"></a>

## 앱 설정 전체 저장

`PUT /v1/me/preferences` · **replacePreferences**

**대응 화면:** S4 프로필 설정

base_revision 일치 시 교체. 지원하지 않는 locale은 422 UNSUPPORTED_LOCALE. 관심 지역은 현재 GPS가 아니다.

**JSON 본문**

| 필드 | 필수 | 타입/허용값 |
| --- | --- | --- |
| `base_revision` | 예 | integer |
| `preferences` | 예 | PreferencesInput |

중첩 객체의 필드·허용값은 [OpenAPI](api/openapi.yaml)의 해당 스키마에 정의되어 있다.

**호출 예시**

```sh
curl -sS -X PUT "$API_BASE/v1/me/preferences" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H 'Content-Type: application/json' \
  --data '{"base_revision":1,"preferences":{"locale":"ko-KR","notifications_enabled":true,"nearby_radius_m":5000,"home_area_code":null}}'
```

**성공:** HTTP 200.
응답 스키마: `PreferencesResponse`; `data`는 `Preferences`.

| data 필드 | 타입/허용값 |
| --- | --- |
| `revision` | integer |
| `updated_at` | string (date-time) |
| `preferences` | PreferencesInput |

<details>
<summary>모의 성공 응답 보기</summary>

```json
{
  "meta": {
    "schema_version": "0.1.0",
    "mode": "simulation",
    "request_id": "req_demo_001",
    "generated_at": "2026-10-31T03:00:00Z",
    "data_status": "current"
  },
  "data": {
    "revision": 2,
    "updated_at": "2026-10-31T03:00:00Z",
    "preferences": {
      "locale": "ko-KR",
      "notifications_enabled": true,
      "nearby_radius_m": 5000,
      "home_area_code": null
    }
  }
}
```

</details>

**오류:** `400`, `401`, `403`, `409`, `422`, `429`, `503`. [공통 오류 처리](app-api-contract.md#오류와-앱-처리)를 따른다.

예제 선택 키: [examples.json](api/examples.json)의 `id=replacePreferences`.

<a id="getLocation"></a>

## 최신 위치 상태 조회

`GET /v1/me/location` · **getLocation**

**대응 화면:** COMMON 공통 초기화·알림·갱신, S1 평상시 홈, S2 긴급 재난 대응

위치 없음은 200 unavailable, fix=null. 현재 위치를 오래된 좌표로 대체 표시하지 않는다.

**호출 예시**

```sh
curl -sS -X GET "$API_BASE/v1/me/location" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

**성공:** HTTP 200.
응답 스키마: `LocationResponse`; `data`는 `Location`.

| data 필드 | 타입/허용값 |
| --- | --- |
| `revision` | integer |
| `status` | available / stale / inaccurate / unavailable |
| `fix` | LocationWrite 또는 null |
| `valid_until` | string (date-time) 또는 null |
| `reason_codes` | array<string> |

<details>
<summary>모의 성공 응답 보기</summary>

```json
{
  "meta": {
    "schema_version": "0.1.0",
    "mode": "simulation",
    "request_id": "req_demo_001",
    "generated_at": "2026-10-31T03:00:00Z",
    "data_status": "current"
  },
  "data": {
    "revision": 1,
    "status": "available",
    "fix": {
      "fix_id": "fix_demo_001",
      "installation_id": "install_demo_001",
      "latitude": 37.505,
      "longitude": 127.005,
      "accuracy_m": 20,
      "captured_at": "2026-10-31T03:00:00Z"
    },
    "valid_until": "2026-10-31T03:05:00Z",
    "reason_codes": []
  }
}
```

</details>

**오류:** `400`, `401`, `403`, `422`, `429`, `503`. [공통 오류 처리](app-api-contract.md#오류와-앱-처리)를 따른다.

예제 선택 키: [examples.json](api/examples.json)의 `id=getLocation`.

<a id="putLocation"></a>

## GPS 위치 갱신

`PUT /v1/me/location` · **putLocation**

**대응 화면:** COMMON 공통 초기화·알림·갱신, S1 평상시 홈, S2 긴급 재난 대응

fix_id로 중복 제거. 이전 captured_at은 409 STALE_LOCATION; 미래 120초 초과는 422. 정확도·최신성 불충족은 수신하되 status를 inaccurate/stale로 반환. 새 관련성 평가는 비동기다.

**JSON 본문**

| 필드 | 필수 | 타입/허용값 |
| --- | --- | --- |
| `fix_id` | 예 | string |
| `installation_id` | 예 | string |
| `latitude` | 예 | number |
| `longitude` | 예 | number |
| `accuracy_m` | 예 | number |
| `captured_at` | 예 | string (date-time) |

중첩 객체의 필드·허용값은 [OpenAPI](api/openapi.yaml)의 해당 스키마에 정의되어 있다.

**호출 예시**

```sh
curl -sS -X PUT "$API_BASE/v1/me/location" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H 'Content-Type: application/json' \
  --data '{"fix_id":"fix_demo_001","installation_id":"install_demo_001","latitude":37.505,"longitude":127.005,"accuracy_m":20,"captured_at":"2026-10-31T03:00:00Z"}'
```

**성공:** HTTP 200.
응답 스키마: `LocationResponse`; `data`는 `Location`.

| data 필드 | 타입/허용값 |
| --- | --- |
| `revision` | integer |
| `status` | available / stale / inaccurate / unavailable |
| `fix` | LocationWrite 또는 null |
| `valid_until` | string (date-time) 또는 null |
| `reason_codes` | array<string> |

<details>
<summary>모의 성공 응답 보기</summary>

```json
{
  "meta": {
    "schema_version": "0.1.0",
    "mode": "simulation",
    "request_id": "req_demo_001",
    "generated_at": "2026-10-31T03:00:00Z",
    "data_status": "current"
  },
  "data": {
    "revision": 1,
    "status": "available",
    "fix": {
      "fix_id": "fix_demo_001",
      "installation_id": "install_demo_001",
      "latitude": 37.505,
      "longitude": 127.005,
      "accuracy_m": 20,
      "captured_at": "2026-10-31T03:00:00Z"
    },
    "valid_until": "2026-10-31T03:05:00Z",
    "reason_codes": []
  }
}
```

</details>

**오류:** `400`, `401`, `403`, `409`, `422`, `429`, `503`. [공통 오류 처리](app-api-contract.md#오류와-앱-처리)를 따른다.

예제 선택 키: [examples.json](api/examples.json)의 `id=putLocation`.

<a id="deleteLocation"></a>

## 서버의 최신 위치 제거

`DELETE /v1/me/location` · **deleteLocation**

**대응 화면:** COMMON 공통 초기화·알림·갱신, S4 프로필 설정

권한 철회 시 호출. 최신 위치를 제거하고 안내/경로를 재평가한다. 성공 후 앱의 최신 위치 캐시도 비운다. 보관 로그의 전체 삭제 API는 별도 정책 대상이다.

| 위치 | 필드 | 필수 | 타입/허용값 | 사용법 |
| --- | --- | --- | --- | --- |
| query | `base_revision` | 예 | integer | 현재 위치 버전 |

**호출 예시**

```sh
curl -sS -X DELETE "$API_BASE/v1/me/location?base_revision=1" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

**성공:** HTTP 204.
응답 본문 없음. 삭제 성공 후 해당 화면의 데이터/설치 등록 상태를 정리한다.

**오류:** `400`, `401`, `403`, `409`, `422`, `429`, `503`. [공통 오류 처리](app-api-contract.md#오류와-앱-처리)를 따른다.

예제 선택 키: [examples.json](api/examples.json)의 `id=deleteLocation`.

<a id="putDevice"></a>

## 설치별 푸시 등록·갱신

`PUT /v1/me/devices/{installation_id}` · **putDevice**

**대응 화면:** COMMON 공통 초기화·알림·갱신, S4 프로필 설정

토큰 갱신·권한 변경 시 호출. 설치 소유권을 토큰 주체에 묶고 다른 계정 소유 식별자는 404. push_token=null 또는 권한 거부이면 비활성. 실제 토큰은 응답/로그에 노출하지 않는다.

| 위치 | 필드 | 필수 | 타입/허용값 | 사용법 |
| --- | --- | --- | --- | --- |
| path | `installation_id` | 예 | string | 호출자 소유의 리소스 식별자 |

**JSON 본문**

| 필드 | 필수 | 타입/허용값 |
| --- | --- | --- |
| `platform` | 예 | android / ios / web |
| `push_provider` | 예 | fcm / apns |
| `push_token` | 예 | string 또는 null |
| `notification_permission` | 예 | granted / denied / not_determined |
| `app_version` | 예 | string |

중첩 객체의 필드·허용값은 [OpenAPI](api/openapi.yaml)의 해당 스키마에 정의되어 있다.

**호출 예시**

```sh
curl -sS -X PUT "$API_BASE/v1/me/devices/install_demo_001" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H 'Content-Type: application/json' \
  --data '{"platform":"android","push_provider":"fcm","push_token":"MOCK_PUSH_TOKEN_NOT_VALID","notification_permission":"granted","app_version":"0.1.0"}'
```

**성공:** HTTP 200.
응답 스키마: `DeviceResponse`; `data`는 `Device`.

| data 필드 | 타입/허용값 |
| --- | --- |
| `installation_id` | string |
| `registered_at` | string (date-time) |
| `push_status` | registered / disabled |
| `notification_permission` | granted / denied / not_determined |

<details>
<summary>모의 성공 응답 보기</summary>

```json
{
  "meta": {
    "schema_version": "0.1.0",
    "mode": "simulation",
    "request_id": "req_demo_001",
    "generated_at": "2026-10-31T03:00:00Z",
    "data_status": "current"
  },
  "data": {
    "installation_id": "install_demo_001",
    "registered_at": "2026-10-31T03:00:00Z",
    "push_status": "registered",
    "notification_permission": "granted"
  }
}
```

</details>

**오류:** `400`, `401`, `403`, `404`, `422`, `429`, `503`. [공통 오류 처리](app-api-contract.md#오류와-앱-처리)를 따른다.

예제 선택 키: [examples.json](api/examples.json)의 `id=putDevice`.

<a id="deleteDevice"></a>

## 설치별 푸시 등록 해제

`DELETE /v1/me/devices/{installation_id}` · **deleteDevice**

**대응 화면:** COMMON 공통 초기화·알림·갱신, S4 프로필 설정

로그아웃 시 호출. 이미 삭제되어도 204. 소유권 확인 후 처리한다.

| 위치 | 필드 | 필수 | 타입/허용값 | 사용법 |
| --- | --- | --- | --- | --- |
| path | `installation_id` | 예 | string | 호출자 소유의 리소스 식별자 |

**호출 예시**

```sh
curl -sS -X DELETE "$API_BASE/v1/me/devices/install_demo_001" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

**성공:** HTTP 204.
응답 본문 없음. 삭제 성공 후 해당 화면의 데이터/설치 등록 상태를 정리한다.

**오류:** `400`, `401`, `403`, `404`, `422`, `429`, `503`. [공통 오류 처리](app-api-contract.md#오류와-앱-처리)를 따른다.

예제 선택 키: [examples.json](api/examples.json)의 `id=deleteDevice`.

<a id="getHome"></a>

## 홈 스냅샷 조회

`GET /v1/home` · **getHome**

**대응 화면:** S1 평상시 홈, COMMON 공통 초기화·알림·갱신

오늘 수칙, 주변 목록, 활성 경보/안내 ID와 sync_cursor를 함께 제공한다. 현재 위치 불가이면 선택 지역이 없는 한 feed.scope=unavailable. 선택 지역 조회는 GPS 기반 긴급 대상 판정을 바꾸지 않는다.

| 위치 | 필드 | 필수 | 타입/허용값 | 사용법 |
| --- | --- | --- | --- | --- |
| query | `scope` | 아니오 | current_location / selected_area | 기본 current_location. selected_area는 area_code 필수. |
| query | `area_code` | 아니오 | string | selected_area에서만 사용. 서버 승인 지역코드; 임의 주소/좌표를 넣지 않는다. |
| query | `limit` | 아니오 | integer | 페이지 항목 수 기본 20 |

**호출 예시**

```sh
curl -sS -X GET "$API_BASE/v1/home?scope=current_location&limit=20" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

**성공:** HTTP 200.
응답 스키마: `HomeResponse`; `data`는 `Home`.

| data 필드 | 타입/허용값 |
| --- | --- |
| `sync_cursor` | string |
| `location` | Location |
| `today_rules` | DailyGuidance |
| `feed` | Feed |
| `active_alert_ids` | array<string> |
| `active_response_ids` | array<string> |
| `capabilities` | object |

<details>
<summary>모의 성공 응답 보기</summary>

```json
{
  "meta": {
    "schema_version": "0.1.0",
    "mode": "simulation",
    "request_id": "req_demo_001",
    "generated_at": "2026-10-31T03:00:00Z",
    "data_status": "current"
  },
  "data": {
    "sync_cursor": "cursor_demo_100",
    "location": {
      "revision": 1,
      "status": "available",
      "fix": {
        "fix_id": "fix_demo_001",
        "installation_id": "install_demo_001",
        "latitude": 37.505,
        "longitude": 127.005,
        "accuracy_m": 20,
        "captured_at": "2026-10-31T03:00:00Z"
      },
      "valid_until": "2026-10-31T03:05:00Z",
      "reason_codes": []
    },
    "today_rules": {
      "for_date": "2026-10-31",
      "scope": "current_location",
      "status": "available",
      "locale": "ko-KR",
      "locale_fallback": false,
      "valid_until": "2026-10-31T03:05:00Z",
      "items": [
        {
          "id": "daily_demo_001",
          "title": "[시연] 오늘의 안전 정보",
          "text": "[시연] 검토된 오늘의 안전 행동요령 표시 영역입니다.",
          "disaster_type": "other",
          "source_id": "src_demo_001",
          "content_version": "demo-only"
        }
      ],
      "sources": [
        {
          "id": "src_demo_001",
          "kind": "simulation",
          "agency": "시연용 기관(가상)",
          "url": "https://example.invalid/sources/demo-001",
          "published_at": "2026-10-31T03:00:00Z",
          "observed_at": null,
          "collected_at": "2026-10-31T03:00:00Z",
          "valid_until": "2026-10-31T03:05:00Z",
          "document_revision": "demo-1",
          "independent_origin_id": "origin_demo_001"
        }
      ]
    },
    "feed": {
      "items": [
        {
          "id": "evt_demo_past",
          "disaster_type": "flood",
          "status": "past",
          "display_title": "[시연] 가상 지역 침수 기록",
          "original_title": "[시연] 가상 지역 침수 발생",
          "region_label": "가상 지역",
          "occurred_at": "2026-10-01T03:00:00Z",
          "ended_at": "2026-10-02T03:00:00Z",
          "updated_at": "2026-10-31T03:00:00Z",
          "summary": "실제 사건이 아닌 화면 연동용 자료입니다.",
          "source": {
            "id": "src_demo_001",
            "kind": "simulation",
            "agency": "시연용 기관(가상)",
            "url": "https://example.invalid/sources/demo-001",
            "published_at": "2026-10-31T03:00:00Z",
            "observed_at": null,
            "collected_at": "2026-10-31T03:00:00Z",
            "valid_until": "2026-10-31T03:05:00Z",
            "document_revision": "demo-1",
            "independent_origin_id": "origin_demo_001"
          },
          "detail_navigation": false
        }
      ],
      "next_cursor": null,
      "scope": "current_location",
      "area_code": null,
      "radius_m": 5000,
      "window_start": "2026-07-31T03:00:00Z",
      "window_end": "2026-10-31T03:00:00Z",
      "snapshot_at": "2026-10-31T03:00:00Z",
      "data_status": "current"
    },
    "active_alert_ids": [
      "alert_demo_001"
    ],
    "active_response_ids": [
      "response_demo_001"
    ],
    "capabilities": {
      "route_3d": {
        "enabled": false,
        "reason_code": "NOT_ADOPTED"
      },
      "voice_turns": {
        "enabled": false,
        "reason_code": "NOT_ADOPTED"
      },
      "guidance_tts": {
        "enabled": false,
        "reason_code": "NOT_ADOPTED"
      },
      "support_draft": {
        "enabled": true,
        "reason_code": null
      }
    }
  }
}
```

</details>

**오류:** `400`, `401`, `403`, `422`, `429`, `503`. [공통 오류 처리](app-api-contract.md#오류와-앱-처리)를 따른다.

예제 선택 키: [examples.json](api/examples.json)의 `id=getHome`.

<a id="listDisasters"></a>

## 주변 재난 목록 추가 조회

`GET /v1/disasters` · **listDisasters**

**대응 화면:** S1 평상시 홈

홈과 같은 범위/정렬의 목록. ongoing은 시작 시각과 무관하게 포함, past는 종료 시각이 최근 3개월 구간인 항목. 과거 display_title에는 발생 표현을 넣지 않는다. 상세 화면 진입 API가 아니다.

| 위치 | 필드 | 필수 | 타입/허용값 | 사용법 |
| --- | --- | --- | --- | --- |
| query | `scope` | 아니오 | current_location / selected_area | 기본 current_location. selected_area는 area_code 필수. |
| query | `area_code` | 아니오 | string | selected_area에서만 사용. 서버 승인 지역코드; 임의 주소/좌표를 넣지 않는다. |
| query | `limit` | 아니오 | integer | 페이지 항목 수 기본 20 |
| query | `cursor` | 아니오 | string | 홈 feed.next_cursor. 동일 조회 조건과 snapshot_at 유지. |

**호출 예시**

```sh
curl -sS -X GET "$API_BASE/v1/disasters?scope=current_location&limit=20" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

**성공:** HTTP 200.
응답 스키마: `FeedResponse`; `data`는 `Feed`.

| data 필드 | 타입/허용값 |
| --- | --- |
| `items` | array<FeedItem> |
| `next_cursor` | string 또는 null |
| `scope` | current_location / selected_area / unavailable |
| `area_code` | string 또는 null |
| `radius_m` | integer |
| `window_start` | string (date-time) |
| `window_end` | string (date-time) |
| `snapshot_at` | string (date-time) |
| `data_status` | current / partial / stale / unavailable |

<details>
<summary>모의 성공 응답 보기</summary>

```json
{
  "meta": {
    "schema_version": "0.1.0",
    "mode": "simulation",
    "request_id": "req_demo_001",
    "generated_at": "2026-10-31T03:00:00Z",
    "data_status": "current"
  },
  "data": {
    "items": [
      {
        "id": "evt_demo_past",
        "disaster_type": "flood",
        "status": "past",
        "display_title": "[시연] 가상 지역 침수 기록",
        "original_title": "[시연] 가상 지역 침수 발생",
        "region_label": "가상 지역",
        "occurred_at": "2026-10-01T03:00:00Z",
        "ended_at": "2026-10-02T03:00:00Z",
        "updated_at": "2026-10-31T03:00:00Z",
        "summary": "실제 사건이 아닌 화면 연동용 자료입니다.",
        "source": {
          "id": "src_demo_001",
          "kind": "simulation",
          "agency": "시연용 기관(가상)",
          "url": "https://example.invalid/sources/demo-001",
          "published_at": "2026-10-31T03:00:00Z",
          "observed_at": null,
          "collected_at": "2026-10-31T03:00:00Z",
          "valid_until": "2026-10-31T03:05:00Z",
          "document_revision": "demo-1",
          "independent_origin_id": "origin_demo_001"
        },
        "detail_navigation": false
      }
    ],
    "next_cursor": null,
    "scope": "current_location",
    "area_code": null,
    "radius_m": 5000,
    "window_start": "2026-07-31T03:00:00Z",
    "window_end": "2026-10-31T03:00:00Z",
    "snapshot_at": "2026-10-31T03:00:00Z",
    "data_status": "current"
  }
}
```

</details>

**오류:** `400`, `401`, `403`, `410`, `422`, `429`, `503`. [공통 오류 처리](app-api-contract.md#오류와-앱-처리)를 따른다.

예제 선택 키: [examples.json](api/examples.json)의 `id=listDisasters`.

<a id="listAlerts"></a>

## 개인 경보 목록 조회

`GET /v1/me/alerts` · **listAlerts**

**대응 화면:** COMMON 공통 초기화·알림·갱신, S2 긴급 재난 대응

처음에는 status=active 기본. active는 active/updated 포함. all은 취소/만료 이력도 포함한다.

| 위치 | 필드 | 필수 | 타입/허용값 | 사용법 |
| --- | --- | --- | --- | --- |
| query | `status` | 아니오 | active / all | 기본 active |
| query | `cursor` | 아니오 | string | 다음 페이지 커서 |
| query | `limit` | 아니오 | integer | 기본 20 |

**호출 예시**

```sh
curl -sS -X GET "$API_BASE/v1/me/alerts?limit=20" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

**성공:** HTTP 200.
응답 스키마: `AlertListResponse`; `data`는 `AlertList`.

| data 필드 | 타입/허용값 |
| --- | --- |
| `items` | array<Alert> |
| `next_cursor` | string 또는 null |

<details>
<summary>모의 성공 응답 보기</summary>

```json
{
  "meta": {
    "schema_version": "0.1.0",
    "mode": "simulation",
    "request_id": "req_demo_001",
    "generated_at": "2026-10-31T03:00:00Z",
    "data_status": "current"
  },
  "data": {
    "items": [
      {
        "id": "alert_demo_001",
        "revision": 1,
        "event_id": "evt_demo_001",
        "response_id": "response_demo_001",
        "disaster_type": "flood",
        "status": "active",
        "title": "[시연] 가상 지역 공식 경보",
        "official_severity": {
          "code": null,
          "label": null,
          "scheme": null
        },
        "instruction_kind": "information",
        "original_text": "[시연 자료] 실제 발령된 경보가 아닙니다.",
        "issued_at": "2026-10-31T03:00:00Z",
        "received_at": "2026-10-31T03:00:00Z",
        "valid_until": "2026-10-31T03:05:00Z",
        "target_area": {
          "type": "Polygon",
          "coordinates": [
            [
              [
                127.0,
                37.5
              ],
              [
                127.01,
                37.5
              ],
              [
                127.01,
                37.51
              ],
              [
                127.0,
                37.51
              ],
              [
                127.0,
                37.5
              ]
            ]
          ]
        },
        "source": {
          "id": "src_demo_001",
          "kind": "simulation",
          "agency": "시연용 기관(가상)",
          "url": "https://example.invalid/sources/demo-001",
          "published_at": "2026-10-31T03:00:00Z",
          "observed_at": null,
          "collected_at": "2026-10-31T03:00:00Z",
          "valid_until": "2026-10-31T03:05:00Z",
          "document_revision": "demo-1",
          "independent_origin_id": "origin_demo_001"
        }
      }
    ],
    "next_cursor": null
  }
}
```

</details>

**오류:** `400`, `401`, `403`, `410`, `422`, `429`, `503`. [공통 오류 처리](app-api-contract.md#오류와-앱-처리)를 따른다.

예제 선택 키: [examples.json](api/examples.json)의 `id=listAlerts`.

<a id="getAlert"></a>

## 개인 경보 원문 조회

`GET /v1/me/alerts/{alert_id}` · **getAlert**

**대응 화면:** S2 긴급 재난 대응

공식 원문·등급·발령 시각을 GPU/개인 안내/지도보다 먼저 표시한다. 취소된 경보도 최신 status로 반환한다. 원문에 없는 대피 명령 제목을 만들지 않는다.

| 위치 | 필드 | 필수 | 타입/허용값 | 사용법 |
| --- | --- | --- | --- | --- |
| path | `alert_id` | 예 | string | 호출자 소유의 리소스 식별자 |

**호출 예시**

```sh
curl -sS -X GET "$API_BASE/v1/me/alerts/alert_demo_001" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

**성공:** HTTP 200.
응답 스키마: `AlertResponse`; `data`는 `Alert`.

| data 필드 | 타입/허용값 |
| --- | --- |
| `id` | string |
| `revision` | integer |
| `event_id` | string |
| `response_id` | string 또는 null |
| `disaster_type` | flood / fire / wildfire / earthquake / heatwave / other |
| `status` | active / updated / cancelled / expired |
| `title` | string |
| `official_severity` | object |
| `instruction_kind` | evacuate / shelter / prepare / information / unknown |
| `original_text` | string |
| `issued_at` | string (date-time) |
| `received_at` | string (date-time) |
| `valid_until` | string (date-time) 또는 null |
| `target_area` | AreaGeometry 또는 null |
| `source` | Source |

<details>
<summary>모의 성공 응답 보기</summary>

```json
{
  "meta": {
    "schema_version": "0.1.0",
    "mode": "simulation",
    "request_id": "req_demo_001",
    "generated_at": "2026-10-31T03:00:00Z",
    "data_status": "current"
  },
  "data": {
    "id": "alert_demo_001",
    "revision": 1,
    "event_id": "evt_demo_001",
    "response_id": "response_demo_001",
    "disaster_type": "flood",
    "status": "active",
    "title": "[시연] 가상 지역 공식 경보",
    "official_severity": {
      "code": null,
      "label": null,
      "scheme": null
    },
    "instruction_kind": "information",
    "original_text": "[시연 자료] 실제 발령된 경보가 아닙니다.",
    "issued_at": "2026-10-31T03:00:00Z",
    "received_at": "2026-10-31T03:00:00Z",
    "valid_until": "2026-10-31T03:05:00Z",
    "target_area": {
      "type": "Polygon",
      "coordinates": [
        [
          [
            127.0,
            37.5
          ],
          [
            127.01,
            37.5
          ],
          [
            127.01,
            37.51
          ],
          [
            127.0,
            37.51
          ],
          [
            127.0,
            37.5
          ]
        ]
      ]
    },
    "source": {
      "id": "src_demo_001",
      "kind": "simulation",
      "agency": "시연용 기관(가상)",
      "url": "https://example.invalid/sources/demo-001",
      "published_at": "2026-10-31T03:00:00Z",
      "observed_at": null,
      "collected_at": "2026-10-31T03:00:00Z",
      "valid_until": "2026-10-31T03:05:00Z",
      "document_revision": "demo-1",
      "independent_origin_id": "origin_demo_001"
    }
  }
}
```

</details>

**오류:** `400`, `401`, `403`, `404`, `422`, `429`, `503`. [공통 오류 처리](app-api-contract.md#오류와-앱-처리)를 따른다.

예제 선택 키: [examples.json](api/examples.json)의 `id=getAlert`.

<a id="postAlertReceipt"></a>

## 단말 표시·열람 보고

`POST /v1/me/alerts/{alert_id}/receipts` · **postAlertReceipt**

**대응 화면:** COMMON 공통 초기화·알림·갱신, S2 긴급 재난 대응

단말이 관측한 received/displayed/opened만 보고한다. 사용자의 대피·안전·신고 완료를 뜻하지 않는다. 과거 경보 revision 수신 보고도 기록하되 현재 상태는 바꾸지 않는다.

| 위치 | 필드 | 필수 | 타입/허용값 | 사용법 |
| --- | --- | --- | --- | --- |
| path | `alert_id` | 예 | string | 호출자 소유의 리소스 식별자 |
| header | `Idempotency-Key` | 예 | string | 동일 요청 재시도는 같은 키 사용. 사용자+메서드+경로별 24시간 보관 제안. 같은 키/다른 본문은 409. |

**JSON 본문**

| 필드 | 필수 | 타입/허용값 |
| --- | --- | --- |
| `alert_revision` | 예 | integer |
| `installation_id` | 예 | string |
| `event` | 예 | received / displayed / opened |
| `occurred_at` | 예 | string (date-time) |

중첩 객체의 필드·허용값은 [OpenAPI](api/openapi.yaml)의 해당 스키마에 정의되어 있다.

**호출 예시**

```sh
curl -sS -X POST "$API_BASE/v1/me/alerts/alert_demo_001/receipts" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H 'Idempotency-Key: demo-request-0001' \
  -H 'Content-Type: application/json' \
  --data '{"alert_revision":1,"installation_id":"install_demo_001","event":"opened","occurred_at":"2026-10-31T03:00:00Z"}'
```

**성공:** HTTP 201.
응답 스키마: `ReceiptResponse`; `data`는 `Receipt`.

| data 필드 | 타입/허용값 |
| --- | --- |
| `receipt_id` | string |
| `recorded_at` | string (date-time) |
| `meaning` | 'client_reported_only' |

<details>
<summary>모의 성공 응답 보기</summary>

```json
{
  "meta": {
    "schema_version": "0.1.0",
    "mode": "simulation",
    "request_id": "req_demo_001",
    "generated_at": "2026-10-31T03:00:00Z",
    "data_status": "current"
  },
  "data": {
    "receipt_id": "receipt_demo_001",
    "recorded_at": "2026-10-31T03:00:00Z",
    "meaning": "client_reported_only"
  }
}
```

</details>

**오류:** `400`, `401`, `403`, `404`, `409`, `422`, `429`, `503`. [공통 오류 처리](app-api-contract.md#오류와-앱-처리)를 따른다.

예제 선택 키: [examples.json](api/examples.json)의 `id=postAlertReceipt`.

<a id="getResponse"></a>

## 긴급 화면의 개인별 안내 조회

`GET /v1/me/responses/{response_id}` · **getResponse**

**대응 화면:** S2 긴급 재난 대응

공식 경보, 주변 영향 근거, 확률 사용 가능 여부, 개인 대응 단계, 현재 태그, 번호별 행동을 원자적인 revision으로 제공한다. unavailable 확률은 null이며 0이 아니다.

| 위치 | 필드 | 필수 | 타입/허용값 | 사용법 |
| --- | --- | --- | --- | --- |
| path | `response_id` | 예 | string | 호출자 소유의 리소스 식별자 |

**호출 예시**

```sh
curl -sS -X GET "$API_BASE/v1/me/responses/response_demo_001" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

**성공:** HTTP 200.
응답 스키마: `ResponseSnapshotResponse`; `data`는 `ResponseSnapshot`.

| data 필드 | 타입/허용값 |
| --- | --- |
| `id` | string |
| `revision` | integer |
| `event_id` | string |
| `disaster_type` | flood / fire / wildfire / earthquake / heatwave / other |
| `status` | active / resolved / superseded / expired |
| `superseded_by` | string 또는 null |
| `evaluated_at` | string (date-time) |
| `valid_until` | string (date-time) |
| `input_versions` | object |
| `official_alert` | Alert 또는 null |
| `relevance` | Relevance |
| `impact` | Impact |
| `personal_response` | object |
| `location` | Location |
| `affected_area` | AreaGeometry 또는 null |
| `area_source_ids` | array<string> |
| `context` | Context |
| `assistant_utterance` | Utterance 또는 null |
| `actions` | array<RuleItem> |
| `route_availability` | RouteAvailability |
| `sources` | array<Source> |

<details>
<summary>모의 성공 응답 보기</summary>

```json
{
  "meta": {
    "schema_version": "0.1.0",
    "mode": "simulation",
    "request_id": "req_demo_001",
    "generated_at": "2026-10-31T03:00:00Z",
    "data_status": "current"
  },
  "data": {
    "id": "response_demo_001",
    "revision": 1,
    "event_id": "evt_demo_001",
    "disaster_type": "flood",
    "status": "active",
    "superseded_by": null,
    "evaluated_at": "2026-10-31T03:00:00Z",
    "valid_until": "2026-10-31T03:05:00Z",
    "input_versions": {
      "profile": 1,
      "location": 1,
      "context": 1
    },
    "official_alert": {
      "id": "alert_demo_001",
      "revision": 1,
      "event_id": "evt_demo_001",
      "response_id": "response_demo_001",
      "disaster_type": "flood",
      "status": "active",
      "title": "[시연] 가상 지역 공식 경보",
      "official_severity": {
        "code": null,
        "label": null,
        "scheme": null
      },
      "instruction_kind": "information",
      "original_text": "[시연 자료] 실제 발령된 경보가 아닙니다.",
      "issued_at": "2026-10-31T03:00:00Z",
      "received_at": "2026-10-31T03:00:00Z",
      "valid_until": "2026-10-31T03:05:00Z",
      "target_area": {
        "type": "Polygon",
        "coordinates": [
          [
            [
              127.0,
              37.5
            ],
            [
              127.01,
              37.5
            ],
            [
              127.01,
              37.51
            ],
            [
              127.0,
              37.51
            ],
            [
              127.0,
              37.5
            ]
          ]
        ]
      },
      "source": {
        "id": "src_demo_001",
        "kind": "simulation",
        "agency": "시연용 기관(가상)",
        "url": "https://example.invalid/sources/demo-001",
        "published_at": "2026-10-31T03:00:00Z",
        "observed_at": null,
        "collected_at": "2026-10-31T03:00:00Z",
        "valid_until": "2026-10-31T03:05:00Z",
        "document_revision": "demo-1",
        "independent_origin_id": "origin_demo_001"
      }
    },
    "relevance": {
      "status": "possible",
      "relationship": "upstream",
      "origin_region_label": "가상 상류 지역",
      "target_region_label": "가상 현재 지역",
      "summary": "[시연] 주변 상류 사건과 현재 지역의 관련성을 평가 중입니다.",
      "evidence_source_ids": [
        "src_demo_001"
      ]
    },
    "impact": {
      "status": "unavailable",
      "probability": null,
      "target": null,
      "model_version": null,
      "reason_codes": [
        "MODEL_NOT_VALIDATED"
      ]
    },
    "personal_response": {
      "level": "unknown",
      "label": "판단에 필요한 정보를 확인 중",
      "policy_version": null,
      "reason_codes": [
        "POLICY_NOT_REVIEWED"
      ]
    },
    "location": {
      "revision": 1,
      "status": "available",
      "fix": {
        "fix_id": "fix_demo_001",
        "installation_id": "install_demo_001",
        "latitude": 37.505,
        "longitude": 127.005,
        "accuracy_m": 20,
        "captured_at": "2026-10-31T03:00:00Z"
      },
      "valid_until": "2026-10-31T03:05:00Z",
      "reason_codes": []
    },
    "affected_area": {
      "type": "Polygon",
      "coordinates": [
        [
          [
            127.0,
            37.5
          ],
          [
            127.01,
            37.5
          ],
          [
            127.01,
            37.51
          ],
          [
            127.0,
            37.51
          ],
          [
            127.0,
            37.5
          ]
        ]
      ]
    },
    "area_source_ids": [
      "src_demo_001"
    ],
    "context": {
      "revision": 1,
      "expires_at": null,
      "tags": [
        {
          "code": "stairs_difficult",
          "label": "계단 이용 어려움",
          "origin": "profile",
          "confirmed_at": "2026-10-31T03:00:00Z",
          "expires_at": null
        }
      ]
    },
    "assistant_utterance": {
      "id": "utter_demo_001",
      "text": "[시연] 현재 상태를 확인해 주세요.",
      "origin": "template",
      "created_at": "2026-10-31T03:00:00Z"
    },
    "actions": [
      {
        "id": "rule_demo_001",
        "order": 1,
        "text": "[시연] 검토된 기관 행동요령이 이 위치에 표시됩니다.",
        "source_id": "src_demo_001",
        "rule_version": "demo-only"
      }
    ],
    "route_availability": {
      "status": "unavailable",
      "reason_code": "NOT_ADOPTED",
      "expires_at": null
    },
    "sources": [
      {
        "id": "src_demo_001",
        "kind": "simulation",
        "agency": "시연용 기관(가상)",
        "url": "https://example.invalid/sources/demo-001",
        "published_at": "2026-10-31T03:00:00Z",
        "observed_at": null,
        "collected_at": "2026-10-31T03:00:00Z",
        "valid_until": "2026-10-31T03:05:00Z",
        "document_revision": "demo-1",
        "independent_origin_id": "origin_demo_001"
      }
    ]
  }
}
```

</details>

**오류:** `400`, `401`, `403`, `404`, `422`, `429`, `503`. [공통 오류 처리](app-api-contract.md#오류와-앱-처리)를 따른다.

예제 선택 키: [examples.json](api/examples.json)의 `id=getResponse`.

<a id="putCurrentContext"></a>

## 사용자가 확인한 현재 상태 저장

`PUT /v1/me/responses/{response_id}/context` · **putCurrentContext**

**대응 화면:** S2 긴급 재난 대응

확인된 현재 상태만 반영한다. null 이동/계단 값은 프로필 상속, alone_now=unknown은 미확인이다. 60분 후 재확인 제안; 사전 프로필은 바꾸지 않는다. 모델 제안은 사용자 확인 전 저장 금지.

| 위치 | 필드 | 필수 | 타입/허용값 | 사용법 |
| --- | --- | --- | --- | --- |
| path | `response_id` | 예 | string | 호출자 소유의 리소스 식별자 |

**JSON 본문**

| 필드 | 필수 | 타입/허용값 |
| --- | --- | --- |
| `base_revision` | 예 | integer |
| `observed_at` | 예 | string (date-time) |
| `confirmation` | 예 | 'user_confirmed' |
| `overrides` | 예 | object |

중첩 객체의 필드·허용값은 [OpenAPI](api/openapi.yaml)의 해당 스키마에 정의되어 있다.

**호출 예시**

```sh
curl -sS -X PUT "$API_BASE/v1/me/responses/response_demo_001/context" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H 'Content-Type: application/json' \
  --data '{"base_revision":1,"observed_at":"2026-10-31T03:00:00Z","confirmation":"user_confirmed","overrides":{"mobility":null,"stairs":"unable","alone_now":"yes"}}'
```

**성공:** HTTP 200.
응답 스키마: `ContextAcceptedResponse`; `data`는 `ContextAccepted`.

| data 필드 | 타입/허용값 |
| --- | --- |
| `context_revision` | integer |
| `response_id` | string |
| `expires_at` | string (date-time) |
| `reevaluation` | 'pending' |

<details>
<summary>모의 성공 응답 보기</summary>

```json
{
  "meta": {
    "schema_version": "0.1.0",
    "mode": "simulation",
    "request_id": "req_demo_001",
    "generated_at": "2026-10-31T03:00:00Z",
    "data_status": "current"
  },
  "data": {
    "context_revision": 2,
    "response_id": "response_demo_001",
    "expires_at": "2026-10-31T04:00:00Z",
    "reevaluation": "pending"
  }
}
```

</details>

**오류:** `400`, `401`, `403`, `404`, `409`, `422`, `429`, `503`. [공통 오류 처리](app-api-contract.md#오류와-앱-처리)를 따른다.

예제 선택 키: [examples.json](api/examples.json)의 `id=putCurrentContext`.

<a id="getUpdates"></a>

## 전경 앱 변경 이벤트 조회

`GET /v1/me/updates` · **getUpdates**

**대응 화면:** COMMON 공통 초기화·알림·갱신, S1 평상시 홈, S2 긴급 재난 대응

home.sync_cursor부터 long polling. 최대 25초 대기 후 변화 없으면 빈 events와 진행 커서. cursor 24시간 만료 제안; 만료/조회 범위 변경은 410으로 홈부터 재동기화. push는 별도 전달 수단이다.

| 위치 | 필드 | 필수 | 타입/허용값 | 사용법 |
| --- | --- | --- | --- | --- |
| query | `after` | 예 | string | 마지막 처리 완료 커서 |
| query | `wait_seconds` | 아니오 | integer | 기본 20 |

**호출 예시**

```sh
curl -sS -X GET "$API_BASE/v1/me/updates?after=cursor_demo_100&wait_seconds=20" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

**성공:** HTTP 200.
응답 스키마: `UpdatesResponse`; `data`는 `Updates`.

| data 필드 | 타입/허용값 |
| --- | --- |
| `events` | array<UpdateEvent> |
| `next_cursor` | string |
| `has_more` | boolean |

<details>
<summary>모의 성공 응답 보기</summary>

```json
{
  "meta": {
    "schema_version": "0.1.0",
    "mode": "simulation",
    "request_id": "req_demo_001",
    "generated_at": "2026-10-31T03:00:00Z",
    "data_status": "current"
  },
  "data": {
    "events": [
      {
        "event_id": "update_demo_001",
        "type": "alert.upserted",
        "resource_id": "alert_demo_001",
        "resource_revision": 1,
        "response_id": "response_demo_001",
        "occurred_at": "2026-10-31T03:00:00Z"
      }
    ],
    "next_cursor": "cursor_demo_101",
    "has_more": false
  }
}
```

</details>

**오류:** `400`, `401`, `403`, `410`, `422`, `429`, `503`. [공통 오류 처리](app-api-contract.md#오류와-앱-처리)를 따른다.

예제 선택 키: [examples.json](api/examples.json)의 `id=getUpdates`.

<a id="getSafetyRules"></a>

## 재난별 기본 수칙 조회

`GET /v1/safety-rules/{disaster_type}` · **getSafetyRules**

**대응 화면:** S5 재난별 기본 수칙

공식 기관 근거의 검토된 콘텐츠만 반환한다. 지원 재난/자료가 없으면 200 status=unavailable 및 items=[]. 출처·버전·번역 fallback을 표시한다.

| 위치 | 필드 | 필수 | 타입/허용값 | 사용법 |
| --- | --- | --- | --- | --- |
| path | `disaster_type` | 예 | flood / fire / wildfire / earthquake / heatwave / other | 호출자 소유의 리소스 식별자 |
| query | `locale` | 아니오 | ko-KR / en-US | 기본 ko-KR. 번역이 없으면 원문과 locale_fallback=true. |

**호출 예시**

```sh
curl -sS -X GET "$API_BASE/v1/safety-rules/flood?locale=ko-KR" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

**성공:** HTTP 200.
응답 스키마: `RulesResponse`; `data`는 `Rules`.

| data 필드 | 타입/허용값 |
| --- | --- |
| `disaster_type` | flood / fire / wildfire / earthquake / heatwave / other |
| `locale` | string |
| `locale_fallback` | boolean |
| `status` | available / unavailable |
| `content_version` | string 또는 null |
| `reviewed_at` | string (date-time) 또는 null |
| `items` | array<RuleItem> |
| `sources` | array<Source> |

<details>
<summary>모의 성공 응답 보기</summary>

```json
{
  "meta": {
    "schema_version": "0.1.0",
    "mode": "simulation",
    "request_id": "req_demo_001",
    "generated_at": "2026-10-31T03:00:00Z",
    "data_status": "current"
  },
  "data": {
    "disaster_type": "flood",
    "locale": "ko-KR",
    "locale_fallback": false,
    "status": "available",
    "content_version": "demo-only",
    "reviewed_at": null,
    "items": [
      {
        "id": "rule_demo_001",
        "order": 1,
        "text": "[시연] 검토된 기관 행동요령이 이 위치에 표시됩니다.",
        "source_id": "src_demo_001",
        "rule_version": "demo-only"
      }
    ],
    "sources": [
      {
        "id": "src_demo_001",
        "kind": "simulation",
        "agency": "시연용 기관(가상)",
        "url": "https://example.invalid/sources/demo-001",
        "published_at": "2026-10-31T03:00:00Z",
        "observed_at": null,
        "collected_at": "2026-10-31T03:00:00Z",
        "valid_until": "2026-10-31T03:05:00Z",
        "document_revision": "demo-1",
        "independent_origin_id": "origin_demo_001"
      }
    ]
  }
}
```

</details>

**오류:** `400`, `401`, `403`, `422`, `429`, `503`. [공통 오류 처리](app-api-contract.md#오류와-앱-처리)를 따른다.

예제 선택 키: [examples.json](api/examples.json)의 `id=getSafetyRules`.

<a id="createSupportDraft"></a>

## 119 문자 미리보기 구성

`POST /v1/me/responses/{response_id}/support-drafts` · **createSupportDraft**

**대응 화면:** S2 긴급 재난 대응

사용자가 요청한 미리보기만 작성하며 전송·전화·접수를 수행하지 않는다. 포함 요청이 있어도 오래되거나 미확인인 위치/상태는 현재 사실처럼 쓰지 않는다. 현재 안내 revision 불일치는 409.

| 위치 | 필드 | 필수 | 타입/허용값 | 사용법 |
| --- | --- | --- | --- | --- |
| path | `response_id` | 예 | string | 호출자 소유의 리소스 식별자 |
| header | `Idempotency-Key` | 예 | string | 동일 요청 재시도는 같은 키 사용. 사용자+메서드+경로별 24시간 보관 제안. 같은 키/다른 본문은 409. |

**JSON 본문**

| 필드 | 필수 | 타입/허용값 |
| --- | --- | --- |
| `response_revision` | 예 | integer |
| `include_location` | 예 | boolean |
| `include_confirmed_state` | 예 | boolean |
| `user_requested_preview` | 예 | True |

중첩 객체의 필드·허용값은 [OpenAPI](api/openapi.yaml)의 해당 스키마에 정의되어 있다.

**호출 예시**

```sh
curl -sS -X POST "$API_BASE/v1/me/responses/response_demo_001/support-drafts" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H 'Idempotency-Key: demo-request-0001' \
  -H 'Content-Type: application/json' \
  --data '{"response_revision":1,"include_location":true,"include_confirmed_state":true,"user_requested_preview":true}'
```

**성공:** HTTP 201.
응답 스키마: `SupportDraftResponse`; `data`는 `SupportDraft`.

| data 필드 | 타입/허용값 |
| --- | --- |
| `draft_id` | string |
| `response_revision` | integer |
| `preview_text` | string |
| `phone_number` | '119' |
| `location_status` | available / stale / unavailable |
| `expires_at` | string (date-time) |
| `delivery_status` | 'not_sent' |
| `requires_user_confirmation` | True |

<details>
<summary>모의 성공 응답 보기</summary>

```json
{
  "meta": {
    "schema_version": "0.1.0",
    "mode": "simulation",
    "request_id": "req_demo_001",
    "generated_at": "2026-10-31T03:00:00Z",
    "data_status": "current"
  },
  "data": {
    "draft_id": "draft_demo_001",
    "response_revision": 1,
    "preview_text": "[시연 전용·전송 금지] 가상 위치와 사용자가 확인한 상태의 문자 미리보기입니다.",
    "phone_number": "119",
    "location_status": "available",
    "expires_at": "2026-10-31T03:05:00Z",
    "delivery_status": "not_sent",
    "requires_user_confirmation": true
  }
}
```

</details>

**오류:** `400`, `401`, `403`, `404`, `409`, `422`, `429`, `501`, `503`. [공통 오류 처리](app-api-contract.md#오류와-앱-처리)를 따른다.

예제 선택 키: [examples.json](api/examples.json)의 `id=createSupportDraft`.

<a id="getRoute"></a>

## 조건부 3D 경로 자료 조회

`GET /v1/me/responses/{response_id}/route` · **getRoute**

**대응 화면:** S2 긴급 재난 대응, S3 3D 대피로

미채택/자료 없음도 200 unavailable이다. 버튼은 현재 안내에서 available이고 미만료일 때만 표시한다. 요청한 response_revision 불일치·현재 상태 변경은 409; 기존 선을 제거하고 안내를 다시 조회한다. 상세 3D 화면 배치는 보류다.

**조건부 기능:** 현재 기본 비활성. 성공 예제는 채택 이후를 대비한 계약이고, 앱은 capability를 확인한 뒤 호출한다.

| 위치 | 필드 | 필수 | 타입/허용값 | 사용법 |
| --- | --- | --- | --- | --- |
| path | `response_id` | 예 | string | 호출자 소유의 리소스 식별자 |
| query | `response_revision` | 예 | integer | 현재 안내 버전 |

**호출 예시**

```sh
curl -sS -X GET "$API_BASE/v1/me/responses/response_demo_001/route?response_revision=1" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

**성공:** HTTP 200.
응답 스키마: `RouteResponse`; `data`는 `Route`.

| data 필드 | 타입/허용값 |
| --- | --- |
| `status` | available / unavailable / pending |
| `response_revision` | integer |
| `reason_code` | string 또는 null |
| `route` | RouteData 또는 null |
| `sources` | array<Source> |

<details>
<summary>모의 성공 응답 보기</summary>

```json
{
  "meta": {
    "schema_version": "0.1.0",
    "mode": "simulation",
    "request_id": "req_demo_001",
    "generated_at": "2026-10-31T03:00:00Z",
    "data_status": "current"
  },
  "data": {
    "status": "unavailable",
    "response_revision": 1,
    "reason_code": "NOT_ADOPTED",
    "route": null,
    "sources": []
  }
}
```

</details>

**오류:** `400`, `401`, `403`, `404`, `409`, `422`, `429`, `503`. [공통 오류 처리](app-api-contract.md#오류와-앱-처리)를 따른다.

예제 선택 키: [examples.json](api/examples.json)의 `id=getRoute`.

<a id="createVoiceTurn"></a>

## 조건부 발화 텍스트 처리 요청

`POST /v1/me/responses/{response_id}/voice-turns` · **createVoiceTurn**

**대응 화면:** S2 긴급 재난 대응

음성 범위 채택 후에만 사용한다. 입력은 단말에서 얻은 텍스트이며 오디오 스트리밍 규격이 아니다. STT/실시간 전이중/끼어들기 구현은 별도 협의. 현 버전 기본 disabled로 501. 성공 분기는 채택 이후의 계약 예제다.

**조건부 기능:** 현재 기본 비활성. 성공 예제는 채택 이후를 대비한 계약이고, 앱은 capability를 확인한 뒤 호출한다.

| 위치 | 필드 | 필수 | 타입/허용값 | 사용법 |
| --- | --- | --- | --- | --- |
| path | `response_id` | 예 | string | 호출자 소유의 리소스 식별자 |
| header | `Idempotency-Key` | 예 | string | 동일 요청 재시도는 같은 키 사용. 사용자+메서드+경로별 24시간 보관 제안. 같은 키/다른 본문은 409. |

**JSON 본문**

| 필드 | 필수 | 타입/허용값 |
| --- | --- | --- |
| `client_turn_id` | 예 | string |
| `response_revision` | 예 | integer |
| `captured_at` | 예 | string (date-time) |
| `transcript` | 예 | string |
| `locale` | 예 | ko-KR / en-US |

중첩 객체의 필드·허용값은 [OpenAPI](api/openapi.yaml)의 해당 스키마에 정의되어 있다.

**호출 예시**

```sh
curl -sS -X POST "$API_BASE/v1/me/responses/response_demo_001/voice-turns" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H 'Idempotency-Key: demo-request-0001' \
  -H 'Content-Type: application/json' \
  --data '{"client_turn_id":"client_turn_demo_001","response_revision":1,"captured_at":"2026-10-31T03:00:00Z","transcript":"계단을 이용하기 어렵습니다.","locale":"ko-KR"}'
```

**성공:** HTTP 202.
응답 스키마: `VoiceTurnResponse`; `data`는 `VoiceTurn`.

| data 필드 | 타입/허용값 |
| --- | --- |
| `turn_id` | string |
| `client_turn_id` | string |
| `response_revision` | integer |
| `status` | pending / ready / failed / cancelled / expired |
| `utterance` | Utterance 또는 null |
| `proposed_context` | ContextProposal 또는 null |
| `audio_url` | string (uri) 또는 null |
| `audio_expires_at` | string (date-time) 또는 null |
| `reason_code` | string 또는 null |
| `expires_at` | string (date-time) |

<details>
<summary>모의 성공 응답 보기</summary>

```json
{
  "meta": {
    "schema_version": "0.1.0",
    "mode": "simulation",
    "request_id": "req_demo_001",
    "generated_at": "2026-10-31T03:00:00Z",
    "data_status": "current"
  },
  "data": {
    "turn_id": "turn_demo_001",
    "client_turn_id": "client_turn_demo_001",
    "response_revision": 1,
    "status": "pending",
    "utterance": null,
    "proposed_context": null,
    "audio_url": null,
    "audio_expires_at": null,
    "reason_code": null,
    "expires_at": "2026-10-31T03:05:00Z"
  }
}
```

</details>

**오류:** `400`, `401`, `403`, `404`, `409`, `422`, `429`, `501`, `503`. [공통 오류 처리](app-api-contract.md#오류와-앱-처리)를 따른다.

예제 선택 키: [examples.json](api/examples.json)의 `id=createVoiceTurn`.

<a id="getVoiceTurn"></a>

## 조건부 발화 처리 결과 조회

`GET /v1/me/responses/{response_id}/voice-turns/{turn_id}` · **getVoiceTurn**

**대응 화면:** S2 긴급 재난 대응

최신 client_turn_id와 response_revision 결과만 화면에 반영한다. proposed_context는 자동 저장하지 않는다. 사용자 발화는 화면/히스토리에 표시하지 않는다. audio_url은 별도 TTS 채택 시만 허용된다.

**조건부 기능:** 현재 기본 비활성. 성공 예제는 채택 이후를 대비한 계약이고, 앱은 capability를 확인한 뒤 호출한다.

| 위치 | 필드 | 필수 | 타입/허용값 | 사용법 |
| --- | --- | --- | --- | --- |
| path | `turn_id` | 예 | string | 호출자 소유의 리소스 식별자 |
| path | `response_id` | 예 | string | 호출자 소유의 리소스 식별자 |

**호출 예시**

```sh
curl -sS -X GET "$API_BASE/v1/me/responses/response_demo_001/voice-turns/turn_demo_001" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

**성공:** HTTP 200.
응답 스키마: `VoiceTurnResponse`; `data`는 `VoiceTurn`.

| data 필드 | 타입/허용값 |
| --- | --- |
| `turn_id` | string |
| `client_turn_id` | string |
| `response_revision` | integer |
| `status` | pending / ready / failed / cancelled / expired |
| `utterance` | Utterance 또는 null |
| `proposed_context` | ContextProposal 또는 null |
| `audio_url` | string (uri) 또는 null |
| `audio_expires_at` | string (date-time) 또는 null |
| `reason_code` | string 또는 null |
| `expires_at` | string (date-time) |

<details>
<summary>모의 성공 응답 보기</summary>

```json
{
  "meta": {
    "schema_version": "0.1.0",
    "mode": "simulation",
    "request_id": "req_demo_001",
    "generated_at": "2026-10-31T03:00:00Z",
    "data_status": "current"
  },
  "data": {
    "turn_id": "turn_demo_001",
    "client_turn_id": "client_turn_demo_001",
    "response_revision": 1,
    "status": "ready",
    "utterance": {
      "id": "utter_demo_confirm",
      "text": "[시연] 현재 계단 이용이 어려운 상태가 맞나요?",
      "origin": "template",
      "created_at": "2026-10-31T03:00:00Z"
    },
    "proposed_context": {
      "overrides": {
        "mobility": null,
        "stairs": "difficult",
        "alone_now": "unknown"
      },
      "requires_user_confirmation": true
    },
    "audio_url": null,
    "audio_expires_at": null,
    "reason_code": null,
    "expires_at": "2026-10-31T03:05:00Z"
  }
}
```

</details>

**오류:** `400`, `401`, `403`, `404`, `422`, `429`, `501`, `503`. [공통 오류 처리](app-api-contract.md#오류와-앱-처리)를 따른다.

예제 선택 키: [examples.json](api/examples.json)의 `id=getVoiceTurn`.

<a id="cancelVoiceTurn"></a>

## 조건부 발화 처리 취소

`DELETE /v1/me/responses/{response_id}/voice-turns/{turn_id}` · **cancelVoiceTurn**

**대응 화면:** S2 긴급 재난 대응

단말 재생을 즉시 중단한 후 서버 처리를 취소한다. 이미 종료된 요청도 204. 늦게 오는 이전 발화 결과는 앱에서 버린다.

**조건부 기능:** 현재 기본 비활성. 성공 예제는 채택 이후를 대비한 계약이고, 앱은 capability를 확인한 뒤 호출한다.

| 위치 | 필드 | 필수 | 타입/허용값 | 사용법 |
| --- | --- | --- | --- | --- |
| path | `turn_id` | 예 | string | 호출자 소유의 리소스 식별자 |
| path | `response_id` | 예 | string | 호출자 소유의 리소스 식별자 |

**호출 예시**

```sh
curl -sS -X DELETE "$API_BASE/v1/me/responses/response_demo_001/voice-turns/turn_demo_001" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

**성공:** HTTP 204.
응답 본문 없음. 삭제 성공 후 해당 화면의 데이터/설치 등록 상태를 정리한다.

**오류:** `400`, `401`, `403`, `404`, `422`, `429`, `501`, `503`. [공통 오류 처리](app-api-contract.md#오류와-앱-처리)를 따른다.

예제 선택 키: [examples.json](api/examples.json)의 `id=cancelVoiceTurn`.
