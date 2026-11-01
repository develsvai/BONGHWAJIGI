# 공유 대화 출처와 보존 범위

[문서 안내](README.md) · [공유 링크](https://chatgpt.com/share/6ae4872b-c438-83ee-940c-d2385795e0c1)

공유 페이지 제목은 「해커톤 아이디어」다. 2026년 10월 30일(KST)에 공개 페이지의 응답을 확보해 사용자 메시지 28개와 최종 답변 28개를 대화 순서대로 추출했다. 답변 생성 중 사용자에게 보인 진행 안내 15개도 [별도 파일](archive/progress-messages.md)에 보존했다. 시스템·도구 메시지, 중복 조각, 화면에 보이지 않는 내부 메시지는 원문으로 취급하지 않았다.

각 메시지에는 M001–M056 번호와 원문 메시지 ID를 붙였다. [보존 명세](archive/manifest.json)에 텍스트 길이, SHA-256, 원문 HTML SHA-256, 위치와 첨부 참조를 기록했다. 원문의 `<Link>`, `<Cite>`, `<AppBlock>` 같은 표현 태그와 UI 조건식·HTML 시안도 텍스트로 보존했다. 실행되는 프로토타입으로 변환한 것은 아니다.

| 문답 | 사용자 질문·수정 | 답변 | 원문 |
| --- | --- | --- | --- |
| 01 | 관광 안내 서비스 | 기존 형태 비교 | [M001–M002](archive/conversation-01.md#m001) |
| 02 | 지하철 로드뷰 | 실내 거리뷰와 3D 지도 | [M003–M004](archive/conversation-01.md#m003) |
| 03 | 환승 사진 길안내 | 환승 로드뷰 내비게이션 | [M005–M006](archive/conversation-01.md#m005) |
| 04 | 참신한 추천·정보보호 | 8개 후보 | [M007–M008](archive/conversation-01.md#m007) |
| 05 | 취업 공백 청년 | 세 가지 지원 후보 | [M009–M010](archive/conversation-02.md#m009) |
| 06 | 공백이 아니라 내 이야기 | 경험 회고·활동 추천 | [M011–M012](archive/conversation-02.md#m011) |
| 07 | AI가 사람을 추천 | 경험 기반 매칭 | [M013–M014](archive/conversation-02.md#m013) |
| 08 | 아동 대상 전환 | 여섯 가지 후보 | [M015–M016](archive/conversation-02.md#m015) |
| 09 | 아동 정보보호 통합 | 게시 전 보호 흐름 | [M017–M018](archive/conversation-03.md#m017) |
| 10 | L4 GPU 지원 | 멀티모달 개인정보 보호 | [M019–M020](archive/conversation-03.md#m019) |
| 11 | 외국인 QR 지하철 | 사진형 환승 안내 | [M021–M022](archive/conversation-03.md#m021) |
| 12 | 외국인 사진 제보 | 운영진 검토형 참여 데이터 | [M023–M024](archive/conversation-03.md#m023) |
| 13 | 고령 운전 문제 | 네 가지 후보 | [M025–M026](archive/conversation-04.md#m025) |
| 14 | 운전 예고편 조정 | 경로·영상 중심 | [M027–M028](archive/conversation-04.md#m027) |
| 15 | 농촌 그늘길 고민 | 폭염 회피 시간·쉼터 | [M029–M030](archive/conversation-04.md#m029) |
| 16 | 집 안 재난 비서 | 초기 대피 도우미 | [M031–M032](archive/conversation-04.md#m031) |
| 17 | 61세 이상 범죄 통계 | 통계·가능 원인 구분 | [M033–M034](archive/conversation-05.md#m033) |
| 18 | 고령자 고립 완화 | 사회적 연결 서비스 | [M035–M036](archive/conversation-05.md#m035) |
| 19 | 누구나 공감할 문제 | 일곱 가지 일상 후보 | [M037–M038](archive/conversation-05.md#m037) |
| 20 | 재난 비서의 추천 주제 | 대피 방법 개인화 | [M039–M040](archive/conversation-05.md#m039) |
| 21 | PPT 색상 1차 | 네이비 계열 | [M041–M042](archive/conversation-06.md#m041) |
| 22 | PPT 색상 재검토 | 차콜·그린·레드 계열 | [M043–M044](archive/conversation-06.md#m043) |
| 23 | 데이터·경로·3D | 단계별 시스템 구성 | [M045–M046](archive/conversation-06.md#m045) |
| 24 | 개인 상황별 추천 | 추천 엔진과 비교 시연 | [M047–M048](archive/conversation-06.md#m047) |
| 25 | MVP 화면 수 | 첫 7개 화면 초안 | [M049–M050](archive/conversation-07.md#m049) |
| 26 | 평상시 홈·재난 전환 | 지역 소식과 긴급 화면 | [M051–M052](archive/conversation-07.md#m051) |
| 27 | GPS·음성·상태 갱신 | 결과 페이지 통합 | [M053–M054](archive/conversation-07.md#m053) |
| 28 | 원형 음성 화면 | 자동 인식·끼어들기 | [M055–M056](archive/conversation-07.md#m055) |

## 첨부 이미지 3개

공유 페이지에서 이미지 첨부의 참조와 크기는 확인했으나 파일을 받을 수 있는 서명된 이미지 URL은 제공되지 않았다. 이미지 파일 자체는 이 기록에 없다. 각 이미지에 관해 사용자가 적은 설명과 답변의 시안·코드는 대화 원문에 모두 있다.

| 메시지 | 원래 파일명 | 크기 | 대화상 용도 |
| --- | --- | --- | --- |
| [M041](archive/conversation-06.md#m041) | `image.png` | 1282 × 922 | PPT 색상 변경 질문 |
| [M053](archive/conversation-07.md#m053) | `IMG_2004.jpg` | 2048 × 1981 | 음성 대화·상태 영역 스케치 |
| [M055](archive/conversation-07.md#m055) | `IMG_2005.jpg` | 2048 × 1989 | 원형 모션과 화면 비율 스케치 |

현재 폴더에 별도로 올라온 `nomal_home.png`, `disaster.png`는 위의 공유 대화 첨부 3개가 아니다. 두 PNG는 이후 작성한 [5개 화면 기획서](봉화지기_모바일_화면_기획서.md)의 평상시 홈과 긴급 대응 화면 예시다.

## 원문 속 사실·출처의 상태

답변은 외부 웹 자료를 인용하며 서비스 현황, 통계, 법률 및 기술 범위를 설명한다. [원문 외부 출처 목록](references.md)에 복원 가능한 링크와 메시지 위치를 연결했다. 링크의 원문 검증·현행성 확인은 이 작업에서 다시 하지 않았다. 참조 ID 일부는 메타데이터에서 실제 URL을 복원하지 못해 목록에 표시했다.
