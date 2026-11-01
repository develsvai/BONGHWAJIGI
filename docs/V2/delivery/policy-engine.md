# 사용자 상태와 결정적 정책 엔진

2026-11-01 KST. 초기 Loom 계획의 산출물 경로를 현행 산불 MVP의 구현·검증 기록에 연결하는 완료 근거입니다. 아래 링크의 상세 문서·코드·보고서를 정본으로 사용합니다. 이번 상태 정리에서 서비스 배포나 모델 실행을 새로 수행하지 않았습니다.

현행 정본은 [3단계 정책](response-policy.md), [실행 규칙](../../../src/bonghwajigi/policy/three_stage.py), [저장·재평가](../../../src/bonghwajigi/policy/service.py), [현재 앱 계약](mvp-app-api.md)입니다.

- 기본 행동지침·출처·검토 상태·규칙 버전에 최신 위치·프로필·사용자가 확인한 현재 상태를 결합합니다.
- 사전 프로필과 사건 중 상태를 분리하고, Qwen 추정은 확인 전 반영하지 않습니다.
- 동일한 입력·정책은 결정적으로 적용하며 입력/정책 버전·이유·근거를 남깁니다. 프로필·위치·확인 상태·지침 변경과 만료 시 재적용합니다.
- 공식 경보·개인 단계·연구 점수는 분리합니다. 예측 불가나 Qwen 오류가 공식 경보를 지우지 않습니다.

[최초 루프의 실제 검증](personal-policy-loop.md)은 당시 unknown단계 이력이며 현재단계는1경고·2대피·3위급입니다. [촬영 검증](filming-scenario-pipeline.md)과 [단계 시험](../../../tests/test_three_stage.py), [루프 시험](../../../tests/test_policy_loop.py), [사용자 대화 확인](../../../tests/test_mobile_interaction.py)에 후속 검증을 연결합니다.
