# 결과

사용자가 첨부한 발표 양식의 구분·명칭·용도·라이선스 형태로 `docs/V2/delivery/external-resources-and-licenses.md`를 작성했다. 서버·GPU 모델·학습 데이터·외부 API·뉴스/행동요령·기존 인프라·개발 도구를 실제 사용/확보/구성/조사로 구분했다. 사용자가 사전 보유·가져온 자료 없음을 확인하여 해당 없음으로 기록했다. 앱 저장소는 조회하지 않았다.

두 잠금 파일 139/71개 항목을 합친 외부 패키지·버전 174개를 모두 수록했다. 로컬/GPU 다섯 환경에서 154개 설치를 확인했고 20개 lock-only 분기를 구분했다. 직접 개발 패키지 2개 및 버전 범위만 선언된 Hatchling은 별도로 기록했다. 설치 METADATA와 동봉 LICENSE/NOTICE 경로·SHA, 공식 PyPI 버전별 metadata를 근거 JSON에 보존했다.

KMA FF의 승인 사용자 접근 제한과 미확정 제품별 KOGL 유형, ESA CCI 구버전 이용조건, Redis 7.4 RSALv2/SSPLv1, 안전한TV 제4유형, 뉴스 저작권, PostgreSQL pgvector 확장과 Python pgvector의 서로 다른 라이선스를 표시했다. Qwen 두 모델의 고정 revision 및 Apache2, NOAA/NASA/CC BY/전용 CopDEM 조건을 구분했다. API endpoint·인증·포맷·쿼터와 카탈로그만 조사한 경로도 설명했다.

검증: 외부 174개 전수 대조에서 누락/추가0, Markdown 행 누락0, 표4열 오류0, 로컬 링크 오류0, 인증정보 패턴0. `git diff --check`, `loom validate --strict` 통과. 문서/근거 파일 변경만 수행했으며 앱·서비스·학습 실행 설정은 변경하지 않았다. 기존 v4 수집·연구·utility 서비스는 읽기 점검에서 모두 active였으며 모델 개선 Task는 계속 RUNNING으로 유지한다.

범위 한계는 문서에 명시했다: 앱 자원 제외, OS/컨테이너 내부 전체 바이너리 SBOM 미작성, 미표기·판본 불명 라이선스를 허가로 간주하지 않음. 이는 자료 정리 완료이며 모든 자원의 재배포 권리를 확보했다는 뜻이 아니다.
