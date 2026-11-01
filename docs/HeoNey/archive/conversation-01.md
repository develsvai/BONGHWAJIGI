# 대화 원문 01 — 관광·지하철·해커톤 관점

[문서 안내](../README.md) · [출처 및 보존 범위](../source-and-coverage.md)

원문의 텍스트를 그대로 보존합니다. 답변의 UI 표현 태그·코드·조건식도 텍스트 블록 안에 포함했습니다. 제안, 통계, 외부 서비스 설명은 당시 대화 내용이며 이번 작업에서 사실 재검증한 결과가 아닙니다.

<a id="m001"></a>
## M001 · 사용자 — 관광 안내 서비스 탐색

원문 메시지 ID: `69a7e8c6-f9f7-42ba-8183-492fb0f40234`

`````text
우리나라 사람이 해외에서 여행온 사람들을 관광 안내해주는 서비스 같은 거 우리나라에 있어?
`````

<a id="m002"></a>
## M002 · 답변 — 관광 안내 서비스 탐색

원문 메시지 ID: `ea236eb4-c016-4794-9570-3d90a8d545e5`

`````text
**있어. 한국에 여행 온 외국인 관광객과 한국인 현지인을 연결해서 관광 안내를 하거나, 함께 돌아다니며 한국 문화를 체험하도록 하는 서비스가 이미 운영되고 있어.**

크게 세 가지로 나눌 수 있어.

1. **현지인 매칭형:** 일반 한국인과 외국인 여행자를 연결해 맛집, 카페, 관광지 등을 함께 방문
2. **로컬 체험형:** 한국인이 직접 만든 음식·문화·스포츠 체험 프로그램에 외국인이 참여
3. **전문 관광 가이드형:** 자격을 갖춘 가이드가 역사·문화 해설과 관광 일정 안내

## 실제 국내 서비스 사례

<box gap={3}>
  <row align=start gap={3}>
    <AsyncImage query="local Seoul localseoul meet Korean local traveller website logo" aspectRatio="1:1" maxWidth="112px"/>
    <box flex="1" gap={1}>
      **1. <Link url="https://localseoul.com/" title="local/seoul"/>**

      <text color="secondary" size="xs">한국인 친구 매칭형</text>

      외국인 여행자가 방문 날짜, 지역, 관심사를 등록하면 한국인 현지인과 연결해 주는 서비스야. 카페 방문이나 산책처럼 친구와 만나는 방식이고, 초기 운영 기간에는 무료 매칭을 제공하고 있어. 정식 관광 가이드 서비스는 아니야. <Cite ref="turn706193search0"/>
    </box>
  </row>
  <divider color="subtle"/>
  <row align=start gap={3}>
    <AsyncImage query="HanBuddy Korea baseball stadium local buddy Seoul tourists experience" aspectRatio="1:1" maxWidth="112px"/>
    <box flex="1" gap={1}>
      **2. <Link url="https://hanbuddy.kr/en" title="HanBuddy (한버디)"/>**

      <text color="secondary" size="xs">유료 로컬 동행 체험형</text>

      한국인 호스트와 외국인 관광객이 함께 야구·축구 경기를 보거나 한국 문화를 체험하는 서비스야. 일정과 인원을 선택해 예약·결제하며, 실제 참가자 후기와 상품 가격도 공개되어 있어. <Cite ref="turn706193search4"/>
    </box>
  </row>
  <divider color="subtle"/>
  <row align=start gap={3}>
    <AsyncImage query="BeKo Be Korean local experience Korean food market Seoul meetup" aspectRatio="1:1" maxWidth="112px"/>
    <box flex="1" gap={1}>
      **3. <Link url="https://be-ko.co.kr/" title="BeKo (비코)"/>**

      <text color="secondary" size="xs">한국인 모임 참여형</text>

      한국인이 평소 즐기는 식사, 전통시장 방문, 문화 체험 등의 활동에 외국인을 초대하는 플랫폼이야. 현지인이 이벤트를 만들고 외국인이 참가를 신청하는 구조이며, 현재 호스트 모집을 안내하고 있어. <Cite ref="turn706193search3"/>
    </box>
  </row>
  <divider color="subtle"/>
  <row align=start gap={3}>
    <AsyncImage query="Airbnb Experiences Seoul night walking tour local guide Naksan Seoul city wall" aspectRatio="1:1" maxWidth="112px"/>
    <box flex="1" gap={1}>
      **4. <Link url="https://www.airbnb.com/experiences/1143839" title="에어비앤비 체험 (Airbnb Experiences)"/>**

      <text color="secondary" size="xs">개인 호스트·전문 가이드 예약형</text>

      한국 현지 호스트가 직접 서울 야경 투어, 문화 체험, 맞춤형 관광 등을 운영하는 방식이야. 실제 예약 상품과 이용자 후기까지 확인할 수 있어. <Cite refs={["turn236587search12","turn236587search14"]}/>
    </box>
  </row>
  <divider color="subtle"/>
  <row align=start gap={3}>
    <AsyncImage query="Seoul guided walking tour cultural tourism volunteer guide Gyeongbokgung tourists" aspectRatio="1:1" maxWidth="112px"/>
    <box flex="1" gap={1}>
      **5. <Link url="https://english.visitseoul.net/walking-tour/" title="서울시 도보해설관광"/>**

      <text color="secondary" size="xs">공공 무료 관광 안내형</text>

      서울시에서 운영하는 무료 관광 프로그램이야. 문화관광해설사가 경복궁·북촌 등 관광지를 한국어·영어·일본어·중국어로 안내해. 사전 예약이 필요하고 개인적인 친구 매칭과는 달라. <Cite ref="turn236587search1"/>
    </box>
  </row>
</box>

## 서비스 기획 관점에서 보면

이미 유사 서비스가 존재하기 때문에 **'한국인과 외국인 관광객을 연결한다'는 기능 자체는 새로운 아이디어가 아니야.**

다만 서비스별 차이는 있어.

| 비교 항목 | 서비스 사례 |
|---|---|
| 친구처럼 편하게 만나기 | local/seoul |
| 한국인과 함께 체험하기 | HanBuddy, BeKo |
| 개인 맞춤 관광 안내 | 에어비앤비 체험 |
| 무료 역사·문화 안내 | 서울시 도보해설관광 |

특히 주의할 점은 법적 구분이야. 「관광진흥법」 제38조에 따르면 외국인 관광객을 대상으로 하는 **여행업자의 관광 안내에는 관광통역안내사 자격 요건**이 적용돼. 단순한 친구 만남과 유료 관광 안내는 동일하게 취급하면 안 되고, 플랫폼의 실제 운영 방식에 따라 등록·자격 요건을 검토해야 해. <Cite refs={["turn882825search3","turn882825search0"]}/>

한 가지 확인하고 싶은 게 있어.

**생각하는 서비스가 일반 한국인이 외국인 여행자와 연결돼 친구처럼 함께 돌아다니는 형태야? 아니면 한국인이 가이드 역할을 하고 돈을 받는 형태야?**

두 방식은 경쟁 서비스도, 사업 구조도 상당히 달라져.
`````

<a id="m003"></a>
## M003 · 사용자 — 지하철 실내 로드뷰

원문 메시지 ID: `05599dd2-0460-41e3-9f54-6d7fb118a989`

`````text
지하철 로드뷰시스템은 없어?
`````

<a id="m004"></a>
## M004 · 답변 — 지하철 실내 로드뷰

원문 메시지 ID: `986d9462-1bc6-47d0-be18-1a1e13f8bd4d`

`````text
**있어. 지하철역 내부를 실제 사진으로 둘러보는 로드뷰 서비스가 이미 존재해.** 다만 모든 지하철역을 지원하는 것은 아니고, 실내지도와 실제 사진 기반 로드뷰는 구분해야 해.

## 1. 네이버 지도 — 지하철역 실내 거리뷰

<AsyncImage ref="turn748706image0" aspectRatio="5:3" fit="contain"/>

<caption>네이버 지도의 역사 내부 거리뷰 및 층별 실내지도 예시. 출처: IT동아</caption>

- 일부 지하철역 내부를 360도 사진으로 확인할 수 있어.
- 통로, 안내 표지판, 개찰구 주변 등을 미리 살펴볼 수 있어.
- 실내지도에서 거리뷰를 지원하는 구간을 선택하면 실제 사진으로 전환돼.

2026년 2월 25일부터 일부 쇼핑시설의 실내뷰는 종료됐지만, **지하철역·공항 등 교통시설의 실내뷰는 유지한다는 것이 네이버의 방침**이야. <Cite refs={["turn674360view0","turn674360search4"]}/>

직접 확인: <Link url="https://map.naver.com/" title="네이버 지도"/>

## 2. 서울시 S-MAP — 3D 지하철역 내부 지도

<AsyncImageGroup query={["서울 S-MAP 지하철 역사 3D 실내지도 잠실역","서울시 에스맵 S-MAP 지하철 실내공간정보 3D 지도"]} aspectRatio="5:3" layout="carousel"/>

서울시의 <Link url="https://smap.seoul.go.kr/" title="S-MAP"/>은 잠실역 등 일부 지하철역의 내부 구조를 3D로 제공해.

실제 사진을 따라 이동하는 로드뷰라기보다는 건물 내부 구조를 입체적으로 살펴보는 방식이야. <Cite refs={["turn748706search1","turn748706search8"]}/>

## 3. 아직 부족한 부분은?

| 기능 | 확인된 현황 |
|---|---|
| 역사 내부 360도 사진 | 일부 역 지원 |
| 층별 구조 확인 | 지원 |
| 역 내부 모든 구간 연결 | 전체 지원 확인 안 됨 |
| 실내에서 목적지까지 실시간 길안내 | 일부 시설에서 기술 적용, 지하철 전체 지원은 확인 안 됨 |
| 외국어 기반 상세 환승 길안내 | 서비스별 지원 범위 확인 필요 |

특히 인천교통공사도 2024년에 **지하철 역사 내부 360도 로드뷰와 교통약자 전용 이동 경로**를 구현하는 기술을 실증 과제로 제시했어. 기존 서비스만으로 해결되지 않는 문제가 있다는 근거로 볼 수 있어. <Cite ref="turn748706search25"/>

---

해커톤 아이디어로 생각하는 거라면 한 가지 물어볼게.

**네가 생각하는 지하철 로드뷰는 어느 쪽이야?**

{@body const [choice,setChoice] = DIL.useState("route")}
<box gap={2}>
  <radio-group direction="col" value={choice} onChange={setChoice}>
    <radio value="view">**① 역사 내부 미리 보기** — 네이버 거리뷰처럼 역 안을 360도로 둘러보기</radio>
    <radio value="route">**② 역사 내부 길 안내** — 실제 사진을 보면서 환승 통로, 출구까지 이동하기</radio>
    <radio value="train">**③ 열차 내부 보기** — 타기 전에 지하철 차량 내부 구조 살펴보기</radio>
  </radio-group>
  <button block onClick={()=>GenUI.issueNewTurn(({view:"지하철역 내부를 360도 사진으로 미리 보는 서비스를 생각하고 있어.",route:"실제 역사 사진을 따라 환승 통로와 출구까지 길을 안내하는 서비스를 생각하고 있어.",train:"지하철 차량 내부를 미리 볼 수 있는 서비스를 생각하고 있어."})[choice])}>선택한 방식으로 자세히 알아보기</button>
</box>
`````

<a id="m005"></a>
## M005 · 사용자 — 사진형 환승 길안내

원문 메시지 ID: `48133603-9503-437d-8781-c6d428986759`

`````text
지하철 환승하거나할때 길찾기 어려우니까 로드뷰로 가는길 제공해주는거
`````

<a id="m006"></a>
## M006 · 답변 — 사진형 환승 길안내

원문 메시지 ID: `e02a3d67-800d-4519-877f-eafcc81dac27`

`````text
그렇다면 네가 생각한 건 **'지하철 환승 전용 로드뷰 내비게이션'**이야.

예를 들어 고속터미널역에서 3호선을 타고 가다가 9호선으로 환승해야 할 때, 단순히 환승 방향만 알려주는 게 아니라 **실제 역 내부 사진을 보여주면서 어느 통로로 가고 어디서 꺾어야 하는지 안내하는 서비스**지.

## 1. 국내에 이미 있는 서비스인가?

2026년 10월 기준으로 확인한 결과, **유사한 실내 길찾기 서비스는 있지만, 환승 경로 전체를 실제 사진으로 따라가는 방식이 상용화되어 널리 제공된다는 근거는 확인하지 못했어.**

| 기존 서비스 | 제공 기능 | 네 아이디어와의 차이 |
|---|---|---|
| 네이버 지도 | 실내지도, 일부 실내 거리뷰, 환승 정보 | 실제 사진과 환승 경로가 하나의 연속 안내로 제공되는지는 확인되지 않음 |
| 카카오지하철 | 빠른 환승 위치, 이동 경로 | 역사 내부 사진 기반 안내가 아님 |
| 또타지하철 | 환승 위치, 노선·교통약자 경로 안내 | 실제 사진을 따라가는 방식은 확인되지 않음 |
| 서울동행맵 | 지하철 역사 실내 내비게이션 확대 추진 | 2026년 말 일부 역 시범 운영 계획, 사진 기반인지는 불명확 |

<Cite refs={["turn906692search3","turn167602search6","turn276805search2","turn906692search39"]}/>

특히 서울시는 2026년 9월 발표된 보도에서 시청역 등을 대상으로 **실내외 연속 내비게이션을 연말까지 시범 운영할 계획**이라고 밝혔어. 따라서 시장의 방향 자체는 네 아이디어와 겹쳐. <Cite ref="turn276805search2"/>

## 2. 네가 생각한 서비스의 이용 방식

<box border radius="xl" padding={3} gap={3}>
  <row justify="between" align="center">
    **환승 로드뷰 — 화면 구성 예시**
    <badge color="secondary">기획 예시</badge>
  </row>
  <row align="center" justify="center" gap={2}>
    <badge>3호선 하차</badge>
    <icon name="arrow-right" color="tertiary"/>
    <badge>실내 경로 안내</badge>
    <icon name="arrow-right" color="tertiary"/>
    <badge>9호선 승강장</badge>
  </row>
  <AsyncImage query="Seoul subway station underground transfer passage interior wide angle directional signs corridors escalators South Korea" aspectRatio="16:9" width="100%"/>
  <box background="surface-secondary" radius="lg" padding={3} gap={1}>
    <row align="center" gap={2}>
      <icon name="arrow-right" color="success" size="lg"/>
      **앞쪽 환승 안내 표지판을 따라 직진**
    </row>
    <text color="secondary" size="xs">실제 구현 시 현재 경로의 사진에 이동 방향을 표시</text>
  </box>
  <row justify="between" align="center">
    <row align="center" gap={2}>
      <icon name="map" color="secondary"/>
      <text color="secondary" size="sm">환승 경로와 현재 단계</text>
    </row>
    <row gap={2}>
      <box background="surface-tertiary" radius="lg" padding={2}>
        <icon name="chevron-left"/>
      </box>
      <box background="surface-tertiary" radius="lg" padding={2}>
        <icon name="chevron-right"/>
      </box>
    </row>
  </row>
  <caption>위 사진은 지하철 내부 참고 이미지이며 실제 환승 경로 데이터는 아니야.</caption>
</box>

이 방식이라면 사용자가 갈림길마다 스마트폰에서 다음 사진을 확인하면서 이동할 수 있어. 지상 도로의 거리뷰와 비슷하지만, **목적지가 다른 노선의 승강장이라는 점**이 핵심이야.

## 3. 해커톤 아이디어로서의 가능성

기술적으로는 구현 가능한 방향이야. 다만 서비스 수준에 따라 난이도가 크게 달라져.

| 구현 방식 | 난이도 | AI 필요 여부 |
|---|---|---|
| 환승 경로를 따라 실제 사진을 순서대로 표시 | 낮음~중간 | 필요 없음 |
| 360도 사진에서 방향 화살표와 경로 표시 | 중간 | 필요 없음 |
| 카메라로 현재 위치를 인식하고 다음 방향 안내 | 높음 | 컴퓨터 비전 AI 활용 가능 |

특히 경쟁 기술도 있어. <Entity category="software" value="네이버지도"/>는 2025년 10월 23일부터 코엑스에서 **카메라로 실내 위치를 인식하는 AR 내비게이션**을 제공하고 있어. 다만 확인된 초기 적용 장소는 지하철 환승 통로가 아니야. <Cite ref="turn915453search0"/>

네 아이디어에서 차별화를 시도할 부분은 다음과 같아.

- 복잡한 환승역의 경로만 집중적으로 안내
- 분기점마다 실제 사진과 이동 방향 표시
- 외국인 관광객을 위한 다국어 안내
- QR코드로 시작 위치를 지정해 지하 GPS 문제를 우회

**가장 큰 과제는 AI 모델보다 실제 역사 사진과 정확한 환승 동선을 확보하는 일이야.** 촬영 허가, 초상권 처리, 역사 구조 변경에 따른 정보 갱신까지 고려해야 해.

따라서 해커톤에서는 지하철 전체가 아니라 **복잡한 환승역 한 곳을 선정해 실제 사진 기반의 환승 길안내를 구현하는 MVP**가 현실적이라고 판단해.

다만 현재 확인한 것은 경쟁 서비스의 공개 기능이야. 실제 사용자가 사진 기반 환승 안내를 얼마나 필요로 하는지, 기존 안내보다 길을 더 잘 찾는지는 별도 사용자 테스트가 필요해.
`````

<a id="m007"></a>
## M007 · 사용자 — 추천·정보보호의 새로운 관점

원문 메시지 ID: `a5bcb29b-fd50-4185-8778-a290574554e9`

`````text
해커톤 주제가 ai기반 추천 서비스랑 ai 기반 정보보호 서비스인데 추천이라는 흔한 주제안에서 이런아이디어가 나올 수 있구나 하는 서비스랑 정보보호 서비스인데 이런쪽의 관점으로 서비스를 만들었구나 하는 참신한 서비스를 만들었으면 좋겠는데
`````

<a id="m008"></a>
## M008 · 답변 — 추천·정보보호의 새로운 관점

원문 메시지 ID: `979598fd-cb30-4d0a-9132-78903065729d`

`````text
네가 원하는 방향은 단순히 AI를 이용한 편리한 서비스가 아니라, **주제를 해석하는 관점 자체가 독특한 서비스**라고 이해했어.

예를 들면 이런 차이야.

| 주제 | 일반적인 접근 | 관점을 바꾼 접근 |
|---|---|---|
| AI 추천 | 좋아할 만한 것을 추천 | **하지 말아야 할 행동을 추천** |
| AI 추천 | 목적지나 최단 경로 추천 | **실수할 가능성이 낮은 경로를 추천** |
| AI 추천 | 관심 있는 정보를 추천 | **내가 미처 생각하지 못한 질문을 추천** |
| AI 정보보호 | 이미 노출된 개인정보 탐지 | **여러 정보가 합쳐져 드러날 개인정보를 예측** |
| AI 정보보호 | 내 개인정보를 보호 | **내 행동 때문에 노출될 타인의 정보를 보호** |
| AI 정보보호 | 민감정보를 무조건 가리기 | **상황에 따라 꼭 필요한 정보만 공개** |

핵심은 추천의 대상을 상품·여행지에서 벗어나게 하거나, 정보보호의 대상을 비밀번호·주민등록번호에서 벗어나게 하는 거야.

실제로 정부에서도 AI 여행코스 추천, 일자리 추천, 복지 혜택 추천 등을 제공하고 있어. 이런 분야에 단순한 챗봇을 추가하는 것만으로는 차별화하기 어려워. <Cite refs={["turn399921search1","turn399921search2"]}/>

내가 해커톤 후보로 검토할 만하다고 생각하는 아이디어를 두 주제별로 나눠볼게. 아래의 참신성·구현 난이도 평가는 객관적으로 검증된 점수가 아니라, 현재 확인된 유사 사례와 예상 개발 범위를 바탕으로 한 기획 판단이야.

## 1. AI 기반 추천 서비스 — 추천의 대상을 바꾸기

<box gap={3}>
  <row align="start" gap={3}>
    <box background="surface-secondary" radius="lg" padding={3}>
      <icon name="route" size="xl"/>
    </box>
    <box flex="1" gap={1}>
      <title size="lg">① 가장 빠른 길이 아니라, 가장 덜 헤매는 길</title>
      <text color="secondary" weight="medium" size="xs">추천 대상: 길찾기 실패 확률이 낮은 경로</text>
      네가 생각했던 지하철 환승 로드뷰를 확장한 아이디어야. AI가 역 내부의 표지판, 갈림길, 계단, 환승 통로의 복잡도를 분석해 초행자가 실수할 가능성이 낮은 경로를 추천해.

      **예시:** "A 경로는 4분이지만 갈림길이 5개, B 경로는 6분이지만 표지판을 두 번만 따라가면 돼요."

      <text color="secondary" size="sm">AI 핵심: 이미지 인식 + 경로별 혼동 가능성 평가. 실제 실패 확률을 예측하려면 이용자 이동 기록 등 학습·검증 데이터가 필요해.</text>
    </box>
  </row>
  <divider color="subtle"/>
  <row align="start" gap={3}>
    <box background="surface-secondary" radius="lg" padding={3}>
      <icon name="message-circle-question" size="xl"/>
    </box>
    <box flex="1" gap={1}>
      <title size="lg">② 내가 해야 하는 질문을 추천하는 AI</title>
      <text color="secondary" weight="medium" size="xs">추천 대상: 사용자가 생각하지 못한 질문</text>
      보통 AI는 질문에 답하지만, 이 서비스는 사용자가 어떤 질문을 해야 하는지 알려줘.

      **예시:** 원룸 계약서를 보여주면 AI가 "퇴실할 때 청소비는 얼마인가요?", "중도 해지 조건은 무엇인가요?"처럼 확인이 필요한 질문을 추천해.

      <text color="secondary" size="sm">AI 핵심: 문서 맥락 파악 + 누락 정보 및 불명확한 조건 탐색. 법적 판단 대신 확인 질문을 제시하는 범위로 제한.</text>
    </box>
  </row>
  <divider color="subtle"/>
  <row align="start" gap={3}>
    <box background="surface-secondary" radius="lg" padding={3}>
      <icon name="shopping-bag" size="xl"/>
    </box>
    <box flex="1" gap={1}>
      <title size="lg">③ 아무것도 사지 말라고 추천하는 AI</title>
      <text color="secondary" weight="medium" size="xs">추천 대상: 소비하지 않아도 되는 선택</text>
      대부분의 쇼핑 추천은 구매를 유도하지만, 이 서비스는 구매하지 않는 것이 합리적인지 판단을 도와줘.

      **예시:** 새 주방용품을 사려고 사진을 찍으면, 이미 가지고 있는 도구로 같은 작업을 할 수 있는지 분석하고 대체 사용법을 추천해.

      <text color="secondary" size="sm">AI 핵심: 물체 인식 + 기능적 대체 가능성 판단. 물건의 정확한 성능이나 호환성을 사진만으로 단정하지 않도록 해야 해.</text>
    </box>
  </row>
  <divider color="subtle"/>
  <row align="start" gap={3}>
    <box background="surface-secondary" radius="lg" padding={3}>
      <icon name="hand-heart" size="xl"/>
    </box>
    <box flex="1" gap={1}>
      <title size="lg">④ 내가 원하는 곳이 아니라, 나를 필요로 하는 곳</title>
      <text color="secondary" weight="medium" size="xs">추천 대상: 내가 도움을 줄 수 있는 장소·상황</text>
      기존 봉사활동 추천과 반대로, 지역에서 해결하지 못한 작은 문제와 개인의 능력을 연결해.

      **예시:** "영어를 조금 할 수 있고 20분 여유가 있어요"라고 입력하면 외국인 안내 봉사나 짧은 지역 행사 지원 기회를 추천해.

      <text color="secondary" size="sm">AI 핵심: 자연어로 된 도움 요청과 개인의 역량·시간·제약 조건 매칭. 실제 검증된 모집 공고 데이터 확보가 필수.</text>
    </box>
  </row>
</box>

## 2. AI 기반 정보보호 — 무엇을 보호하는지 바꾸기

이쪽은 조금 더 독특한 문제를 정의할 여지가 있어. 특히 **정보 자체는 개인정보가 아니더라도, 정보를 조합하면 개인정보가 될 수 있다**는 점을 활용할 수 있지.

<box gap={3}>
  <row align="start" gap={3}>
    <box background="surface-secondary" radius="lg" padding={3}>
      <icon name="puzzle" size="xl"/>
    </box>
    <box flex="1" gap={1}>
      <title size="lg">① 흩어진 정보가 합쳐지면 무엇이 드러날까?</title>
      <text color="secondary" weight="medium" size="xs">보호 대상: 정보의 조합으로 추론되는 사생활</text>
      SNS 게시물 하나하나는 특별히 위험하지 않아 보여도, 여러 게시물이 합쳐지면 생활 패턴이나 위치가 드러날 수 있어.

      **예시:** 사진 3장을 업로드하면 AI가 위치 단서, 반복되는 시간대, 배경의 표지판 등을 분석하고 어떤 정보가 노출될 가능성이 있는지 설명해.

      <text color="secondary" size="sm">AI 핵심: 이미지·문맥을 종합해 조합 노출 위험 분석. 실제 주소나 신원을 추적하기보다 노출 위험을 경고하는 구조.</text>
    </box>
  </row>
  <divider color="subtle"/>
  <row align="start" gap={3}>
    <box background="surface-secondary" radius="lg" padding={3}>
      <icon name="file-check-2" size="xl"/>
    </box>
    <box flex="1" gap={1}>
      <title size="lg">② 정보를 가리는 게 아니라, 필요한 만큼만 보여주기</title>
      <text color="secondary" weight="medium" size="xs">보호 방식: 목적에 맞는 최소 정보 공개</text>
      일반 개인정보 마스킹은 주민등록번호 등을 탐지해 가리는 방식이지. 여기서는 정보를 전달하는 목적에 따라 공개 범위를 다르게 결정해.

      **예시:** 택배 파손을 신고하기 위해 운송장 사진을 올리면 배송 확인에 필요한 정보는 남기고, 수취인의 전화번호와 상세 주소는 가리는 방식을 제안해.

      <text color="secondary" size="sm">AI 핵심: 제출 목적 이해 + 문서 내 정보의 필요성 판단. 원본을 외부 AI에 전송하지 않는 보호 설계도 중요.</text>
    </box>
  </row>
  <divider color="subtle"/>
  <row align="start" gap={3}>
    <box background="surface-secondary" radius="lg" padding={3}>
      <icon name="users" size="xl"/>
    </box>
    <box flex="1" gap={1}>
      <title size="lg">③ 내가 찍은 사진인데, 내 정보만 보호하면 될까?</title>
      <text color="secondary" weight="medium" size="xs">보호 대상: 촬영자 외 제3자의 개인정보</text>
      여행 사진이나 행사 사진에는 촬영자가 의도하지 않은 사람과 정보가 들어갈 수 있어.

      **예시:** 행사 사진을 게시하기 전에 AI가 타인의 얼굴, 사원증, 명찰, 차량번호 등을 찾아 가릴 부분을 제안해.

      <text color="secondary" size="sm">AI 핵심: 이미지 속 제3자의 식별 가능 정보 탐지. 다만 이 분야는 이미 유사 서비스가 있어서 단순 자동 모자이크만으로는 차별화가 약해.</text>
    </box>
  </row>
  <divider color="subtle"/>
  <row align="start" gap={3}>
    <box background="surface-secondary" radius="lg" padding={3}>
      <icon name="hourglass" size="xl"/>
    </box>
    <box flex="1" gap={1}>
      <title size="lg">④ 개인정보에도 유통기한이 필요하지 않을까?</title>
      <text color="secondary" weight="medium" size="xs">보호 대상: 목적이 끝난 뒤에도 남는 정보</text>
      정보가 유출되지 않도록 하는 것뿐 아니라, 필요가 끝난 뒤에도 접근할 수 있다는 문제에 집중해.

      **예시:** 잠시 방문할 사람에게 출입 정보를 전달할 때 AI가 정보의 사용 목적을 분석해 1회 열람이나 시간제한 공유를 제안하고, 기한이 지나면 접근을 차단해.

      <text color="secondary" size="sm">AI 핵심: 정보의 성격·용도에 따른 공개 정책 추천. 실제 접근 차단은 AI가 아닌 서버의 권한 관리로 구현해야 해.</text>
    </box>
  </row>
</box>

## 3. 기존 사례를 조사해보면

참신함을 판단할 때 주의할 부분도 있어.

- <Link url="https://safesnap.lux.re/gb/" title="SafeSnap"/>은 사진을 게시하기 전에 위치가 노출될 가능성을 분석하고 수정 방법을 제안하고 있어. 따라서 사진의 위치정보 보호 자체는 완전히 새로운 접근이 아니야.
- <Link url="https://www.poof.photo/" title="Poof"/>와 <Link url="https://play.google.com/store/apps/details?id=com.koriai.jiwoocam" title="지켜줄Cam"/>은 사진 속 얼굴이나 개인정보를 보호하는 기능을 제공하고 있어.
- 2026년 <Link url="https://www.privacyinternational.org/sites/default/files/2026-02/Nowhere%20to%20Hide%20Privacy%20International_0.pdf" title="Privacy International 보고서"/>는 GPS 정보가 없어도 AI가 사진만으로 위치를 추론할 수 있는 위험을 분석했어.

즉, **정보의 조합으로 발생하는 위험은 실제 연구 근거가 있는 문제**야. 다만 내가 제안한 여러 장의 SNS 게시물에 대한 위험 시뮬레이션이 기존 서비스와 얼마나 다른지는 별도 경쟁 분석이 필요해.

## 4. 현재 단계에서의 후보 비교

<text color="secondary" size="xs">평가는 상대적인 기획 의견이며, 해커톤 기간과 팀 역량은 아직 확정하지 않은 상태야.</text>

| 아이디어 | 관점의 독특함 | 시연 구현 부담 | 판단 |
|---|---|---|---|
| 덜 헤매는 길 추천 | 높음 | 높음 | 시각적 시연 강점 |
| 해야 할 질문 추천 | 높음 | 낮음~중간 | AI 역할 명확 |
| 소비하지 않기 추천 | 높음 | 중간 | 문제의식 차별화 |
| 나를 필요로 하는 곳 추천 | 중간 | 중간~높음 | 공익성 강점 |
| 조합정보 노출 분석 | 높음 | 중간~높음 | 보안 주제에 적합 |
| 최소 정보 공개 | 중간~높음 | 중간 | 시연 완성도 확보 용이 |
| 제3자 개인정보 보호 | 중간 | 중간 | 경쟁 서비스 많음 |
| 개인정보 유통기한 | 중간~높음 | 중간 | 보안 구조까지 필요 |

내가 우선 더 발전시켜보고 싶은 것은 **추천 분야의 '해야 할 질문 추천'과 정보보호 분야의 '조합정보 노출 분석'**이야.

둘 다 관점을 뒤집는 핵심이 한 문장으로 설명되고, AI가 단순히 검색 결과를 정리하는 역할을 넘어 문맥을 이해하고 여러 단서를 종합해야 한다는 점이 있어.

다만 지금 8개는 개발 확정안이 아니라 아이디어 탐색 후보야. 참신함만 생각하면 훨씬 더 실험적인 아이디어도 가능해.

{@body const [direction,setDirection] = DIL.useState("radical")}
<box border radius="xl" padding={3} gap={3}>
  **다음에는 어떤 방향으로 아이디어를 더 확장할까?**
  <radio-group direction="col" value={direction} onChange={setDirection}>
    <radio value="radical">**독창성 최우선** — 기존 서비스의 형태 자체를 벗어나는 예상 밖의 아이디어</radio>
    <radio value="public">**사회문제 중심** — 평소 문제로 인식하지 못했던 불편이나 사각지대를 발견하는 아이디어</radio>
    <radio value="feasible">**해커톤 경쟁력 중심** — 독특하면서도 짧은 개발 기간에 완성도 높게 시연할 아이디어</radio>
  </radio-group>
  <button block onClick={()=>GenUI.issueNewTurn(({radical:"추천과 정보보호 두 주제를 더 파격적인 관점으로 해석한 독창적인 서비스 아이디어를 추가로 발굴해줘. 기존 흔한 서비스와의 차이를 분석해줘.",public:"AI 기반 추천 및 정보보호 주제에서 놓치고 있는 사회문제나 사각지대를 중심으로 참신한 서비스 아이디어를 추가로 발굴해줘.",feasible:"AI 추천과 정보보호 주제에서 해커톤 심사 경쟁력과 MVP 실현 가능성이 높은 참신한 서비스 아이디어를 더 발굴해서 비교해줘."})[direction])}>선택한 방향으로 아이디어 확장</button>
</box>
`````
