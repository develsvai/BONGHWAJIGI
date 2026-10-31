# BONGHWAJIGI 봉화지기

여러 출처의 재난 정보를 모아 현재 위치와의 관련성을 평가하고, 사용자 상황에 맞는 행동과 대피 안내를 제공하는 공공 목적의 모바일 서비스입니다.

현재 단계는 **설계 정리 및 UI/UX 수령 대기**입니다. 팀원이 준비하는 UI/UX를 확인한 뒤 화면 흐름, 데이터 계약, 구현 범위를 맞춥니다. 이 저장소의 초기 산출물은 설계 문서이며, 모델 배포나 서비스 구현 완료를 의미하지 않습니다.

- [설계 문서 안내](docs/README.md)
- [서비스 목표와 사용자 시나리오](docs/product-and-scenarios.md)
- [데이터 수집과 대응 흐름](docs/architecture-and-data-flow.md)
- [AI 역할과 서버 구성](docs/ai-and-infrastructure.md)
- [결정 사항과 회의 대조](docs/decisions-and-meeting-review.md)
- [UI/UX 인계와 확인 항목](docs/ui-ux-handoff.md)

## 작업 기록

Loom workspace를 한국어로 초기화했습니다. 에이전트 작업 규칙은 [AGENTS.md](AGENTS.md)를 따릅니다. 현재 초기 작업 브랜치는 Loom 기본 정책에 맞춘 `develop`입니다.

```sh
loom status --json
loom resume --json
loom validate --strict
```

인증정보, 개인 위치 이력, 모델 가중치, 회의 녹음과 전체 전사는 저장소에 포함하지 않습니다.

## 개인 브랜치 발표자료

2026년 10월 31일 기준, `hyun02063185` 브랜치의 [발표자료 폴더](docs/presentations/README.md)에 작성한 PPTX 5개와 원본 템플릿 1개를 보관합니다. 발표용 PPT 5개는 `slides`에, 원본 템플릿은 `templates`에 모았습니다. 발표 순서는 이후 정리하며, 각 초안은 한 장짜리이고 전체 통합본은 아직 작성 전입니다.
