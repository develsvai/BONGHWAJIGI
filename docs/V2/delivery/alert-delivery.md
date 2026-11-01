# 공식 원문 우선 알림 경로

2026-11-01 KST. 초기 Loom 계획의 산출물 경로를 현행 산불 MVP의 구현·검증 기록에 연결하는 완료 근거입니다. 아래 링크의 상세 문서·코드·보고서를 정본으로 사용합니다. 이번 상태 정리에서 서비스 배포나 모델 실행을 새로 수행하지 않았습니다.

[긴급 워커](../../../src/bonghwajigi/events/urgent.py)는 공식 출처·원문·발령 시각·대상 구역과 사용자 위치를 확인합니다. 임베딩·Qwen·연구 모델·개인 정책 완료를 기다리지 않고 경보 기록과 전달 작업을 먼저 만듭니다.

DB작업과 outbox의 원자 저장, 전용 urgent큐, 전달 revision·기기·lease·재시도·만료·정정/해제와 조회/수신 상태를 구분합니다. 위치가 불명확하면 임의로 대상 안에 있다고 확정하지 않습니다.

근거는 [확정 정책 및 공식 경보 처리](response-policy.md), [알림 구현](../../../src/bonghwajigi/notifications/delivery.py), [실제 촬영 검증](filming-scenario-pipeline.md), [검증 JSON](filming-pipeline-verification.json)입니다. 촬영의 원문 API노출 측정은 Qwen보다 먼저 끝났으며 휴대폰 종단 지연/SLA가 아닙니다.

현재 서버 제공자는 simulation입니다. 전경 단말의 로컬 배너·알림음과 실제FCM을 구분하며 Firebase자격·기기 준비 후 실발신/백그라운드수신을 별도 대기로 남깁니다. 자동119발신은 하지 않습니다.
