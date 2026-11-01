# Previous Results

10 older recorded result(s) were omitted. Promote durable context to Job Notes or explicit Context References.

## 14. 일반 서버에 산불 MVP를 상시 배포하고 예측 제외 통합 시연 검증

# 산불 MVP 일반 서버 배포 완료

일반 서버 inno-server-011에 실행 커밋 654a9ef의 Docker 이미지를 배포하고 상시 실행/부팅 등록을 완료했다. API·긴급·분석·전달·outbox·정책·Qwen 통합 7개 프로세스, PostgreSQL/pgvector·Redis 2개, 정상 완료된 migration 1개다. 실제 예측 연결은 사용자 지시로 제외하며 앱 예측은 unavailable/null이다. 앱 저장소와 진행 중인 training 작업은 수정하지 않았다.

## 실제 검증

- 사용자 확정 명칭은 1 경고, 2 대피, 3 위급이다. 합성 사용자 3명으로 H2 이동 여건별 차이, 긴급 큐 공식 대피 원문/위치 대상, 조력자 도착, 대체 경로 없는 차단, 공식 정정·해제, 자동 하향 방지와 확인 후 하향, 위치 삭제/복원 재평가를 확인했다. 실제 재난 발령이 아닌 합성 입력이다.
- 긴급 경로는 Qwen을 기다리지 않는다. 일반 서버 GPU 터널만 끊고 전체 합성 시연을 다시 실행해 동일 흐름이 통과했다. 기존 GPU 모델 서비스와 학습은 중단하지 않았다.
- 실제 GPU 임베딩 1024차원, 인터넷 검색 성공/5개 결과, 실제 Qwen 통합 완료. 입력 876/출력 257토큰, 모델 시간 10355.72ms다. 생성 요약은 미검토이고 개인 단계는 고정 규칙만 사용한다.
- 일반 서버 전체 서비스 정지/재시작 후 해당 시나리오 계정 3개·입력 30개·개인 정책 3개·전달 기록 17개·변경 36개·긴급 작업 3개가 보존됐다. 입력 본문 SHA256 일치, 정책 ID 보존 및 revision 비감소를 확인했다. migration bde1925b1429.
- 재시작 이후 전달은 simulated 12개/superseded 5개이며 pending 없음. 긴급·분석·전달 큐 잔여 0개다. 실제 푸시 발송/단말 수신을 뜻하지 않는다.
- 개발 컴퓨터에서 SSH 사설망을 통해 readiness 200, 무인증 사용자 조회 401, 실행 OpenAPI 0.2.0-mvp(사용자 21개 경로/28개 동작)를 확인했다. 사용자 간 다른 리소스 접근은 404다.
- 승인된 전용 SSH 키는 일반 서버 출발과 GPU 8001 API 포트만 허용한다. 다른 포트·원격 포워딩·임의 명령의 거부를 실제 검사했다. 일반 서버 설정/개인키는 600이며 값은 Git/로그에 없다.

## 검증과 산출물

- 실제 PostgreSQL 포함 서버 테스트 82 passed, 기존 Starlette/httpx 경고 1개. Ruff check/format, 실행 OpenAPI 구조, 기존 25 API/67스키마/48HTTP예제/4오류 거부, Alembic check, Compose config 통과. 워커 오류 표식 0개.
- docs/V2/delivery/mvp-server-runbook.md: 실제 접속·계정·시연·지속 실행·복구·비공개 설정·제외 기능.
- docs/V2/delivery/mvp-server-evidence.json: 정상/GPU 미연결 합성 시연, 모델 지표, 재시작 및 사설망 검사 근거.
- deploy/compose/mvp.yaml, deploy/systemd/bonghwajigi-general*.service, deploy/ssh/gpu-api-only.conf: 상시 배포 구성.
- tools/mvp_provision.py, tools/mvp_demo.py, tools/mvp_analysis_demo.py: 비공개 준비와 재실행 가능한 시연.

## 범위와 다음 연결

사용자가 Firebase와 HTTPS 도메인이 아직 없다고 답했으므로 모의 발신/SSH 사설망 개발 접속까지 완료했다. 실제 단말/FCM/공개 HTTPS/외부 로그인 제공자/실제 도로 경로는 미검증이다. 실제 예측 연결·실제 K8s 수집·3D·서버 음성·자동 119 신고는 제외했다. 실제 Firebase 자격 파일/기기와 도메인이 정해지면 실제 전달 및 단말 통합을 검증해야 한다. 현재 위치·상태는 5분마다 만료되므로 앱에서 최신 자료를 보내야 한다.

서버와 터널은 계속 실행한다. 진행 중인 다른 채팅의 학습 파일/전역 문서 등록 변경을 보존하며, 이번 구현과 Task 기록만 커밋한다.

## 15. 발표용 외부 API·모델·데이터·오픈소스와 라이선스 전수 정리

# 결과

사용자가 첨부한 발표 양식의 구분·명칭·용도·라이선스 형태로 `docs/V2/delivery/external-resources-and-licenses.md`를 작성했다. 서버·GPU 모델·학습 데이터·외부 API·뉴스/행동요령·기존 인프라·개발 도구를 실제 사용/확보/구성/조사로 구분했다. 사용자가 사전 보유·가져온 자료 없음을 확인하여 해당 없음으로 기록했다. 앱 저장소는 조회하지 않았다.

두 잠금 파일 139/71개 항목을 합친 외부 패키지·버전 174개를 모두 수록했다. 로컬/GPU 다섯 환경에서 154개 설치를 확인했고 20개 lock-only 분기를 구분했다. 직접 개발 패키지 2개 및 버전 범위만 선언된 Hatchling은 별도로 기록했다. 설치 METADATA와 동봉 LICENSE/NOTICE 경로·SHA, 공식 PyPI 버전별 metadata를 근거 JSON에 보존했다.

KMA FF의 승인 사용자 접근 제한과 미확정 제품별 KOGL 유형, ESA CCI 구버전 이용조건, Redis 7.4 RSALv2/SSPLv1, 안전한TV 제4유형, 뉴스 저작권, PostgreSQL pgvector 확장과 Python pgvector의 서로 다른 라이선스를 표시했다. Qwen 두 모델의 고정 revision 및 Apache2, NOAA/NASA/CC BY/전용 CopDEM 조건을 구분했다. API endpoint·인증·포맷·쿼터와 카탈로그만 조사한 경로도 설명했다.

검증: 외부 174개 전수 대조에서 누락/추가0, Markdown 행 누락0, 표4열 오류0, 로컬 링크 오류0, 인증정보 패턴0. `git diff --check`, `loom validate --strict` 통과. 문서/근거 파일 변경만 수행했으며 앱·서비스·학습 실행 설정은 변경하지 않았다. 기존 v4 수집·연구·utility 서비스는 읽기 점검에서 모두 active였으며 모델 개선 Task는 계속 RUNNING으로 유지한다.

범위 한계는 문서에 명시했다: 앱 자원 제외, OS/컨테이너 내부 전체 바이너리 SBOM 미작성, 미표기·판본 불명 라이선스를 허가로 간주하지 않음. 이는 자료 정리 완료이며 모든 자원의 재배포 권리를 확보했다는 뜻이 아니다.
