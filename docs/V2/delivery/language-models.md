# Qwen·Embedding의 현재 역할과 검증

2026-11-01 KST. 초기 Loom 계획의 산출물 경로를 현행 산불 MVP의 구현·검증 기록에 연결하는 완료 근거입니다. 아래 링크의 상세 문서·코드·보고서를 정본으로 사용합니다. 이번 상태 정리에서 서비스 배포나 모델 실행을 새로 수행하지 않았습니다.

GPU 서버의 Qwen3-4B-Instruct-2507과 Qwen3-Embedding-0.6B는 [고정 revision·실제 로딩·호출 검증](gpu-model-readiness.md)을 보존합니다. 임베딩은1024차원 벡터를 만들고, 유사 근거 검색은 PostgreSQL/pgvector가 수행합니다.

[수신→저장문서·웹검색→임베딩 검색](analysis-retrieval-flow.md), [경보를 포함한 Qwen 사건 통합](qwen-integration-result.md), [현재 대화·확인 상태](mobile-dialogue-and-route.md), [촬영 실제 모델 검증](filming-scenario-pipeline.md)이 후속 구현 근거입니다.

Qwen은 사건 자료를 정리하고 근거 있는 답변·상태 후보를 만듭니다. 최종 단계와 행동은 검토된 DB지침·고정 규칙이 정하며, 확인 전 상태 제안을 정책에 확정하지 않습니다. 모델 장애·지연 시 공식 원문·정책 경로와 템플릿 대체를 유지합니다. 새 문서가 정책을 자동 승인하지 않고 학습·추론 자원 경계도 유지합니다. 실제 사용자 위험 예측 모델 연결 완료를 뜻하지 않습니다.
