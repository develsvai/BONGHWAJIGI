# 경보 포함 Qwen3 통합 결과 — 추론 입력 직전

실행: **2026-10-31 19:40 KST**. 과거 영덕 산불 자료를 실제 분석 큐·임베딩·Qwen3로 처리했다. 공식 경보 발령 기록 1건과 근거 자료 5개를 묶었고, 모델이 선택한 근거 문장 3개의 출처 일치를 확인했다. 마지막 상태는 `pre_inference_review`다. XGBoost 추론·개인 대응 단계 결정·알림 발송은 실행하지 않았다.

이전에 제공한 `analysis-demo.json`은 합성 입력과 넓은 인터넷 검색 결과였고 공식 경보를 포함하지 않았다. 이번에는 공식 발령 기록과 지역·과거 시점을 지정한 별도 시나리오를 사용했다.

## Qwen3가 실제 작성한 통합 요약

> 당시 경상북도 영덕군 전 지역에 산불 확산이 보도됐으며, 산에서 떨어진 곳으로 대피가 안내됐다. 정부는 전국 산불경보를 심각 단계로 확대하고 국가소방동원령을 발동했다.

위 문장은 모델의 실제 출력이다. **2025년 과거 사건에 관한 내부 검토용 요약**이며 현재 사용자에게 보내는 대피 안내가 아니다. `summary_review_status=not_reviewed`, `approved_policy=false`로 저장했다. JSON 형식과 근거 인용의 일치는 자동 검사했지만 요약 전체의 의미·사실성을 자동 승인한 것은 아니다.

[생성 응답 원본](qwen-integration/generation-response.json)에서 모델이 돌려준 문자열·모델 revision·토큰 수·처리 시간을 확인할 수 있다. [모델에 보낸 자료와 지시](qwen-integration/generation-request.json)도 함께 보관했다.

## 이번에 포함한 재난 경보

| 항목 | 값 |
| --- | --- |
| 자료 종류 | 공식 게시물에 남은 과거 산불 위기경보 발령 기록 |
| 발령 기관 | 산림청 |
| 발령 시각 | 2025-03-25 16:00 KST |
| 대상 지역 | 전국 |
| 공식 등급 | 심각 |
| 원자료 | 2025-03-26 대한민국 정책브리핑의 발령·확대 사실 기록 |
| 직접 수신한 재난문자 원본 | 없음 (`original_sms_available=false`) |
| 현재 발효 여부 | 확인하지 않음 (`current_effective_status=not_checked`) |
| 개인별 대응 레벨 | 미결정·생성하지 않음 |

전국 경보 확대와 산림청 발령 사실은 [대한민국 정책브리핑 원자료](https://www.korea.kr/news/policyNewsView.do?newsId=148940993)에 근거한다. 발령 시각과 게시일을 별도 필드로 보존했다. 게시일만 공개되어 있어 `published_at`은 2025-03-26의 마지막 초를 상한으로 사용하고, 날짜 단위라는 표시도 남겼다.

발령 필드는 원자료를 확인해 작성한 시나리오 입력이다. Qwen이 경보 발령 여부를 판단한 결과는 아니다. 경보 기록은 검색 순위와 관계없이 통합 자료에 포함하며 모델이 등급·발령 시각·대상을 변경하도록 허용하지 않는다. 원문 짧은 발췌는 JSON의 `official_alerts[].original_excerpt`에 있다. 이 분석 시연에서는 경보를 발송하지 않는다. 실제 긴급 경보 수신·우선 전달 API는 아직 구현하지 않았고, 이 생성 과정을 기다리도록 연결하지 않았다.

## 무엇을 합쳤는가

재생 기준 시각은 **2025-03-27 00:00 KST**, 사건 지역 표시는 **경상북도 영덕군**이다. 지역명은 시나리오 작성자가 지정했으며 좌표 변환이나 사용자의 현 위치 확인은 수행하지 않았다.

인터넷 질의는 `산불 영덕 대피 after:2025-03-20 before:2025-03-28`이었다. RSS 결과 5건 중 발표 시각 조건을 적용하고 저장 문서까지 함께 임베딩 검색했다. 최종 통합 입력은 아래 5개다.

| 자료 | 성격 | 통합에 넣은 방식 |
| --- | --- | --- |
| 산불경보 심각 확대·경북 산불 상황 | 정책브리핑 공식 자료의 짧은 발췌와 작성자 요약 | 필수 근거로 고정 |
| 산불 발생 시 행동 요령 | 행정안전부 안전한TV 자료의 작성자 요약 | 필수 참고 자료로 고정, 정책 미승인 |
| 의성산불 확산에 영양·영덕군 주민 대피 재난문자 | 중앙일보, 인터넷 검색의 제목·짧은 설명 | 임베딩 검색 |
| 영덕군 전 지역 산불 확산·대피 안내 보도 | 연합뉴스TV, 인터넷 검색의 제목·짧은 설명 | 임베딩 검색 |
| 영덕군 전 지역 산불 확산·대피 안내 보도 | 연합뉴스, 인터넷 검색의 제목·짧은 설명 | 임베딩 검색 |

기본 행동요령의 원출처는 [행정안전부 안전한TV](https://www.safetv.go.kr/base/video/view?idx=2759&menuLevel=&menuNo=&playlistManagementIdx=8)다. 이번에는 참고 문서로 포함했으며 개인 정책 DB에 승인된 지침으로 등록하지 않았다. 나머지 뉴스 URL·발표/수집 시각·검색 점수는 [검색 결과 원본](qwen-integration/retrieval-handoff.json)에 있다. 서로 다른 URL의 유사 보도가 남아 있어 3개 뉴스가 독립적인 3개 확인을 뜻하지는 않는다.

Qwen3는 공식 자료의 경북 확산·대피·기반시설 장애 요약, 중앙일보의 주민 대피 재난문자 제목, 연합뉴스TV의 영덕군 대피 안내 제목을 근거로 선택했다. 각 `evidence_id`가 실제 입력 자료에 있고 `quote`가 해당 텍스트에 그대로 존재하는지 검사했다. 여기서 인용 대상은 보관한 요약·RSS 텍스트이며 뉴스 기사 본문 전체가 아니다.

## 추론 모델 앞에 남긴 자료

완전한 결과는 [추론 전 통합 JSON](qwen-integration/pre-inference.json)이다. 핵심 필드만 줄이면 다음과 같다.

```json
{
  "mode": "simulation",
  "origin": "historical_replay",
  "stage": "pre_inference_review",
  "incident": {
    "disaster_type": "wildfire",
    "area_name": "경상북도 영덕군",
    "coordinates": null,
    "grid_id": null
  },
  "user_context": {"profile": null, "location": null, "policy": null},
  "inference_gate": {
    "status": "blocked",
    "input_matrix_created": false,
    "xgboost_invoked": false,
    "probability": null,
    "personal_response_level": null
  }
}
```

사건 개요와 공식 경보는 통합했지만 **수치 추론에 투입할 행렬은 만들지 않았다.** 현재 저장소의 [학습 입력 계약](../../../training/reports/dataset-report.json)은 미국 NDWS 자료의 다음 일별 위성 화재 관측(`fire_next_day`)을 위한 20개 피처다. 개인의 산불 피해 확률을 바로 예측하는 계약이 아니며 국내 적용도 검증되지 않았다.

| 필요한 입력 | 이번 확보 상태 |
| --- | --- |
| 고도 `elevation`, 가뭄 `pdsi`, 식생 `NDVI` | 해당 격자의 관측값 없음 |
| 강수 `pr`, 비습 `sph`, 풍향 `th`, 최저/최고기온 `tmmn`/`tmmx`, 풍속 `vs` | 시간·격자·단위가 정렬된 자료 없음 |
| 연료 관련 `erc`, 인구 `population` | 학습과 같은 전처리·해상도의 입력 없음 |
| 이전 화재 관측 `PrevFireMask` | 위성 관측 격자 없음 |
| 주변 화재/관측 수, 거리, 풍향 sin/cos, 품질 지표 등 파생 피처 8개 | 원래 래스터가 없어 계산하지 않음 |
| 사용자 상태·현 위치·검토된 개인 정책 | 이번 시나리오에 없음 |

20개 값은 모두 `null`로 보존했다. 뉴스의 지역명이나 단편적인 수치를 격자 관측값으로 바꾸거나 임의 값으로 채우지 않는다. 차단 사유는 `MISSING_STRUCTURED_RASTER_INPUTS`, `MISSING_GRID_AND_GEOGRAPHIC_ALIGNMENT`, `MODEL_DOMAIN_NOT_VALIDATED_FOR_KOREA`다.

## 실제 실행과 검증

흐름: **공식 자료 확인 → 로컬 수신 API → PostgreSQL/outbox → Redis/Celery → L4 임베딩·인터넷 검색 → Qwen3 생성 → 근거 검사 → 추론 전 JSON 저장**.

| 항목 | 실제 결과 |
| --- | --- |
| 최종 실행 시각 | 2026-10-31 19:40:47 KST |
| 공식 사이트 확인 | 정책브리핑·안전한TV 모두 HTTP 200, 본문 표식 확인 및 HTML SHA256 기록 |
| 모델 | `Qwen/Qwen3-4B-Instruct-2507` |
| 고정 revision | `cdbee75f17c01a7cc42f958dc650907174af0554` |
| 생성 입력 / 출력 | 1,021 / 334토큰 |
| 모델 처리 시간 | 13,404.69ms (전체 파이프라인 시간과 다름) |
| 입력 예산 | 실제 서버 tokenizer 검사, 입력 + 출력 예약 512 ≤ 4,096 |
| 근거 인용 검사 | 3개 모두 출처 ID·원문 텍스트 일치 |
| 추론·정책·알림 | 실행하지 않음 |

첫 생성에서는 과거 뉴스의 대피 표현이 요약에서 권고형으로 남았다. 지시에 과거 보고체와 권고형 금지를 추가해 다시 실행했고 위 문서에는 두 번째 실제 결과를 보존했다. 모델 원문을 사람이 대신 고쳐서 모델 출력으로 표시하지 않았다.

게시일이 기준 시각 이후인 자료, 다른 시나리오, 근거 없는 경보 원문, 없는 출처·인용, 모델의 임의 수치 필드, 잘린 JSON·출력 토큰 한도 도달·다른 모델 revision을 거부하는 검사를 추가했다. **실제 DB를 사용한 기존 검사와 신규 검사를 합쳐 42개 통과**했고 Ruff 검사·포맷과 기존 앱 API 계약 검사도 통과했다. 최종 검증 기록은 Loom Task `task-20261031-103324-qwen3-b1f9a853`에 남긴다.

현재 수집한 과거 자료의 **발표 시각 기준 필터**를 적용했다. 현재의 검색 인덱스·수정된 게시물에서 확보했으므로 2025년 당시 실제로 수집할 수 있었는지까지 입증하는 백테스트는 아니다. 기본 지침과 뉴스의 적합성·최신성·정책 승인은 별도다.

## 직접 다시 실행하기

[분석 환경 안내](analysis-retrieval-flow.md)에 따라 `.env.analysis`, 로컬 DB/Redis, 기존 GPU SSH 터널과 `serve_analysis.py`를 준비한다. 기존 분석 API의 토큰과 GPU 토큰은 서로 별도다. 토큰을 명령행에 적지 않는다.

```sh
BONGHWA_ENV_FILE=.env.analysis uv run --no-sync python tools/run_integration_demo.py
```

기본 출력은 새 `data/artifacts/yeongdeok-.../` 디렉터리다. `--output-dir`로 경로를 정할 수 있고 기존 디렉터리를 덮어쓰지 않는다. 도구는 수신 API와 기존 분석 워커를 이용하고 그 다음 Qwen3를 한 번 호출한다. 분석 워커가 자동으로 생성 단계를 실행하는 배포 구성은 이번에 추가하지 않았다.

보관 파일: [시나리오 입력](qwen-integration/scenario-input.json), [공식 자료 확인](qwen-integration/source-checks.json), [검색 결과](qwen-integration/retrieval-handoff.json), [생성 요청](qwen-integration/generation-request.json), [생성 원본](qwen-integration/generation-response.json), [추론 전 JSON](qwen-integration/pre-inference.json), [실행 메타데이터](qwen-integration/run-metadata.json).
