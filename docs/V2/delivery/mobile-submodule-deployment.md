# 앱 서브모듈과 배포 소스 확인

2026-11-01 KST. 앱 저장소를 `apps/mobile`의 Git 서브모듈로 연결한다. 정본 원격은 사용자가 지정한 `https://github.com/duswls98952/BONGHWAJIGI_APP.git`이다. 일반 서버와 앱은 각각의 커밋을 갖고 메인 저장소가 검증된 앱 커밋을 고정한다.

현재 APK는 **0.3.1 / versionCode 5**이다. 실행 소스는 `c0b87ea2bab3ba769ebe3bfbbc91e140d0c12f0e`, APK SHA256은 `c30826365bc023074bdfdc86372e47e8ae780a431ed3ac2caadc5856d79312fe`다. 메인 gitlink는 단말 음성·경로 검증 문서가 포함된 `f54cae1c753054de0a8f2eb76166807019db8db4`에 고정한다. 실행 소스 이후에는 문서·검증 기록만 추가됐다. [최신 앱 검증 정본](../../../apps/mobile/docs/12-demo-polish-voice-route.md)과 [APK 빌드 manifest](../../../apps/mobile/docs/validation/android-polish-build.json)를 함께 대조한다.

이전0.2.0의3단계·TTS는 [초기 APK 문서](../../../apps/mobile/docs/10-android-delivery.md),0.2.1의 네이버 지도는 [지도 연결 문서](../../../apps/mobile/docs/11-naver-map-integration.md)에 역사로 보존한다. 아래의 과거 재귀 clone과 단말 확인은 각각 당시 버전의 근거다.

## 초기화와 소스 확인

새 컴퓨터에서는 다음 명령으로 서브모듈까지 받는다.

```sh
git clone --recurse-submodules --branch develop https://github.com/develsvai/BONGHWAJIGI.git
cd BONGHWAJIGI
python3 tools/check_mobile_source.py
```

기존 checkout에서는 메인 커밋을 정상 갱신한 다음 실행한다. 작업 중인 소스가 있다면 먼저 해당 작업을 보존한다.

```sh
git submodule sync --recursive
git submodule update --init --recursive
git submodule status apps/mobile
python3 tools/check_mobile_source.py
```

검사 도구는 메인 HEAD의 `160000` gitlink, 앱 checkout SHA, 앱 미커밋 변경 유무, 서버·앱 OpenAPI의 일치를 확인한다. 정상이라면 메인/앱 SHA, API/lockfile 해시와 Node·Expo·React Native 버전을 출력한다. 서브모듈에서 임의 `git pull`이나 `update --remote`로 최신 브랜치를 받으면 메인에서 검증한 SHA와 달라질 수 있다.

## 앱 빌드와 결과물

앱의 Node 요구 범위는 `package.json`을 따른다. 현재 Node24와 lockfile을 사용한다.

```sh
cd apps/mobile
npm ci
npm run check
```

Android SDK·JDK·서명키·공개 API 주소를 준비한 공통 APK 빌드 절차는 [초기 배포 문서](../../../apps/mobile/docs/10-android-delivery.md), 최신 기능·단말 검증은 [0.3.1 문서](../../../apps/mobile/docs/12-demo-polish-voice-route.md)를 따른다. 서버 서비스 토큰·JWT 서명키·GPU 토큰·Firebase 비밀키를 앱 환경에 넣지 않는다. 서명 자격은 Git 밖의 비공개 파일로 관리한다. APK 바이너리와 서명키를 gitlink에 추가하지 않는다.

앱 결과물에는 실제 빌드에 사용한 앱 소스 SHA, API 주소, 앱 버전, 서명 인증서 지문, APK SHA256을 함께 남긴다. `check_mobile_source.py` 출력은 소스 일치 근거이며 APK 설치나 단말 기능 검증을 대신하지 않는다.

앱 API는 [일반 서버 배포 문서](mobile-server-deployment.md)의 Tailnet HTTPS를 사용한다. 현재 실행 서버 소스는 `414482274f9252056ac350c69d4687e7a1429d8b`이며 [텍스트 대화·합성 경로 API](mobile-dialogue-and-route.md)와 기존 [단말 시계 보정](mobile-location-clock-skew.md)을 포함한다. 승인된 단말의 Tailscale 연결이 필요하다. 네이버 Android 지도는0.2.1에서 연결했다. 같은 앱을 다시 빌드할 때는 Git 밖의 지도 Key ID 주입이 필요하다. Firebase 실발신과 실제 예측 연결은 계속 별도 준비 조건이다.

## 실기기 연결 근거 — 초기0.2.0

사용자는 설치된 APK에서 1·2·3단계 갱신을 확인했다. 음성 재확인에서는 휴대폰이 무음이었다고 설명하고 무음 해제 뒤 정상 청취를 최종 확인했다. 같은 합성 계정의 서버 DB를 2026-10-31 17:44:16 UTC에 읽기 대조하여 다음 정책 이력을 확인했다. 계정 식별자·토큰·개인 위치는 이 문서에 포함하지 않는다.

| 서버 정책 revision | 단계 | 평가 시각 UTC |
| --- | --- | --- |
| 2 | 경고 (`prepare`) | 2026-10-31 17:43:08.895844 |
| 3 | 대피 (`act`) | 2026-10-31 17:43:26.102004 |
| 4 | 위급 (`request_assistance`) | 2026-10-31 17:43:34.242662 |

위치 입력 revision1, 현재 상태 revision2가 저장됐다. 음성 출력은 사용자의 단말 청취 확인에 근거하며 서버는 안내 텍스트를 제공한다. 위 이력은 합성 시나리오의 실서버 연결 검증이다.

## 네이버 지도 단말 검증 — 0.2.1

기존 Samsung SM-G996N에 같은 서명의0.2.1을 업데이트 설치했다. 기존 앱 계정·프로필을 보존한 채 실제 네이버 전국 타일을 확인했고, 시연 위치 저장 후 위치 마커·공유 좌표·정확도10m 표시와 카메라 이동을 화면 캡처로 확인했다. 사용자가 공식 경보 상세에서 **붉은 사건 영역과 위치 마커가 함께 보임**을 직접 확인했다. 상세 영역은 사용자 확인 근거이며 그 화면의 캡처를 확보한 것으로 기록하지 않는다.

서버는2026-10-31 18:23:43UTC에 READ ONLY로 대조했다. 위치 revision2가18:22:50.701780UTC에 수신되어18:27:50.701780UTC까지 유효했고 시연 좌표와 일치했다. 합성 사건 mobile-fire revision4의 영역도 유효했으며 정책 계산 오류가 없고 위치 관련성은 inside였다. 홈 지도에는 위치 마커를, 공식 경보·개인 대응 상세에는 해당 사건 범위를 표시한다. 최초 전국 지도에 마커가 없었던 것은 위치 공유 전 상태였다.

사건 사각형은 관련 지역 범위이고 실제 화선·안전 구역·대피 경로가 아니다. 이번 확인은 합성 시연 좌표를 사용했으며 실제 GPS 이동·백그라운드 추적을 검증한 것으로 표시하지 않는다. 서버 API·GPU·학습·5분 위치 유효성 계약은 이 지도 연결 작업에서 변경하지 않았다. 지도 래퍼·SDK·Maps 서비스 조건은 [외부 자원 문서](external-resources-and-licenses.md)의 Android 지도 절을 따른다.

## 음성 대화·상태 확인·시연 경로 단말 검증 — 0.3.1

Samsung SM-G996N에 같은 서명의0.3.1을 업데이트 설치했다. 앱 담당자는 native 로고·홈 카드 대비·연속 모서리와 실제 네이버 지도 경로를 확인했고 사용자는 경로 표시를 직접 확인했다. 초기0.3.0 음성 입력은 이미 허용된 마이크 권한을 매번 다시 요청하면서 인식 시작 전에 취소되는 문제가 있었다.0.3.1은 허용 상태를 먼저 읽어 재요청을 피하고 최초 권한 허용 후 녹음 시작을 분리했다.

최종0.3.1에서 실제 한국어 발화→인식 텍스트→서버 답변→계단 이용 어려움 제안과 상태 반영 화면을 캡처했다. native 로그에서 기존 마이크 권한 허용, 온디바이스 인식, 시작·발화 종료 이벤트를 확인했다. 사용자가 **음성 인식과 상태 반영 모두 정상**이라고 최종 확인했다. 원음 파일을 보관한 검증이 아니다.

[서버 READ ONLY 대조](mobile-voice-device-evidence.json)는 동일 합성 단말의 최근 revision·시각만 기록한다.19:18:31UTC의 Qwen 계단 제안은 context4를 기준으로 생성됐고 확인 후 정책14 경고→15 대피(19:18:49)로 바뀌었다. 이어19:19:20의 상태 제안은 context5를 기준으로 생성됐고 현재 context6(19:19:43), 정책16 대피(19:19:45), requested/applied24/24, 계산 오류없음을 확인했다. 계정ID·토큰·대화 원문은 이 근거에 포함하지 않는다.

앱 타입·62개 테스트·문서 링크·웹 번들 및 release APK 검증을 통과했고 실제 APK 파일과 빌드 manifest의 해시가 일치한다. 서버는121개 PostgreSQL 회귀 검사와 실제 Qwen·확인 전 비변경·확인 후3단계 갱신을 별도로 통과했다. 시연은 합성 위치와 서버 합성 경로를 사용하며 실제 GPS·공식 안전 경로·실제 예측·FCM 실발신 검증으로 확대하지 않는다. 신규 STT·글꼴의 조건은 [외부 자원 문서](external-resources-and-licenses.md)의 Android 음성 입력·로고 서체 절을 따른다.

## 새 checkout 재현 검증 — 초기0.2.0

메인 커밋 `eaeef8756cd066518fb50bc634ff2a701c78a9f5`를 `origin/develop`에 정상 push한 뒤 별도 디렉터리에 실제 GitHub 원격을 `git clone --recurse-submodules --single-branch --branch develop`으로 받았다. `apps/mobile`이 `ed91b1ce78554e339e9a95bbc49a4028cc957178`로 자동 초기화됐고 메인과 앱 작업 트리가 모두 clean이었다.

`python3 tools/check_mobile_source.py`가 원본 checkout과 새 clone에서 모두 통과했다. API 계약 SHA256은 `323536c7322fcfea70d0853633731de09b19a37479370769a41e7a9e42b72062`, 앱 package-lock SHA256은 `08b60136671bfe60a1a9c04480da64e1d9b27c49a9107867219f4d390b2dbf65`다. 이후 메인 커밋은 이 검증 결과와 Loom 완료 기록을 추가한다.

## 새 checkout 재현 검증 — 0.2.1

메인 `ad0d34dd67bf7bf21829fc1bffd291f06c35b4d2`를 정상 push한 뒤 실제 GitHub 원격을 새 디렉터리에 `--recurse-submodules --single-branch --branch develop`으로 clone했다. 앱은 `ced24463bb79a6ef5d3b532f6d2a48215ca84a56`에 자동 고정됐고 새 메인·앱 작업 트리 모두 clean이었다. 원본과 새 clone의 `python3 tools/check_mobile_source.py`가 모두 통과했다.

API 계약 SHA256은 기존과 같은 `323536c7322fcfea70d0853633731de09b19a37479370769a41e7a9e42b72062`, 지도 앱 package-lock SHA256은 `5197246c8a946b42d613b36f0bc887ea2cb844d767378fb9c3baf5433934e419`다. 앱 QA 커밋과 실행 소스의 `src`, `app`, 앱 설정·빌드 스크립트·package/lock에는 차이가 없으며 실제 APK 파일 SHA256도 지도 빌드 manifest와 일치했다. 이후 메인 커밋은 이 재현 결과와 Loom 완료 기록을 추가한다.

## 다음 앱 버전 고정

앱 변경은 앱 저장소에서 구현·검증·커밋·원격 push를 끝낸 뒤 새 SHA를 메인 저장소에 반영한다. 서브모듈의 로컬 미커밋 내용을 메인 커밋이 저장해 주지 않는다.

```sh
git -C apps/mobile fetch origin develop
git -C apps/mobile checkout --detach VERIFIED_APP_COMMIT
git add apps/mobile
git diff --cached --submodule=log
```

`VERIFIED_APP_COMMIT`은 검증하고 원격에 게시한 전체 SHA로 바꾼다. 메인 커밋 이후 소스 검사와 새로운 checkout의 재귀 초기화를 확인하고 메인 `develop`을 일반 push한다. 서버 Python 이미지 빌드에서는 `.dockerignore`가 `apps/mobile`을 제외하므로 앱 의존성·빌드 산출물을 서버 이미지에 넣지 않는다.
