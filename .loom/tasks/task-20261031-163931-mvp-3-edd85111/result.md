# 발표용 아키텍처 3장 완료

기존 세로 다이어그램과 현재 코드·완료된 배포 검증 기록을 대조해 3장을 만들었다. 전체 4단계 흐름, 세 모델의 필요성과 입력·출력, 공식 원문 우선 전달과 개인 안내 갱신을 각각 한 장에 정리했다.

산출물은 docs/V2/delivery/architecture-slides/output의 3200×1800 PNG 3장, 개별 도형·텍스트를 편집할 수 있는 PPTX, SVG 3장과 ZIP이다. docs/V2/delivery/presentation-architecture.md에 비교표·쉬운 용어·근거를 남겼다.

현재 범위는 K8s 실제 수집 보류, 시나리오 입력, 두 Qwen 실제 연결, XGBoost 실제 예측 미연결, 고정 규칙의 3단계, Firebase 모의 전송, 진행 중 앱 통합이다. 학습 코드·서버 실행 코드·앱 파일·원격 상태를 변경하지 않았다.

## 검증

- source/build.mjs로 편집 가능한 3장과 3200×1800 이미지를 생성했다.
- source/finalize.mjs의 패키지 무결성, 16:9 크기, 3장, 글꼴, 재가져오기 검사 통과. finding 0, warning 0.
- 최종 PPTX를 다시 가져와 3장을 렌더링하고 각 장을 직접 확인했다. 한국어 글꼴, 여백, 아이콘, 연결선, 단계 명칭을 확인했다.
- Python/Pillow 검증: PNG 3장 해상도, 137개 텍스트 폭, 로컬 문서 링크, PPTX 3장, ZIP 무결성 통과.
- loom validate --strict 및 git diff --check 통과.

PowerPoint 데스크톱 앱에서 실행한 검증은 아니다. 다른 환경에서 지정 글꼴이 없으면 편집본 글꼴이 대체될 수 있으며 PNG는 그대로 사용할 수 있다. 최신 원격 서버 상태는 이번 작업에서 재검사하지 않았다. 배포 근거는 기존 검증 기록이다.
