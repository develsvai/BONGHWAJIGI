# Previous Results

25 older recorded result(s) were omitted. Promote durable context to Job Notes or explicit Context References.

## 29. 발표 v1 디자인 통일과 외부 자원·기대 효과 페이지 수정

# 결과

사용자가 전달한 11장 v1 PPT의 디자인을 통일하고, 후속 지시에 따라 10장 외부 자원 표를 17개 상세 행으로 확대하고 11장을 사용자 원문의 기대 효과·확장 방향으로 다시 작성했다.

산출물: `docs/V2/delivery/presentation-v1/output/봉화지기_발표자료_디자인통일_v2.pptx`와 `output/preview/`의 전 11장 PNG. 문서: `docs/V2/delivery/presentation-v1-design.md`.

11장·원본 크기, 1~9장 모든 텍스트, 9개 원본 이미지 바이트, 모든 개별 도형 이름과 개수를 대조했다. 전체 렌더링을 확인하고 패키지·폰트·재가져오기 검증을 통과했다. 원본 7장 아이콘 구성의 connector 경고는 시각적으로 확인 후 유지했다. 3장 그룹 일부는 평탄화되며 개별 요소는 보존한다. 네이티브 PowerPoint 실행 검증은 하지 않았다.

최종 파일 SHA256: `460fe57ec29e709a575c7bbcf0c8506b190d7bc7ff21990e04a014c157ef7ef0`.

## Validation

- `node docs/V2/delivery/presentation-v1/source/finalize-v1.mjs /private/tmp/bonghwa-v1-design/edited /private/tmp/bonghwa-v1-design/edited/output/final-v3.pptx`: exit 0. Package integrity pass, 11 slides, font policy pass, native table on slide 10, Artifact Tool import pass.
- `python3 /private/tmp/validate-v1-preservation.py`: exit 0. Slides 1–9 text runs match, all individual shape names match, all image bytes match, dimensions match.
- Full-size render review: 11/11 slides. Table overflow warning resolved. Existing slide 7 connector warning visually checked.
- `loom validate --strict`: OK, 6 jobs / 60 tasks. `git diff --check`: exit 0.
- Detailed private receipts: `/private/tmp/bonghwa-v1-design/edited/final-v3.pptx.validation.json`, `/private/tmp/bonghwa-v1-design/preservation.json`.

## 30. 멘토링 피드백과 실제 구현을 반영해 상세 README 작성

# README 구성 완료

루트 `README.md`를 444행의 상세 실행 안내로 재구성했다. 사용자 제공 1차 멘토링 전사 전체 227행과 발표자료 v3의 전체 11장 텍스트를 확인하고 실제 코드·최신 배포/촬영 기록과 대조했다. 멘토링의 출처·수집 지연, 멱등성·재시도·누락 방지, 실패 경계, 비밀 설정, 기술과 실행 명령 피드백을 반영했다.

주요 내용:

- 서비스 목적·현재 구현 표, 일반/GPU/DB/Redis/K8s 역할, 공식 경보와 일반 분석의 두 경로, 세 모델의 입력/출력·역할.
- 사용자 제공 아키텍처 PNG 포함. 원본 SHA-256과 동일한 저장소 기존 파일을 재사용하여 중복 파일을 만들지 않았다. 그림의 3위험 표기는 확정 API 명칭3위급으로 본문에서 바로잡았다.
- 앱의 현재 공식/합성/검색 자료와 별도 학습·확산 연구 자료를 구분한 출처 표. 현재 K8s 자동 수집 미실행, 공식 CBS 전문 미확보, 과거 자료/사후 분석/합성 위치의 해석을 명시했다.
- 이벤트ID+본문 해시, DB 고유 제약, outbox 원자 저장/재전달, 문서·정책 revision, 검색 URL, 앱 Idempotency-Key, 알림 최신성/lease의 중복·실패 처리. exactly-once나 운영 HA를 주장하지 않는다.
- Tailnet 전용 HTTPS와 사용자 JWT를 구분하고 SSH/USB 대안을 설명했다. 로컬 API 틀, Linux 전체 Compose, 기존 일반 서버 시나리오, GPU 직접 호출, 검증·장애 진단 명령을 제공했다.
- 실제 예측 미연결, FCM 모의 전송/단말 로컬 알림, 합성 경로, 사용자 확인 전 상태 미반영을 명시했다. 초기 SSH전용 문서와 현재 TailnetHTTPS 후속 기록도 구분했다.

검증: `.venv/bin/python /private/tmp/bonghwa-validate-readme.py` 통과. 문서의 16개 shell블록 구문, 로컬 링크/목차, 입력 검사와 4개 CLI 도움말, 새 비공개 설정의 생성/권한600/키 분리/덮어쓰기 거부, Compose config를 확인했다. 기본 API/GPU의 live200/ready503을 실제 모델·DB 없이 확인했다. 첨부 PNG SHA일치·인증정보 패턴0·git diff 공백·Loom strict 통과. 검증 JSON은 이 Task의 `verification.json`에 기록했다.

실제 Tailnet HTTPS 읽기 검사: 정상 TLS 검증으로 readiness200, DB·브로커 연결, prediction excluded 및 GPU optional 상태를 확인했다. 무인증 app-config401도 확인했다. 이 검증으로 데이터 주입·서버 배포·학습/모델 재시작을 하지 않았다.

제한과 다음 행동: 전체 Compose 새 배포와 시나리오 명령은 코드·CLI·설정 계약을 검증했으며 이번 README 작업에서 운영 데이터로 재실행하지 않았다. 문서 기준 이후 서비스나 데이터 경로가 바뀌면 현재 실행 범위를 갱신해야 한다. 앱·진행 중 학습·다른 채팅의 파일 삭제를 보존하고 README 및 이번 Task 기록만 커밋한다.
