# 기술 스택 발표 페이지

사용자가 제공한 `ppt_8.webp`의 내용을 앞서 만든 아키텍처 발표 자료와 같은 스타일의 한 장으로 재구성했다.

- [편집용 PowerPoint](architecture-slides/output/bonghwajigi-tech-stack.pptx)
- [PNG 미리보기](architecture-slides/output/tech-stack.png)

기존 PPT를 가져와 1600×900 슬라이드 크기와 제목 서식, Apple SD Gothic Neo 글꼴, 녹색·청록색·주황색 팔레트 및 여백을 재사용했다. 본문과 도형은 PowerPoint에서 개별 편집할 수 있다. 글꼴이 없는 기기에서는 대체 글꼴이 적용될 수 있으며 PNG는 원래 모양을 유지한다.

일반 서버, GPU 서버, PostgreSQL, Redis, 앱의 역할과 직접 개발·검증 내용을 담았다. 원본의 GPU ‘검색·설명’은 실제 역할에 맞게 ‘검색용 벡터 생성·자료 요약·출처 정리’로 풀어 썼다. 원본의 모의 사용자 3명과 서버 82건·앱 14건은 제공 자료의 수치로 보존했다. 이 수치는 이번 작업에서 새로 실행한 검사나 최신 누적 건수가 아니다.

재생성 원본은 `architecture-slides/source/build-tech-stack.mjs`와 `finalize-tech-stack.mjs`다. 앞서 만든 세 장의 PPT와 이미지에는 변경을 가하지 않았다.
