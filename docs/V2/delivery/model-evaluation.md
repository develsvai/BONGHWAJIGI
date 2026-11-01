# 모델 평가와 실제 예측 보류 판정

2026-11-01 KST. 초기 Loom 계획의 산출물 경로를 현행 산불 MVP의 구현·검증 기록에 연결하는 완료 근거입니다. 아래 링크의 상세 문서·코드·보고서를 정본으로 사용합니다. 이번 상태 정리에서 서비스 배포나 모델 실행을 새로 수행하지 않았습니다.

현재 판정은 **국내 개인 대응용 실제 확률 연결 보류**입니다. 연구의 일부 순위 지표 개선을 운영 확률의 타당성으로 해석하지 않습니다.

- [초기 CUDA 모델 독립 평가](xgboost-training-verification.md)는 미국 위성 관측 목표에 대한 결과이며 국내 사용자 영향 성능이 아닙니다.
- [보강 실험](../../../training/reports/model-strengthening-20261101/README.md), [국내 첫 관측 비교](../../../training/reports/korea-first-observation-20261101/README.md), [GFS2022 비교](../../../training/reports/korea-gfs-2022-20261101/README.md)는 기간·사건 분할, 기준선 대비 실패 지표와 보정 한계를 보존합니다.
- 최근 GFS 후보는 기존 입력·거리 기준 대비 채택하지 않았습니다. 화재 관측/재구성 경계·실제 화선·개인 피해·연기/경로 노출은 서로 다른 목표입니다.
- ELMFIRE 가정별 scenario_fraction을 검증된 확률로 변환하지 않습니다. source_asof·연료·국내 독립 정답의 공백을 유지합니다.

현재 API의 unavailable/null과 공식 경보 독립 전달은 [현재 앱 계약](mvp-app-api.md), [정책](response-policy.md)에 있습니다. 국내 정답·당시 입력 확보와 독립 평가·보정 후 재판정은 새 대기 태스크, 채택 모델의 CPU 연결·되돌리기는 기존 대기 태스크로 유지합니다.
