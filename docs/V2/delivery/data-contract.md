# 현재 수신·정책·앱 데이터 계약

2026-11-01 KST. 초기 Loom 계획의 산출물 경로를 현행 산불 MVP의 구현·검증 기록에 연결하는 완료 근거입니다. 아래 링크의 상세 문서·코드·보고서를 정본으로 사용합니다. 이번 상태 정리에서 서비스 배포나 모델 실행을 새로 수행하지 않았습니다.

현재 실행 계약은 [MVP OpenAPI](api/mvp-openapi.json)와 [앱 API](mvp-app-api.md)입니다. 이전0.1 초안과 실제 실행 계약을 구분합니다.

- [시나리오 봉투](../../../src/bonghwajigi/contracts/scenarios.py): simulation, scenario_id/event_id, urgent/analysis 및 synthetic/historical_replay/collected_sample 출처를 구분합니다. 현재 수신 봉투를 live 수집기라고 표시하지 않습니다.
- [문서·분석](../../../src/bonghwajigi/contracts/analysis.py): 원문 URL·게시/수집 시각·검토 상태, as_of와 유효기간, 문서 revision·origin을 검증합니다.
- [정책 입력](../../../src/bonghwajigi/contracts/policy.py)·[공간 문맥](../../../src/bonghwajigi/contracts/spatial.py)·[앱 입력](../../../src/bonghwajigi/contracts/app.py): 사건/사용자/위치/프로필/확인 상태·버전과 공식 경보를 분리합니다. 좌표·유효시각·결측을 안전 판정으로 바꾸지 않습니다.
- [재생 번들](../../../data/filming/yeongdeok-20250325.json)과 [출처 설명](filming-sources.md)은 원시 게시/관측 시각과 재생 observed_at/expires_at을 구분합니다.

동일 ID·동일 본문은 중복, 충돌 본문/역순 revision은 거부합니다. 구현과 검증은 [수신·분석 흐름](analysis-retrieval-flow.md), [사용자 세션과 동의/삭제](app-integration-api.md), [촬영 검증](filming-scenario-pipeline.md)에 있습니다. 실제 기관의 상시 live 수집·공간 분석은 별도 후속 범위입니다.
