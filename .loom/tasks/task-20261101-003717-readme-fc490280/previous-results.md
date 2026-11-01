# Previous Results

24 older recorded result(s) were omitted. Promote durable context to Job Notes or explicit Context References.

## 28. 촬영 시나리오 자료 수집과 지역 행동요령·개인 준비 실파이프라인 검증

# 결과

공식 자료6건과 별도 A/B 합성 조건을 수집·분리했다. 지역 행동요령과 공통/개인 준비, 현재 동반·이동 상태 질문, 확인 후 정책 갱신을 구현해 실제 일반 서버에 배포했다. 런타임67933ce. 신규 휴대폰 경보 배너·알림음1회·위급3단계·아이 질문까지 확인했다.

## 검증

전체 PostgreSQL141 tests, Ruff, diff check 통과. 새 격리 시나리오의 실제 임베딩→검색→긴급큐→Qwen 통합→A/B 실제 Qwen 답변→사용자 확인→정책·경로 검증 all exit0. 공식 경보 API는 Qwen 전에 A1.553/B1.564초에 노출. 인터넷검색은실행했으나과거질의0건,저장근거5건사용. 실제예측·GPS·119·원격FCM은미실행.

## 산출물

docs/V2/delivery/filming-scenario-pipeline.md, filming-sources.md, filming-pipeline-verification.json, filming-model-metadata.json. data/filming과 tools/filming_scenario.py. 기존 synthetic 사건은 원문·이력 보존한 보관 상태로 전환했다.

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
