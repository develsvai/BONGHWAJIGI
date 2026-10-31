# Previous Results

20 older recorded result(s) were omitted. Promote durable context to Job Notes or explicit Context References.

## 24. 기술 스택 페이지를 기존 발표 스타일의 편집용 PPT로 제작

# 결과

첨부 `ppt_8.webp`의 기술 스택 페이지를 기존 아키텍처 PPT와 같은 서식의 편집용 한 장으로 제작했다.

- `docs/V2/delivery/architecture-slides/output/bonghwajigi-tech-stack.pptx`
- `docs/V2/delivery/architecture-slides/output/tech-stack.png`
- `docs/V2/delivery/tech-stack-slide.md`

기존 PPT의 제목·부제 개체와 마스터를 가져오고 같은 크기·글꼴·팔레트·여백으로 본문을 구성했다. 원본 수치 3명·82건·14건을 유지하고 제공 자료 기준임을 표시했다.

## 검증

- `node build-tech-stack.mjs /private/tmp/bonghwa-tech-stack` — 한 장의 편집용 PPTX와 3200×1800 PNG 생성.
- `node finalize-tech-stack.mjs /private/tmp/bonghwa-tech-stack` — 패키지, 16:9 크기, 한 장, 참조 글꼴, 제목 맞춤, 재가져오기 통과. 검사 결과 finding 0 / warning 0.
- 최종 PPTX XML 읽기 검사 — 편집 가능 도형 40개, 본문 이미지 0개. 기술 구성 5개와 3명·82건·14건 포함.
- 최종 파일 SHA-256 `ecef06c509e7486c1dc99c1326badbffd28cb76f1a36089959ffb82d4428b19b`와 검증 산출물 일치. 문서 상대 링크 통과.
- PNG를 원본 크기로 열어 한글·여백·제목·색상·내용을 시각 검토했다. PowerPoint 앱 자체 실행 검증은 하지 않았다.

## 한계와 다음 행동

Apple SD Gothic Neo가 없는 환경에서는 글꼴 대체가 가능하다. 그대로 삽입할 때는 PNG를 사용할 수 있다. 첨부 원본의 검사 수치이며 이번 작업의 새 기능 테스트 결과는 아니다. 기존 발표 자료와 다른 작업의 변경은 보존했다.

## 25. 네이버 실지도 검증 앱 버전을 서브모듈에 고정하고 외부 자원 문서 갱신

# 완료 결과

지도 연결 앱에 대한 읽기 검토를 수행했다. 지역 관련성 문구의 최신 입력 확인과 simulation 모드의 좌표 표기 문제를 전달했고 앱 담당자가 보완했다. SDK2.9.1 초기화 콜백은 타일/인증 성공이 아니라는 점을 확인했다.

## 검증

최종 앱 QA 커밋 ced24463bb79a6ef5d3b532f6d2a48215ca84a56을 origin/develop에서 fetch하고 detached checkout했다. manifest·실제 APK 해시·앱/서버 API 계약은 대조 통과했고 메인 원격 push 후 새 재귀 checkout까지 검증했다. 이번 준비 과정에서는 앱 코드·서버·GPU·학습을 수정하지 않았다.

## 지도 자원 근거

- wrapper 2.9.1 설치 LICENSE에서 MIT 확인. Android SDK 기본값·Gradle 실제 캐시 모두3.23.2.
- 공식 Maven AAR의 SDK LICENSE는 NAVER Corp. All rights reserved이며 동봉 NOTICE를 별도 유지한다. Apache-2.0인 데모 저장소와 구분했다.
- 공식 Maps 서비스약관 PDF와 Android 시작·Application 등록 가이드를 조회했다. Key ID의 실제 값 또는 Client Secret은 읽거나 저장하지 않았다.
- 외부 자원 문서의 기존 앱 제외 문구·미확인 행과 새 지도 절만 갱신했다. 공유 파일에 누적된 학습 자원 변경은 유지하며 commit에서는 HEAD에 지도 변환만 적용한 blob으로 분리한다.

## 단말 지도 확인 중 서버 읽기 대조

앱 담당자의 요청으로2026-10-31 18:23:43UTC에 기존 단말 합성 계정을 READ ONLY 트랜잭션으로 대조했다. 위치 revision2의 관측 시각은18:22:50.701780UTC, 유효 종료18:27:50.701780UTC였고 기존 시연 좌표와 일치했다. mobile-fire revision4와 사각형 범위(서129.0·동129.8·남36.0·북37.0)도 유효했다. 정책 projection revision9, requested/applied14/14, error_code null, relevance inside. 계정ID·토큰·개인 위치를 문서에 남기지 않았고 서버 데이터를 수정하지 않았다.

앱 담당자는 시연 위치 저장 뒤 실제 네이버 타일·위치 마커·표시 좌표·카메라 이동을 확인했다. 최초 마커 부재는 위치 공유 전 전국 보기였다. 사용자는 공식 경보 상세의 붉은 영역과 위치 마커가 함께 표시됨을 최종 확인했다. 최종 앱 QA 커밋은 ced24463bb79a6ef5d3b532f6d2a48215ca84a56이다.

## 최종 앱 출처 대조

- 앱 gitlink: ced24463bb79a6ef5d3b532f6d2a48215ca84a56, origin/develop에 존재하며 submodule clean.
- APK0.2.1/code3 실행소스66c4d734287549d6403c429ca42e6fdb44d38d2b. 실행소스 이후 src/app/config/scripts/package 차이없음. build source_dirty는 안내 문서4개 편집으로 설명된다.
- 실제 APK 파일SHA256과 manifest가5d4b2cb00adead0d2f6e2e1f51c76c32819c6b7b5095189549dd8fc0079aee25로 일치.
- 앱/서버 OpenAPI 내용동일, SHA256323536c7322fcfea70d0853633731de09b19a37479370769a41e7a9e42b72062. lockfile SHA2565197246c8a946b42d613b36f0bc887ea2cb844d767378fb9c3baf5433934e419.
- 앱 담당자 검증: TypeScript·45테스트·웹 export·native release 빌드·실제 단말 업데이트 설치. 타일/마커 캡처와 사용자 직접 영역 확인의 근거를 구분해 기록했다.

## 원격 재현과 경계

main ad0d34dd67bf7bf21829fc1bffd291f06c35b4d2 정상 push 후 /private/tmp/bonghwa-map-recursive-20261101-1829에 실제 GitHub를 재귀 clone했다. main/app 모두 clean, gitlink ced24463bb79a6ef5d3b532f6d2a48215ca84a56 자동 초기화, sourcechecker·OpenAPI·lockfile 해시 대조 통과. 문서 로컬 링크와 git diff check, Loom strict(6 Jobs/56 Tasks) 통과.

다른 채팅의 학습·발표·라이선스 후속 자원은 작업 트리에 보존하고 이번 커밋에 포함하지 않았다. main 작업 트리 전체가 clean이라고 주장하지 않는다. 앱 코드·지도 키·서버 API·GPU·학습을 수정하지 않았다. 실제GPS·경로계산·FCM 실발신은 이번 지도 QA 범위 밖이다. 후속 UI/대화 요청은 별도 Task에서 진행한다.
