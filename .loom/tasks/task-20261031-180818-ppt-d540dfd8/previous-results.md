# Previous Results

18 older recorded result(s) were omitted. Promote durable context to Job Notes or explicit Context References.

## 22. 검증된 앱 커밋을 서브모듈로 고정하고 배포 소스 확인 절차 동기화

# 결과

앱을 canonical 원격 https://github.com/duswls98952/BONGHWAJIGI_APP.git 의 apps/mobile 서브모듈로 연결했다. 단말 검증 문서가 포함된 ed91b1ce78554e339e9a95bbc49a4028cc957178을 고정한다. APK 실행 소스는 0716c49이며 두 커밋 사이 실행 코드 차이는 없다.

초기화·빌드 출처·API 검사·다음 버전 갱신 절차는 docs/V2/delivery/mobile-submodule-deployment.md, 재현 검사는 tools/check_mobile_source.py에 있다. 서버 Docker context에서 apps/mobile을 제외했다. README에 진입 링크를 추가했다.

## 검증

메인 eaeef8756cd066518fb50bc634ff2a701c78a9f5를 정상 push한 뒤 실제 GitHub 원격을 새 디렉터리에 git clone --recurse-submodules --single-branch --branch develop으로 받았다. 서브모듈 ed91b1c 자동 초기화, 메인/앱 clean, python3 tools/check_mobile_source.py 통과. 원본 checkout 검사도 동일하게 통과했다. OpenAPI SHA323536c7… 및 package-lock SHA08b60136… 일치. 빌드 manifest의 소스와 APK 해시 fe689259… 대조, 단말 정책 revision2/3/4와 사용자 음성 청취 최종 확인 기록을 포함했다. Ruff, 문서 링크, git diff --check, Loom strict 통과.

## 남은 조건

실제 예측, Firebase 원격 푸시, 네이버 지도는 앞선 범위대로 별도 준비 사항이다. 이 Task는 정상 push와 소스 재현을 완료했으며 다른 채팅의 training/presentation 미커밋 변경을 보존했다. 앱의 후속 Loom 완료 기록은 앱 원격에 추가돼도 검증된 gitlink ed91b1c는 유지한다.

## 23. 실기기 시계 오차로 거절되는 위치 입력을 보정하고 일반 서버 검증

# 구현 결과

위치와 현재 상태 입력의30초 이내 시계 오차를 수신시각으로 보정했다. 정책 만료는 보정시각+5분이며 이전 입력과 삭제 후 재전송 검증을 유지한다. 문서: docs/V2/delivery/mobile-location-clock-skew.md.

## 검증

.venv/bin/ruff check 통과. 실제 로컬 PostgreSQL 포함 pytest 전체104개 통과(기존Starlette경고1). 위치/상태10개 시간경계와 보정위치 재전송·삭제회귀1개를 추가했다. 일반 서버959ab56 배포 후 실제 Tailnet HTTPS에서도 +0.6초 위치/context가 성공하여 경고→대피→위급을 확인했고, +40초 위치/context는422를 유지했다. 공식 원문·cursor·refresh·logout 통과. 기존 DB/비공개 설정백업600, GPU/학습 미접근. 사용자 단말 UI 재시도는 앱 검증Task에서 이어간다.
