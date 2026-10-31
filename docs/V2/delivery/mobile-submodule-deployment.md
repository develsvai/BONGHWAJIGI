# 앱 서브모듈과 배포 소스 확인

2026-11-01 KST. 앱 저장소를 `apps/mobile`의 Git 서브모듈로 연결한다. 정본 원격은 사용자가 지정한 `https://github.com/duswls98952/BONGHWAJIGI_APP.git`이다. 일반 서버와 앱은 각각의 커밋을 갖고 메인 저장소가 검증된 앱 커밋을 고정한다.

APK 실행 소스는 `0716c49d501fe5e066537b673698e07fcbd48ff6`이며 APK SHA256은 `fe6892591e5224f5b982d53ce0536425f4a44290182477b865b922a63b2ad5e9`이다. 메인 gitlink는 단말 검증 문서가 포함된 `ed91b1ce78554e339e9a95bbc49a4028cc957178`에 고정한다. 두 커밋 사이에는 문서와 검증 기록만 추가됐다. [앱 APK 배포·단말 검증 문서](../../../apps/mobile/docs/10-android-delivery.md)와 [빌드 manifest](../../../apps/mobile/docs/validation/android-build.json)에서 산출물 근거를 확인한다.

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

Android SDK·JDK·서명키·공개 API 주소를 준비한 APK 빌드와 단말 검증은 [앱 배포 문서](../../../apps/mobile/docs/10-android-delivery.md)를 따른다. 서버 서비스 토큰·JWT 서명키·GPU 토큰·Firebase 비밀키를 앱 환경에 넣지 않는다. 서명 자격은 Git 밖의 비공개 파일로 관리한다. APK 바이너리와 서명키를 gitlink에 추가하지 않는다.

앱 결과물에는 실제 빌드에 사용한 앱 소스 SHA, API 주소, 앱 버전, 서명 인증서 지문, APK SHA256을 함께 남긴다. `check_mobile_source.py` 출력은 소스 일치 근거이며 APK 설치나 단말 기능 검증을 대신하지 않는다.

앱 API는 [일반 서버 배포 문서](mobile-server-deployment.md)의 Tailnet HTTPS를 사용한다. 현재 실행 서버 소스는 `959ab56`이며 [단말 시계 보정 배포](mobile-location-clock-skew.md)를 포함한다. 승인된 단말의 Tailscale 연결이 필요하다. Firebase·네이버 지도 자격과 실제 예측 연결은 별도 준비 조건이다.

## 실기기 연결 근거

사용자는 설치된 APK에서 1·2·3단계 갱신을 확인했다. 음성 재확인에서는 휴대폰이 무음이었다고 설명하고 무음 해제 뒤 정상 청취를 최종 확인했다. 같은 합성 계정의 서버 DB를 2026-10-31 17:44:16 UTC에 읽기 대조하여 다음 정책 이력을 확인했다. 계정 식별자·토큰·개인 위치는 이 문서에 포함하지 않는다.

| 서버 정책 revision | 단계 | 평가 시각 UTC |
| --- | --- | --- |
| 2 | 경고 (`prepare`) | 2026-10-31 17:43:08.895844 |
| 3 | 대피 (`act`) | 2026-10-31 17:43:26.102004 |
| 4 | 위급 (`request_assistance`) | 2026-10-31 17:43:34.242662 |

위치 입력 revision1, 현재 상태 revision2가 저장됐다. 음성 출력은 사용자의 단말 청취 확인에 근거하며 서버는 안내 텍스트를 제공한다. 위 이력은 합성 시나리오의 실서버 연결 검증이다.

## 새 checkout 재현 검증

메인 커밋 `eaeef8756cd066518fb50bc634ff2a701c78a9f5`를 `origin/develop`에 정상 push한 뒤 별도 디렉터리에 실제 GitHub 원격을 `git clone --recurse-submodules --single-branch --branch develop`으로 받았다. `apps/mobile`이 `ed91b1ce78554e339e9a95bbc49a4028cc957178`로 자동 초기화됐고 메인과 앱 작업 트리가 모두 clean이었다.

`python3 tools/check_mobile_source.py`가 원본 checkout과 새 clone에서 모두 통과했다. API 계약 SHA256은 `323536c7322fcfea70d0853633731de09b19a37479370769a41e7a9e42b72062`, 앱 package-lock SHA256은 `08b60136671bfe60a1a9c04480da64e1d9b27c49a9107867219f4d390b2dbf65`다. 이후 메인 커밋은 이 검증 결과와 Loom 완료 기록을 추가한다.

## 다음 앱 버전 고정

앱 변경은 앱 저장소에서 구현·검증·커밋·원격 push를 끝낸 뒤 새 SHA를 메인 저장소에 반영한다. 서브모듈의 로컬 미커밋 내용을 메인 커밋이 저장해 주지 않는다.

```sh
git -C apps/mobile fetch origin develop
git -C apps/mobile checkout --detach VERIFIED_APP_COMMIT
git add apps/mobile
git diff --cached --submodule=log
```

`VERIFIED_APP_COMMIT`은 검증하고 원격에 게시한 전체 SHA로 바꾼다. 메인 커밋 이후 소스 검사와 새로운 checkout의 재귀 초기화를 확인하고 메인 `develop`을 일반 push한다. 서버 Python 이미지 빌드에서는 `.dockerignore`가 `apps/mobile`을 제외하므로 앱 의존성·빌드 산출물을 서버 이미지에 넣지 않는다.
