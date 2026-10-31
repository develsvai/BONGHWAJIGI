# 구현·검증 결과

최종 앱 f54cae1c753054de0a8f2eb76166807019db8db4를 원격 develop에서 받아 apps/mobile에 고정했다. 실행 소스c0b87ea2bab3ba769ebe3bfbbc91e140d0c12f0e와 실행 파일 차이없음, submodule clean, 앱/서버 OpenAPI 전체일치, APK0.3.1/code5 실제 파일SHA256 c30826365bc023074bdfdc86372e47e8ae780a431ed3ac2caadc5856d79312fe·66,088,154bytes 일치를 확인했다. 앱 담당자는 타입·62테스트·문서링크·웹번들·native빌드/설치·최종음성인식/상태반영과지도경로를 검증했다.

사용자 정상 확인과 native 화면/로그, 동일 합성 계정 READ ONLY 서버의 context4→5→6 및 정책14경고→15/16대피 이력을 대조했다. sourceID·계정ID·토큰·대화원문 없는 JSON을 mobile-voice-device-evidence.json에 기록했다. 서버 실행소스4144822와121테스트/실모델연결 검증은 별도 완료 Task를 참조한다.

자원 문서에 새 STT·expo-font MIT, Android 기본인식 서비스 조건, 대한민국정부상징체 공공누리4유형과 바이너리/고지 확인 범위를 기록했다. APK의 font는 저장소 원본과 해시동일하다. JUnit은 테스트 구성으로 구분했다. 자체 API 표는 현재58개 동작과 대조해 누락6개 행과 합성경로 제공 상태를 바로잡았다. 문서로컬링크·diff·Loomstrict 통과 후 메인커밋/원격재귀clone을 이어 검증한다.

메인 pin 커밋 `08a381de06c6371337a7dc1e66aa166fe28e0383`을 정상 push한 뒤 실제 GitHub 원격을 별도 디렉터리로 재귀 clone했다. 원본·새 clone 모두 `tools/check_mobile_source.py` 통과, 앱 `f54cae1c753054de0a8f2eb76166807019db8db4` 자동 초기화, 새 main/app clean을 확인했다. API 계약 SHA256 `e9075d620d9d916d512328b380e35c9073f9e681fd8236a86cc083787a735671`, package-lock SHA256 `8d12887f658e24f21ff7d27b85c62e1fd5ec94270923a09b638477b9cf68285d`가 일치한다. 타 채팅의 학습·발표·공유 문서 변경은 부분 staging으로 제외하고 보존했다.
