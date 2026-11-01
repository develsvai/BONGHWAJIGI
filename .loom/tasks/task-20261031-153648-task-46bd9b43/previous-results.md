# Previous Results

12 older recorded result(s) were omitted. Promote durable context to Job Notes or explicit Context References.

## 16. 외부 자원 문서에 고정 배포물 라이선스와 전체 API·출처 부록 병합

# 결과

발표 표 형식의 외부 자원 Markdown을 기존 검증 내용과 병합했다. 사용자 답변은 “사전 보유 코드 없음”으로 정확히 반영했다. 디자인·자료까지 없다고 확대하지 않았다.

- 외부 패키지·버전 174개, 기존 5개 환경 설치 154개/lock-only20개를 보존했다.
- CUDA/NVIDIA 36개 고정 버전 공식 wheel LICENSE를 추가 확인했다. NCCL BSD-3-Clause, NVTX LLVM 예외, NVSHMEM 배포물 EULA를 구분했다. cuda-toolkit 메타패키지 2개의 자체 LICENSE는 미확인이다.
- 일반 서버52개·GPU4개 API 동작, 원본URL51개·동적경로3개를 부록으로 추가했다.
- SafetyTV 제4유형, KMA 제품별 미확정 KOGL, ESA 구버전, CopDEM 전용조건 등 기존 검증을 보존했다. 모델 고정 revision 및 Embedding의 별도 LICENSE 부재를 정확히 설명했다.

검증: .venv/bin/python /private/tmp/bonghwa-validate-resource-doc.py 통과. 두 lock174쌍 누락/추가0, 직접 의존성 누락0, API56동작 일치, NVIDIA36확인, 4열표/로컬링크/인증정보 패턴 오류0. git diff --check 및 loom validate --strict 통과. 학습·서비스·배포를 변경하지 않았다.

산출물: docs/V2/delivery/external-resources-and-licenses.md, external-resources/supplemental-verification-20261101.json, external-resources/document-validation.json.

한계: 앱 감사와 전체 OS 바이너리 SBOM은 제외했다. 미확인 조건을 허가로 판정하지 않는다. 같은 버전의 모든 ABI/OS wheel을 검사했다는 뜻은 아니다. 사용자 후속 요청으로 앱 구현·검증·APK 배포는 별도 실행 계약에서 이어간다.

## 17. 외부 자원 명세 중복을 제거하고 단일 정본으로 통합

# 사용자 요청으로 취소

사용자가 “아 그래 오키 오키 그럼 그냥 놔둬”라고 답해 통합·삭제 요청을 철회했다. 지정 경로가 직전 산출물과 동일함을 확인했고, 본문 수정이나 파일 삭제 전에 중단했다. 기존 명세와 근거 JSON은 변경하지 않았다. 재개하려면 사용자의 새 지시가 필요하다.
