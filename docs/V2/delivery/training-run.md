# 실제 XGBoost 학습 실행과 저장 검증

2026-11-01 KST. 초기 Loom 계획의 산출물 경로를 현행 산불 MVP의 구현·검증 기록에 연결하는 완료 근거입니다. 아래 링크의 상세 문서·코드·보고서를 정본으로 사용합니다. 이번 상태 정리에서 서비스 배포나 모델 실행을 새로 수행하지 않았습니다.

[GPU 설치·합성 CUDA 연결](gpu-model-readiness.md), [실데이터 실행기](xgboost-training-run.md), [사용자가 실행한 CUDA 학습의 독립 재추론](xgboost-training-verification.md)이 완료 기록입니다.

실제 NDWS 학습은 저장 모델·데이터·피처 순서·트리 수·검증 및 최초 독립 test 평가를 재현했습니다. 이후 국내 관측·GOFER·GFS 개선 연구는 [개선 기록](korea-wildfire-improvement.md)과 [학습 README](../../../training/README.md)에 별도 분할·고정 계획·영수증·모델 SHA·재로딩·성공/실패 결과를 보존합니다.

최신 [GFS 비교 검증](../../../training/reports/korea-gfs-2022-20261101/verification.json)은45회 적합과 독립 수치 대조·전체542개 훈련 시험 통과를 기록합니다. 이는 과거 실행 근거이며 이번 Loom정리에서 재학습한 결과가 아닙니다. 연구 실행은 종료됐고 실서비스 모델·단계·알림을 바꾸지 않았습니다. 일반 서버 실제 CPU 모델 채택·교체·복구는 별도 대기 범위입니다.
