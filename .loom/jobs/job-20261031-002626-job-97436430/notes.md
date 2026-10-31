# Notes

## 2026-10-31T00:26:26+00:00

설계 기준은 docs/V2이며 HeoNey는 참고다. 앱 구현은 제외하고 앱팀에 API 명세를 제공한다. 이 등록은 작업 계약 고정이며 후속 구현 Task를 지금 실행하거나 Queue에 넣지 않는다. 기준 원문은 docs/V2/01, 02, 03 문서이고 실행 작업표는 docs/V2/04-execution-backlog.md이다. 등록 시 의존관계는 Job 경계를 넘어 적용한다.
- Tags: `v2`, `scope`, `backlog`
## 2026-10-31T00:50:01+00:00

GPU 상태 조회에서 NVIDIA L4 1대와 CUDA driver API 초기화 성공을 확인했다. 현재 기본 Python 3.12.3 환경에는 torch transformers vllm xgboost sentence-transformers numpy pandas 배포 메타데이터가 없고 Docker 실행 파일 및 nvcc도 PATH에서 확인되지 않았다. D3에서 전용 모델 환경과 실제 메모리 지연 동시성을 측정해야 한다. GPU 유휴 상태만으로 모델 처리량을 보장하지 않는다.

- Task: `task-20261031-002629-qwen-617b8d58`
- Tags: `infrastructure`, `model-runtime`
