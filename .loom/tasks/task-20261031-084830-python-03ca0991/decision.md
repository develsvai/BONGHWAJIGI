# 구현 결정

단일 Python 패키지를 공유하고 설치 extra 및 프로세스로 일반 API·수집·GPU·ML 환경을 분리했다. root import와 일반 API가 GPU 라이브러리를 요구하지 않게 했다. 각 Celery 앱은 자기 큐와 모듈만 로딩한다.

미구현 앱 경로를 성공 fixture로 제공하지 않았다. readiness와 내부 모델·시나리오 수신은 503이며 수집·학습 CLI는 --check 없이 종료 코드 2다. 기본 실행 모드는 simulation이고 시나리오 입력은 live를 거부한다.

사용자 추가 지시에 따라 MVP는 실제 K8s 수집의 선행 조건을 제외하고 확보 자료의 시나리오 → 이벤트 API → DB/outbox → 큐로 구성했다. 실제 수신·저장 구현은 후속 작업으로 남겼다. 장래 K8s 구조와 템플릿은 보존했다.

검토된 정책과 사용자의 대응 레벨 회의 결과를 기다리며 규칙·확률 임계값·모의 예측값은 추가하지 않았다. GPU 모델 설치 요청은 새 실행 Task로 이어간다. Verified Team Policy Snapshot은 없다.
