# Previous Results

11 older recorded result(s) were omitted. Promote durable context to Job Notes or explicit Context References.

## 15. 발표용 외부 API·모델·데이터·오픈소스와 라이선스 전수 정리

# 결과

사용자가 첨부한 발표 양식의 구분·명칭·용도·라이선스 형태로 `docs/V2/delivery/external-resources-and-licenses.md`를 작성했다. 서버·GPU 모델·학습 데이터·외부 API·뉴스/행동요령·기존 인프라·개발 도구를 실제 사용/확보/구성/조사로 구분했다. 사용자가 사전 보유·가져온 자료 없음을 확인하여 해당 없음으로 기록했다. 앱 저장소는 조회하지 않았다.

두 잠금 파일 139/71개 항목을 합친 외부 패키지·버전 174개를 모두 수록했다. 로컬/GPU 다섯 환경에서 154개 설치를 확인했고 20개 lock-only 분기를 구분했다. 직접 개발 패키지 2개 및 버전 범위만 선언된 Hatchling은 별도로 기록했다. 설치 METADATA와 동봉 LICENSE/NOTICE 경로·SHA, 공식 PyPI 버전별 metadata를 근거 JSON에 보존했다.

KMA FF의 승인 사용자 접근 제한과 미확정 제품별 KOGL 유형, ESA CCI 구버전 이용조건, Redis 7.4 RSALv2/SSPLv1, 안전한TV 제4유형, 뉴스 저작권, PostgreSQL pgvector 확장과 Python pgvector의 서로 다른 라이선스를 표시했다. Qwen 두 모델의 고정 revision 및 Apache2, NOAA/NASA/CC BY/전용 CopDEM 조건을 구분했다. API endpoint·인증·포맷·쿼터와 카탈로그만 조사한 경로도 설명했다.

검증: 외부 174개 전수 대조에서 누락/추가0, Markdown 행 누락0, 표4열 오류0, 로컬 링크 오류0, 인증정보 패턴0. `git diff --check`, `loom validate --strict` 통과. 문서/근거 파일 변경만 수행했으며 앱·서비스·학습 실행 설정은 변경하지 않았다. 기존 v4 수집·연구·utility 서비스는 읽기 점검에서 모두 active였으며 모델 개선 Task는 계속 RUNNING으로 유지한다.

범위 한계는 문서에 명시했다: 앱 자원 제외, OS/컨테이너 내부 전체 바이너리 SBOM 미작성, 미표기·판본 불명 라이선스를 허가로 간주하지 않음. 이는 자료 정리 완료이며 모든 자원의 재배포 권리를 확보했다는 뜻이 아니다.

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
