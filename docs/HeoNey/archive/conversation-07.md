# 대화 원문 07 — 모바일 화면·최종 음성 UX

[문서 안내](../README.md) · [출처 및 보존 범위](../source-and-coverage.md)

원문의 텍스트를 그대로 보존합니다. 답변의 UI 표현 태그·코드·조건식도 텍스트 블록 안에 포함했습니다. 제안, 통계, 외부 서비스 설명은 당시 대화 내용이며 이번 작업에서 사실 재검증한 결과가 아닙니다.

<a id="m049"></a>
## M049 · 사용자 — MVP 7개 화면 초안

원문 메시지 ID: `b14cb40a-a471-48e2-9139-66df68431d54`

`````text
응 그럼 mvp나 영상 시연 제출에도 같은재난 상황에따른 대피방법 적합한 추천 이라는 거를 보여주면 더 설득력 있을 것같아 그럼 이런 플로우로 했을 때 모바일 화면의 구성을 뭐뭐를 넣어야할까 몇몇몇 화면들이 있어야할까 물론 나의 상황을 실시간으로 알리는 즉각 피드백이나 대화가 가능한 기능도 있어야하겠지만 일단 기본적인 나의 상황을 적어두는 프로필도 있어야할 것 같거든
`````

<a id="m050"></a>
## M050 · 답변 — MVP 7개 화면 초안

원문 메시지 ID: `0ee0bf6d-fea7-49c0-97b0-1c6a7afd6a8e`

`````text
현재 구상한 기능을 기준으로 하면 **해커톤 MVP는 핵심 화면 7개로 구성하는 것을 추천해.**

특히 이번 서비스는 일반적인 재난정보 앱과 달리 **같은 재난에서도 개인의 상황에 따라 서로 다른 대피 방법을 추천한다는 점**이 핵심이기 때문에, 화면 구성도 그 과정을 보여줄 수 있어야 해.

나는 앱을 다음 세 부분으로 나누는 게 좋겠어.

1. **평상시:** 개인 프로필 등록, 대피 준비, 재난정보 확인
2. **재난 발생 시:** 재난 알림, AI 음성 대화, 개인 맞춤형 대피 방법 추천
3. **대피 진행 중:** 3D 경로 안내 또는 도움 요청, 실시간 상황 변경 및 안전 확인

## 1. 모바일 화면 전체 구성

<box border radius="xl" padding={3} gap={2}>
  <box background="surface-secondary" radius="lg" padding={3} align="center" gap={1}>
    **① 홈 화면**
    <text size="xs" color="secondary">재난 현황 · 현재 상태 · 대피 준비</text>
  </box>
  <grid columns={2} gap={2}>
    <grid-item>
      <box border radius="lg" padding={3} align="center" gap={1} height="100%">
        **② 내 프로필**
        <text size="xs" color="secondary" textAlign="center">기본 이동 조건 · 동반자 · 비상 연락처</text>
      </box>
    </grid-item>
    <grid-item>
      <box border radius="lg" padding={3} align="center" gap={1} height="100%">
        **③ 재난 알림**
        <text size="xs" color="secondary" textAlign="center">재난 종류 · 공식 지시 · 영향 지역</text>
      </box>
    </grid-item>
  </grid>
  <row justify="center">
    <icon name="arrow-down" color="tertiary"/>
  </row>
  <box border radius="lg" padding={3} align="center" gap={1}>
    **④ AI 음성 대화**
    <text size="xs" color="secondary">현재 상황을 질문하고 기존 프로필과 비교</text>
  </box>
  <row justify="center">
    <icon name="arrow-down" color="tertiary"/>
  </row>
  <box background="surface-secondary" radius="lg" padding={3} align="center" gap={1}>
    **⑤ 개인 맞춤형 대피 추천**
    <text size="xs" color="secondary">추천 방법 · 추천 이유 · 실행 가능 여부</text>
  </box>
  <row justify="center">
    <icon name="git-branch" color="tertiary"/>
  </row>
  <grid columns={2} gap={2}>
    <grid-item>
      <box border radius="lg" padding={3} align="center" gap={1} height="100%">
        **⑥ 3D 대피경로**
        <text size="xs" color="secondary" textAlign="center">검증된 경로가 있는 경우</text>
      </box>
    </grid-item>
    <grid-item>
      <box border radius="lg" padding={3} align="center" gap={1} height="100%">
        **⑦ 도움 요청**
        <text size="xs" color="secondary" textAlign="center">혼자 대피하기 어려운 경우</text>
      </box>
    </grid-item>
  </grid>
  <box background="surface-tertiary" radius="md" padding={2} gap={1} align="center">
    <row align="center" justify="center" gap={2}>
      <icon name="refresh-cw" color="secondary"/>
      <text weight="medium" size="sm">언제든 현재 상황 변경 가능</text>
    </row>
    <text color="secondary" size="xs" textAlign="center">상황 변경 → AI 재확인 → 추천 결과 갱신</text>
  </box>
</box>

대피 중 상태 확인과 대피 완료 처리는 별도 페이지를 늘리기보다 ⑥·⑦ 화면에 공통으로 넣는 게 좋아.

---

## 2. 각 화면에 들어갈 구체적인 요소

| 화면 | 필수 구성 요소 | 주요 기능 |
|---|---|---|
| ① 홈 | 현재 위치, 재난 현황, 내 대피 준비 상태, AI 대화 버튼 | 앱의 시작점 |
| ② 내 프로필 | 이동 조건, 계단 이용 여부, 동반자, 비상 연락처, 대피 지원 필요 여부 | 평상시 기본 정보 저장 |
| ③ 재난 알림 | 재난 종류, 발생 지역, 공식 대피 지시, 발표 시각, 정보 출처 | 확인된 재난 상황 전달 |
| ④ AI 대화 | 음성 입력, 텍스트 입력, AI 질문, 현재 상태 확인 | 실시간 개인 상황 파악 |
| ⑤ 맞춤형 추천 | 추천 대피 방법, 이유, 이용 가능한 경로·지원 수단, 정보 확인 상태 | AI 추천 결과 제공 |
| ⑥ 3D 지도 | 지도, 대피 장소, 경로, 위험·통제 구역, 음성 안내 | 경로를 따라 이동하도록 지원 |
| ⑦ 도움 요청 | 119 연락, 보호자 연락, 위치 공유 동의, 요청 상태 | 스스로 이동이 어려운 경우 지원 |

실제 긴급전화 연결이나 보호자 알림이 구현되지 않았다면 버튼을 누른 것만으로 구조 요청이 전달됐다고 표시하면 안 돼. 시연에서는 모의 요청임을 명시해야 해.

## 3. 가장 중요한 화면은 ② 프로필과 ④ AI 대화야

이 두 화면을 잘 설계하면 개인 맞춤형 추천 기능이 자연스럽게 연결돼.

### ② 내 프로필 — 평소의 나를 등록

처음 설치했을 때 한 번 입력하고, 이후에는 변경된 정보만 수정할 수 있도록 구성해.

<box border radius="xl" padding={3} gap={3}>
  <row align="center" justify="between">
    **내 대피 프로필**
    <icon name="user-round" color="secondary"/>
  </row>
  <text color="secondary" size="xs">화면 구성 예시 · 실제 정보가 저장되는 입력 화면은 아님</text>
  {@body const [walking,setWalking] = DIL.useState("yes")}
  {@body const [stairs,setStairs] = DIL.useState("yes")}
  {@body const [alone,setAlone] = DIL.useState("yes")}
  <box gap={1}>
    <label>평소 혼자 걸어서 이동할 수 있나요?</label>
    <radio-group direction="row" value={walking} onChange={setWalking}>
      <radio value="yes">가능</radio>
      <radio value="no">도움 필요</radio>
    </radio-group>
  </box>
  <divider color="subtle"/>
  <box gap={1}>
    <label>계단을 이용할 수 있나요?</label>
    <radio-group direction="row" value={stairs} onChange={setStairs}>
      <radio value="yes">가능</radio>
      <radio value="no">어려움</radio>
    </radio-group>
  </box>
  <divider color="subtle"/>
  <box gap={1}>
    <label>평소 혼자 거주하시나요?</label>
    <radio-group direction="row" value={alone} onChange={setAlone}>
      <radio value="yes">예</radio>
      <radio value="no">아니요</radio>
    </radio-group>
  </box>
  <divider color="subtle"/>
  <box gap={1}>
    **추가 등록 정보**

    - 주로 머무는 장소 및 층수
    - 비상 연락처(선택)
    - 평소 이용 가능한 이동수단
    - 음성 안내 언어 및 글자 크기
  </box>
  <box background="surface-secondary" radius="lg" padding={3} gap={1}>
    <text color="secondary" size="xs">현재 입력 상태에 따른 프로필 요약 예시</text>
    **{walking==="yes" ? "독립 보행 가능" : "이동 지원 필요"} · {stairs==="yes" ? "계단 이용 가능" : "계단 이용 어려움"} · {alone==="yes" ? "1인 거주" : "동거인 있음"}**
  </box>
</box>

개인정보 수집은 가능한 한 적게 해야 해. 나이나 질병명을 반드시 입력받기보다 실제 대피에 필요한 이동 조건을 받는 것이 추천 기능에도 더 직접적이야.

그리고 **프로필은 고정된 사실이 아니라 평상시 상태를 나타내는 정보**로 취급해야 해.

평소 걸을 수 있던 사람도 재난 상황에서 다치거나 움직이기 어려워질 수 있으니까.

### ④ AI 대화 — 지금의 나를 확인

재난이 발생했을 때 프로필에 적힌 질문을 전부 다시 묻는 건 비효율적이야.

대신 AI가 현재 상황에서 꼭 필요한 정보만 확인하도록 구성하자.

<box border radius="xl" padding={3} gap={3}>
  <row align="center" justify="between">
    <row align="center" gap={2}>
      <icon name="audio-lines" color="secondary"/>
      **AI 재난 안내**
    </row>
    <badge>대화 예시</badge>
  </row>
  <box background="surface-secondary" radius="lg" padding={3}>
    **AI**

    "현재 지역에 홍수 대피 명령이 내려졌습니다. 평소에는 혼자 걸으실 수 있다고 등록하셨는데, 지금도 이동하실 수 있으신가요?"
  </box>
  <box border radius="lg" padding={3}>
    **사용자**

    "지금 다리가 아파서 혼자 걸어가기는 힘들어."
  </box>
  <box background="surface-secondary" radius="lg" padding={3} gap={1}>
    **AI**

    "현재 혼자 이동하기 어렵다는 말씀이시군요. 긴급 이동 지원을 요청할 수 있도록 연락 방법을 안내하겠습니다."
  </box>
  <row align="center" gap={2}>
    <icon name="mic" color="secondary" size="lg"/>
    <box flex="1" gap={1}>
      <text weight="medium" size="sm">말하기 또는 직접 입력</text>
      <text size="xs" color="secondary">음성 인식 결과는 사용자가 확인·수정 가능</text>
    </box>
  </row>
</box>

이 부분에서 실제 AI의 역할이 드러나.

**저장된 기본 프로필 + 현재 음성 대화에서 파악한 상태 → 현재 상황에 맞는 추천 결과**

다만 대화가 길어지면 안 돼. 긴급 상황에서는 필요한 질문을 최소화하고, 바로 119 연락 등 공식 긴급 대응에 접근할 수 있어야 해.

---

## 4. MVP 시연 영상은 이렇게 구성하는 게 좋겠어

영상에서 가장 중요한 건 화려한 3D 지도를 먼저 보여주는 게 아니라 **같은 재난에서 추천이 어떻게 달라지는지** 보여주는 거야.

<box border radius="xl" padding={3} gap={3}>
  <box gap={1}>
    <row align="center" gap={2}>
      <icon name="cloud-rain" color="secondary"/>
      **공통 시나리오**
    </row>
    <text color="secondary" size="sm">같은 마을, 같은 홍수 대피 명령, 같은 시각의 재난 데이터</text>
  </box>
  <grid columns={2} gap={2}>
    <grid-item>
      <box background="surface-secondary" radius="lg" padding={3} gap={2} height="100%">
        <text color="secondary" weight="medium" size="xs">사용자 A</text>
        <icon name="footprints" size="xl"/>
        **혼자 이동 가능**

        <text size="sm">AI가 현재 상태를 확인</text>
        <icon name="arrow-down" color="tertiary"/>
        **검증된 도보 대피경로 추천**
        <text size="xs" color="secondary">3D 경로 안내 실행</text>
      </box>
    </grid-item>
    <grid-item>
      <box background="surface-secondary" radius="lg" padding={3} gap={2} height="100%">
        <text color="secondary" weight="medium" size="xs">사용자 B</text>
        <icon name="accessibility" size="xl"/>
        **혼자 이동 불가능**

        <text size="sm">AI가 현재 상태를 확인</text>
        <icon name="arrow-down" color="tertiary"/>
        **긴급 이동 지원 안내**
        <text size="xs" color="secondary">연락·도움 요청 화면 실행</text>
      </box>
    </grid-item>
  </grid>
  <divider color="subtle"/>
  <box gap={1}>
    **추가 시연: 실시간 상황 변경**

    A가 처음에는 걸을 수 있다고 대답했지만 이후 "길이 막혀 있고 물이 차오르고 있어요"라고 말하면, AI가 기존 경로를 계속 안내하지 않고 경로의 유효성을 다시 확인하게 해.

    <text color="secondary" size="sm">실제 안전 판단에 필요한 통제·침수 데이터가 없으면 새로운 경로를 임의로 추천하지 않고 공식 긴급 대응을 안내</text>
  </box>
</box>

이 장면까지 구현하면 추천이 단순히 최초 프로필에 따라 갈라지는 조건문이 아니라, **상황 변화에 반응하는 개인화 시스템**이라는 것을 보여주기 좋아.

## 5. 모바일 사용성에서 반드시 고려할 것

주요 대상에 어르신과 1인 가구가 포함되어 있으므로 일반 앱과는 다른 우선순위가 필요해.

- 화면마다 **음성으로 말하기**, **긴급전화**, **내 상황 변경**을 쉽게 이용할 수 있어야 해.
- AI가 질문할 때는 한 번에 많은 정보를 묻지 않고, 큰 글씨와 명확한 선택 버튼을 함께 제공해야 해.
- 3D 경로를 이해하기 어려운 사용자를 위해 2D 지도나 간단한 텍스트 안내도 제공할 수 있어야 해.
- 재난정보에는 반드시 출처와 갱신 시각을 표시하고, 통신 장애 시 최신 정보인 것처럼 안내하지 않아야 해.

특히 재난 발생 중에 회원가입이나 복잡한 프로필 작성부터 요구해서는 안 돼. 프로필이 없는 사용자도 공식 재난정보와 긴급 연락 기능을 즉시 이용할 수 있어야 해.

## 6. 실제 제작 우선순위

| 우선순위 | 화면 | 이유 |
|---|---|---|
| 필수 | 홈 | 서비스 접근 |
| 필수 | 프로필 | 개인화 데이터 확보 |
| 필수 | 재난 알림 | 시나리오 시작 |
| 필수 | AI 음성 대화 | 실시간 상황 분석 |
| 필수 | 개인 맞춤 추천 | 해커톤 주제의 핵심 |
| 필수 | 3D 경로 안내 | 추천 결과 시각화 |
| 필수 | 도움 요청 | 다른 유형의 개인화 결과 시연 |
| 이후 | 대피 이력, 보호자 관리, 통계 | 초기 MVP 핵심에서 제외 |

**결론적으로 7개 핵심 화면이면 충분해.** 화면 수를 늘리는 것보다 동일한 재난 데이터에서 사용자 프로필과 현재 상황에 따라 다른 결과가 나오는 기능을 확실하게 구현하는 것이 중요해.

현재 화면 기획은 **로그인 없는 체험 접근, 선택적 프로필 등록, 모바일 앱, 홍수 중심 MVP, 모의 재난 데이터 사용**을 가정했어. 실제 재난에 사용하는 상용 앱이 아니라 해커톤 시연을 위한 구성이야.

그리고 아직 UI 디자인 단계에서 결정하지 않은 부분이 하나 있어. **AI 대화를 홈 화면에서 언제든 열 수 있는 형태로 둘지, 재난 발생 시 자동으로 대화 화면에 진입시키는 형태로 둘지**인데, 이 두 가지는 병행할 수 있어. 평상시에는 홈의 대화 버튼을 통해 접근하고, 공식 대피 명령이 확인됐을 때는 즉시 확인할 수 있는 재난 안내 화면과 음성 안내를 제공하는 방식이 적절해 보여.
`````

<a id="m051"></a>
## M051 · 사용자 — 평상시 홈과 재난 전용 화면

원문 메시지 ID: `f9d16660-aae1-479c-acca-559ae3eaf83f`

`````text
요즘 우리 지역은 이런 느낌으로 설정한 지역반경 몇미터? 내의 재난이 있었던 사항? 지역 소식? 불이나 이런거 알려주는 거를 홈화면으로 하면 될 것 같고 어차피 현재 상태나 대피 준비는 실제 상황이 일어났을때 전용 화면이 뜨는 식으로 하면 될 것 같아 재난상황이 되면 재난 단계에 따라 앱 알림이나 소리로 알려주고 그떄는 앱 들어가면 홈화면이 아닌 재난 알림 화면이 뜨면 되겠어 거기서는 간단하게 어떤 재난 상황인지 크게 보여주고 영향지역은 전체 영향지역중 내가 어디에 있다를 알려주면 될것같고 그 아래 공식지시와 대피 방법을 알려주면 될 것 같아 그리고 현재 상황을 알려주세요(라거나 현재 이동이 어려우신가요?_상황별 맞춤 멘트) 라는 버튼이 있어서 그걸 누르면 ai로 음성 대화를 할 수 있는거지 그럼 맞춤 대피 방법을 알려주거나 대신 신고를 해주거나 하는 방법으로 그리고 3d 대피경로를 제공할 수 있는 경우 내상황을 다알려주고나서 대피경로를 안내해드릴까요? 하는선택지를 띄워주면 되고 아니면 다른 선택지로 119신고 가 있으면 될 것 같아 그리고 상황변경은 ai 음성 대화 한켠에 버튼은 따로 만들어두거나 하는식으로 재난 알림 화면이
`````

<a id="m052"></a>
## M052 · 답변 — 평상시 홈과 재난 전용 화면

원문 메시지 ID: `ddd4982d-26a9-41e0-9b63-d6ccc209dcc9`

`````text
지금 제안한 구조라면 기존의 7개 화면을 유지할 필요가 없어. **평상시에는 지역 재난정보를 확인하는 앱, 재난 발생 시에는 개인 맞춤형 대피 지원 앱으로 전환되는 구조**가 더 자연스러워.

특히 좋은 점은 재난 발생 후 사용자가 홈 화면에서 대피 기능을 찾아다닐 필요가 없다는 거야.

다만 모든 재난 알림에서 화면을 강제로 전환하기보다는 **재난의 심각도와 사용자에게 실제로 적용되는 대피 지시를 기준으로 화면을 전환**하는 게 적절해.

# 1. 수정된 모바일 앱 전체 구조

<box border radius="xl" padding={3} gap={2}>
  <box background="surface-secondary" radius="lg" padding={3} align="center" gap={1}>
    <icon name="house" size="lg" color="secondary"/>
    **① 평상시 홈**
    <text color="secondary" size="xs" textAlign="center">우리 지역 재난 소식 · 주변 사고 · 재난 이력</text>
    <text color="secondary" size="xs">프로필 설정 및 대피 준비</text>
  </box>
  <row justify="center" align="center" gap={2}>
    <icon name="arrow-down" color="tertiary"/>
    <text color="secondary" size="xs">지역에 영향을 주는 재난 발생</text>
  </row>
  <box border radius="lg" padding={3} align="center" gap={1}>
    <icon name="bell-ring" color="secondary" size="lg"/>
    **② 재난 알림 · 긴급 모드**
    <text color="secondary" size="xs" textAlign="center">재난 종류 · 내 위치 · 공식 지시 · 기본 행동요령</text>
  </box>
  <row justify="center">
    <icon name="arrow-down" color="tertiary"/>
  </row>
  <box background="surface-secondary" radius="lg" padding={3} align="center" gap={1}>
    <icon name="mic" color="secondary" size="lg"/>
    **③ AI 상황 대화**
    <text color="secondary" size="xs" textAlign="center">저장된 프로필 + 현재 상황 확인</text>
    <text color="secondary" size="xs">상황 변경 · 추가 정보 전달</text>
  </box>
  <row justify="center">
    <icon name="arrow-down" color="tertiary"/>
  </row>
  <box border radius="lg" padding={3} align="center" gap={1}>
    <icon name="brain-circuit" color="secondary" size="lg"/>
    **④ 개인 맞춤형 대피 추천**
    <text color="secondary" size="xs" textAlign="center">실행 가능한 대피 방법과 추천 이유 제시</text>
  </box>
  <row justify="center">
    <icon name="git-branch" color="tertiary"/>
  </row>
  <grid columns={2} gap={2}>
    <grid-item>
      <box background="surface-secondary" radius="lg" padding={3} align="center" gap={1} height="100%">
        <icon name="map" color="secondary" size="lg"/>
        **⑤ 3D 경로 안내**
        <text size="xs" color="secondary" textAlign="center">확인된 이동 경로 표시</text>
      </box>
    </grid-item>
    <grid-item>
      <box background="surface-secondary" radius="lg" padding={3} align="center" gap={1} height="100%">
        <icon name="phone-call" color="secondary" size="lg"/>
        **⑥ 도움 요청**
        <text size="xs" color="secondary" textAlign="center">119 연결 · 보호자 연락</text>
      </box>
    </grid-item>
  </grid>
  <box background="surface-tertiary" radius="md" padding={2} align="center" gap={1}>
    <text weight="medium" size="sm">공통 기능 · 내 상황이 바뀌었어요</text>
    <text color="secondary" size="xs">AI 재대화 → 기존 추천 재검토</text>
  </box>
</box>

여기에 **내 프로필 설정 화면 1개**를 추가하면 총 7개 화면이야. 다만 ④ 추천 결과를 ③ AI 대화 화면 안에서 보여주면 실제로는 6개 정도로 줄일 수도 있어.

# 2. 평상시 홈 화면

네가 말한 대로 '요즘 우리 지역은 어떤 상황인가?'에 집중하는 게 좋아.

<box border radius="xl" padding={3} gap={3}>
  <row justify="between" align="center">
    <box gap={1}>
      <title size="lg">우리 동네 안전 소식</title>
      <row align="center" gap={1}>
        <icon name="map-pin" size="xs" color="secondary"/>
        <text color="secondary" size="xs">설정 지역 · 서울 ○○동</text>
      </row>
    </box>
    <icon name="settings" color="secondary"/>
  </row>
  <box background="surface-secondary" radius="lg" padding={3} gap={2}>
    **주변 소식 조회 범위**
    {@body const [radius,setRadius] = DIL.useState("3")}
    <radio-group direction="row" value={radius} onChange={setRadius}>
      <radio value="0.5">500m</radio>
      <radio value="1">1km</radio>
      <radio value="3">3km</radio>
      <radio value="5">5km</radio>
    </radio-group>
    <text color="secondary" size="xs">선택한 반경 {radius==="0.5"?"500m":radius+"km"} 내의 위치정보가 확인된 소식을 조회하는 설정 예시</text>
  </box>
  <box gap={2}>
    **최근 지역 재난·안전 소식**
    <row align="start" gap={3}>
      <icon name="flame" color="danger"/>
      <box flex="1" gap={1}>
        **주변 화재 발생 이력**
        <text color="secondary" size="xs">발생 장소 · 발생 일시 · 공식 출처</text>
      </box>
      <icon name="chevron-right" color="tertiary"/>
    </row>
    <divider color="subtle"/>
    <row align="start" gap={3}>
      <icon name="cloud-rain" color="secondary"/>
      <box flex="1" gap={1}>
        **지역 기상특보 및 호우 전망**
        <text color="secondary" size="xs">영향 지역 · 발표 시각 · 정보 출처</text>
      </box>
      <icon name="chevron-right" color="tertiary"/>
    </row>
    <divider color="subtle"/>
    <row align="start" gap={3}>
      <icon name="shield" color="secondary"/>
      <box flex="1" gap={1}>
        **주변 대피시설 확인**
        <text color="secondary" size="xs">재난 유형별 시설 정보와 확인 시각</text>
      </box>
      <icon name="chevron-right" color="tertiary"/>
    </row>
  </box>
  <divider color="subtle"/>
  <row justify="around">
    <box align="center" gap={1}>
      <icon name="house"/>
      <text size="xs" weight="medium">홈</text>
    </box>
    <box align="center" gap={1}>
      <icon name="map"/>
      <text size="xs" color="secondary">지역 지도</text>
    </box>
    <box align="center" gap={1}>
      <icon name="user-round"/>
      <text size="xs" color="secondary">내 프로필</text>
    </box>
  </row>
</box>
<caption>실제 지역 소식이나 재난 발생 정보를 표시한 화면이 아닌 UI 구상 예시야.</caption>

여기서 한 가지를 구분할 필요가 있어.

**지역 소식 조회 범위와 긴급 재난 알림 범위는 별도로 관리하는 게 좋아.**

예를 들어 사용자가 주변 소식을 500m로 설정했다고 해서 2km 떨어진 하천의 범람으로 거주지에 대피 명령이 내려졌을 때 알림을 놓치면 안 되니까.

일반 지역 소식은 사용자가 정한 반경으로 보여주고, 긴급 알림은 공식 재난 영향 지역과 실제 사용자의 위치를 기준으로 판단하는 구조를 추천해.

# 3. 재난 발생 시 전용 화면

이 화면은 네가 구상한 대로 **재난 상황 설명과 지금 해야 할 행동이 가장 먼저 보이도록** 배치하는 게 좋아.

<box border radius="xl" padding={3} gap={3}>
  <box background="#852D2D" theme="dark" radius="lg" padding={3} gap={2}>
    <row justify="between" align="center">
      <row align="center" gap={2}>
        <icon name="alert-triangle" color="#FFFFFF"/>
        <text color="#FFFFFF" weight="medium" size="sm">재난 대피 안내</text>
      </row>
      <icon name="volume-2" color="#FFFFFF"/>
    </row>
    <title size="2xl" color="#FFFFFF">홍수 대피 명령</title>
    <text color="#FFFFFF">현재 지역에 공식 대피 명령이 발령된 모의 상황입니다.</text>
  </box>
  <box gap={2}>
    <row align="center" justify="between">
      **내 위치와 영향 지역**
      <text size="xs" color="secondary">위치 확인 필요</text>
    </row>
    <svg viewBox="0 0 340 160" width="100%" xmlns="http://www.w3.org/2000/svg">
      <rect width="340" height="160" rx="9" fill="#EEF1EC"/>
      {#each [25,65,105,145] as y}
        <path d={`M0 ${y} H340`} stroke="#FFFFFF" strokeWidth="9"/>
      {/each}
      {#each [48,108,185,270,315] as x}
        <path d={`M${x} 0 V160`} stroke="#FFFFFF" strokeWidth="8"/>
      {/each}
      <path d="M0 88 Q65 36 115 75 T230 74 T340 58" fill="none" stroke="#8BB9D5" strokeWidth="14"/>
      <path d="M82 25 Q156 3 233 30 L280 68 L244 130 Q162 154 92 115 L65 73 Z" fill="#E99F96" fillOpacity=".5" stroke="#CC6257" strokeWidth="2" strokeDasharray="5 4"/>
      <circle cx="166" cy="82" r="11" fill="#FFFFFF"/>
      <circle cx="166" cy="82" r="7" fill="#2F6CBE" stroke="#FFFFFF" strokeWidth="2"/>
      <rect x="178" y="66" width="83" height="27" rx="7" fill="#FFFFFF"/>
      <text x="219" y="84" fill="#263238" fontSize="12" textAnchor="middle" fontWeight="bold">내 위치</text>
      <rect x="13" y="132" width="118" height="21" rx="6" fill="#FFFFFF"/>
      <rect x="22" y="138" width="11" height="10" rx="2" fill="#E99F96" stroke="#CC6257"/>
      <text x="40" y="146" fontSize="10" fill="#3D4549">재난 영향 지역</text>
    </svg>
    <caption>임의 도형으로 만든 지도 예시. 실제 침수 예상 범위와는 무관해.</caption>
  </box>
  <box background="surface-secondary" radius="lg" padding={3} gap={2}>
    **공식 대피 지시 및 기본 행동요령**
    <text size="sm">발령기관의 공식 대피 지시를 우선 따르세요. 침수된 도로와 지하 공간에 접근하지 마세요.</text>
    <text color="secondary" size="xs">실제 서비스에서는 발령기관 · 발표시각 · 갱신시각 표시</text>
  </box>
  <box background="rgba(28,91,121,0.08)" border={{size:1,color:"subtle"}} radius="lg" padding={3} gap={2}>
    <row align="center" gap={2}>
      <icon name="audio-lines" color="default" size="lg"/>
      **현재 상황을 알려주세요**
    </row>
    <text size="sm">혼자 이동할 수 있는지, 도움이 필요한지 말씀해 주세요. 현재 상황에 맞는 대응 방법을 찾아드릴게요.</text>
    <box background="#205D78" theme="dark" radius="lg" padding={3} align="center">
      <row align="center" gap={2}>
        <icon name="mic" color="#FFFFFF"/>
        <text color="#FFFFFF" weight="medium">AI에게 말하기</text>
      </row>
    </box>
  </box>
  <box border radius="lg" padding={3}>
    <row align="center" justify="center" gap={2}>
      <icon name="phone-call" color="danger"/>
      **119 긴급전화**
    </row>
  </box>
</box>

이 화면에서 중요한 구성은 다음 순서야.

**무슨 재난인가 → 내가 영향 지역에 있는가 → 공식 지시는 무엇인가 → 내 상황에 맞는 추가 지원을 받으려면 어떻게 하는가.**

그리고 재난 발생 시 AI 대화를 시작하기 전에 무조건 질문에 대답하도록 만들면 안 돼. 긴급한 경우에는 AI 대화를 거치지 않고도 119에 바로 연락할 수 있어야 해.

# 4. AI 대화 화면은 별도의 채팅 앱처럼 만들지 않는 게 좋아

AI가 길게 대화하는 것이 목적이 아니니까, 음성 대화 화면에서는 **현재 AI가 이해한 사용자 상황과 가능한 다음 행동**을 보여주는 게 좋아.

<box border radius="xl" padding={3} gap={3}>
  <row align="center" justify="between">
    **AI 대피 지원**
    <badge>홍수 대응 중</badge>
  </row>
  <box background="surface-secondary" radius="lg" padding={3} gap={2}>
    <text color="secondary" size="xs">저장된 내 프로필</text>
    <row wrap="wrap" gap={2}>
      <badge>1인 가구</badge>
      <badge>평소 독립 보행 가능</badge>
    </row>
  </box>
  <box gap={2}>
    <row align="center" gap={2}>
      <icon name="volume-2" color="secondary"/>
      **AI**
    </row>
    "현재 혼자 이동하실 수 있으신가요?"
    <box background="surface-secondary" radius="lg" padding={3}>
      <text color="secondary" size="xs">사용자 응답</text>
      "지금은 다리가 아파서 계단을 올라가기 힘들어."
    </box>
  </box>
  <box border radius="lg" padding={3} gap={2}>
    **AI가 확인한 현재 상황**
    <row align="center" gap={2}>
      <icon name="check" color="success"/>
      <text size="sm">걷기는 가능</text>
    </row>
    <row align="center" gap={2}>
      <icon name="alert-circle" color="secondary"/>
      <text size="sm">계단 이용 어려움</text>
    </row>
    <row align="center" gap={2}>
      <icon name="help-circle" color="secondary"/>
      <text size="sm">외부 이동 경로 확인 필요</text>
    </row>
    <text color="secondary" size="xs">인식 내용이 틀리면 수정할 수 있습니다.</text>
  </box>
  <grid columns={2} gap={2}>
    <grid-item>
      <box border radius="lg" padding={3} align="center" gap={1}>
        <icon name="refresh-cw"/>
        <text weight="medium" size="sm">상황 변경</text>
      </box>
    </grid-item>
    <grid-item>
      <box border radius="lg" padding={3} align="center" gap={1}>
        <icon name="keyboard"/>
        <text weight="medium" size="sm">직접 입력</text>
      </box>
    </grid-item>
  </grid>
  <box background="surface-secondary" radius="lg" padding={3} align="center" gap={1}>
    <icon name="mic" size="xl"/>
    **눌러서 말하기**
  </box>
</box>

이때 '상황 변경'은 별도 화면이 아니라 **현재 정보를 다시 입력하거나 음성으로 정정하는 기능**이면 충분해.

예를 들어 "아까는 걸을 수 있었는데 지금은 못 걷겠어요"라고 말하면 추천 결과를 다시 판단하는 거지.

# 5. 맞춤 대피 추천 화면은 하나의 고정된 화면일 필요가 없어

AI가 확인한 상태에 따라 다음 선택지가 달라지는 구조가 적절해.

{@body const [userType,setUserType] = DIL.useState("stairs")}
<box border radius="xl" padding={3} gap={3}>
  **같은 홍수 상황에서 개인별 추천 결과 비교**
  <radio-group direction="col" value={userType} onChange={setUserType}>
    <radio value="walk">A · 혼자 걷고 계단도 이용 가능</radio>
    <radio value="stairs">B · 걷기는 가능하지만 계단 이용 어려움</radio>
    <radio value="help">C · 혼자 이동할 수 없음</radio>
  </radio-group>
  <divider color="subtle"/>
  <box background="surface-secondary" radius="lg" padding={3} gap={2}>
    <text color="secondary" size="xs">AI 맞춤형 대피 추천 · 가상 결과</text>
    {#if userType==="walk"}
      <row align="center" gap={2}>
        <icon name="footprints" size="lg"/>
        **도보 대피경로 안내**
      </row>
      이동 가능한 상태이므로 공식적으로 확인된 도보 대피경로가 있다면 해당 경로를 안내합니다.
      <box background="surface" radius="lg" padding={3} align="center">
        **3D 대피경로 확인**
      </box>
    {:else if userType==="stairs"}
      <row align="center" gap={2}>
        <icon name="route" size="lg"/>
        **계단 없는 대피경로 우선 확인**
      </row>
      계단을 이용하기 어렵다고 말씀하셨기 때문에 계단이 포함된 경로는 제외하고 접근성이 확인된 경로를 찾습니다.
      <box background="surface" radius="lg" padding={3} align="center">
        **이용 가능한 경로 확인**
      </box>
    {:else}
      <row align="center" gap={2}>
        <icon name="phone-call" size="lg"/>
        **긴급 이동 지원 안내**
      </row>
      혼자 이동할 수 없는 상황이므로 무리한 도보 대피를 안내하지 않고 긴급 지원 요청을 우선 안내합니다.
      <box background="surface" radius="lg" padding={3} align="center">
        **119 긴급전화 연결**
      </box>
    {/if}
  </box>
  <row justify="between">
    <text size="sm" color="secondary">현재 상황이 달라졌나요?</text>
    <text size="sm" weight="medium"><icon name="refresh-cw" inline/> 다시 알려주기</text>
  </row>
  <caption>이 인터랙션은 추천 결과가 달라지는 원리를 보여주는 예시이며, 실제 대피 안전성을 판단하지 않아.</caption>
</box>

**3D 경로 화면을 모든 사용자에게 보여줄 필요는 없어.** 이동이 가능한 사람에게는 지도를 제공하지만, 구조 지원이 필요한 사람에게는 연락 수단을 먼저 제공하는 것이 개인 맞춤형 서비스의 핵심이야.

또 119 신고의 경우 AI가 통화 내용을 준비하거나 상황을 정리하는 것은 가능하지만, 실제 신고를 대신 접수·전달하려면 별도의 통신·기관 연동과 확인 절차가 필요해. MVP에서는 실제 연결 가능한 전화 버튼과 모의 신고 시연을 구분해야 해.

# 6. 재난 알림 단계별로 앱의 반응을 달리하자

여기는 네 구상에서 추가로 명확하게 정의하면 좋은 부분이야.

| 단계 | 앱 동작 | 초기 화면 |
|---|---|---|
| 일반 지역 소식 | 홈에 게시 | 일반 홈 |
| 주의가 필요한 기상특보 | 일반 알림, 상세보기 제공 | 홈 또는 특보 상세 |
| 사용자 지역에 공식 대피 권고·명령 | 눈에 띄는 긴급 알림과 음성 안내 시도 | 재난 전용 화면 우선 |
| 즉각적인 생명 위험·긴급구조 필요 | 긴급 연락 및 공식 행동지침 우선 | 긴급 대응 화면 |

이 단계는 서비스 설계 예시이고, 실제 경보 등급은 공식 재난정보의 분류와 지시를 기준으로 연결해야 해.

특히 앱에서 내는 알림음은 스마트폰의 알림 권한, 무음 모드, 운영체제 제약으로 인해 항상 들린다고 보장할 수 없어. 정부의 긴급재난문자와 동일한 전달력을 가진 것처럼 설명해서도 안 돼.

앱을 직접 열었을 때는 현재 유효한 대피 명령이 있다면 재난 화면을 먼저 보여주되, 공식 지시가 해제됐을 때는 일반 홈으로 돌아오게 설계하면 돼.

---

## 7. 현재 단계의 화면 설계 정리

| 화면 | 핵심 기능 | 필요성 |
|---|---|---|
| ① 평상시 홈 | 설정 지역의 재난·안전 소식 | 필수 |
| ② 내 프로필 | 평상시 이동 능력, 동거 여부, 비상 연락처 | 필수 |
| ③ 재난 알림 | 재난 정보, 내 위치, 공식 대피 지시 | 필수 |
| ④ AI 음성 대화 | 현재 상태 파악·변경·확인 | 필수 |
| ⑤ 개인별 대피 추천 | 상황별 추천 방법과 근거 | 필수 |
| ⑥ 3D 경로 안내 | 검증된 대피경로의 시각화 | 조건부 |
| ⑦ 도움 요청 | 긴급전화·지원 절차·연락 상태 | 조건부 |

여기서 ⑥과 ⑦은 개인별 추천 결과에 따라 진입하는 화면으로 두면 돼. 별도로 **설정 화면, 공지 목록, 상세 기록, 대피 이력** 같은 기능은 MVP에 당장 넣지 않아도 돼.

### 해커톤 시연에서는 이 순서가 가장 설득력 있어

**평상시 홈 → 모의 홍수 대피 명령 발생 → 재난 화면으로 전환 → 사용자 A의 AI 대화 → 3D 대피경로 추천 → 사용자 B의 AI 대화 → 다른 대피 방법 추천 → 상황 변경 시 결과 갱신.**

이렇게 하면 홈 화면과 재난 모드의 차이, AI의 역할, 개인화 추천, 3D 경로 기술을 하나의 이야기로 보여줄 수 있어.

다만 이 단계에서 아직 확정되지 않은 기술적 요소가 세 가지 있어. **재난 영향 지역을 어떤 공간 데이터로 표시할지, 실제 통행 가능성을 어떻게 확인할지, 119·보호자 연락 기능을 어디까지 연동할지**야. 이 부분은 UI만으로 해결할 수 없으므로 개발 요구사항에서 별도로 검토해야 해.

내 판단으로는 지금 제안한 화면 구조를 기본안으로 잡아도 괜찮아. 특히 **평상시 프로필에 저장된 정보가 재난 발생 후 AI 대화에서 재확인되고, 그 결과가 서로 다른 추천으로 이어지는 연결**을 명확하게 구현하는 것이 이번 해커톤에서 가장 중요한 부분이야.
`````

<a id="m053"></a>
## M053 · 사용자 — GPS 알림·대화 상태 갱신

원문 메시지 ID: `0c2899ee-59a1-4cdd-83d0-369007407e57`

`````text
[이미지 첨부: image_asset_pointer; sediment://file_000000008d1c8209a7e5c03871b8b592?shared_conversation_id=6ae4872b-c438-83ee-940c-d2385795e0c1]
응 조회 범위는 그냥 주변 소식 확인하는 용이라서 긴급 재난 알림 범위는 gps를 통해 나를 중심으로 할 거야 
그리고 단계별로 ai가 확인한 현재상황 이런거 일일히 안보여줘도 될 것 같아 일단 3. 재난 발생 시 전용 화면은 첫화면으로 넣고 (홍수 대피 명령 있는 화면)거기서 ai 에게 말하기라는 언어보다는 여기서는 ai라는 단어는 빼는게 좋을 것같아 아직은 ai 에 불신이 있을 수 있으니 피난로 찾기? 이런식의로 언어를 쓰는게 좋을 것 같아 그리고 거기서 화면이 넘어가면 내가 올려준 사진처럼 ai가 말할때 저 비선형의 뭔가가 움직이면서 밑에는 대화가 스크립트로 올라가면서 글로도 볼 수 있으면 좋을 것 같아. 근데 모든 대화가 뜨는게 아니라 계속 대화하다보면 위로 올라가면서 최신대화를 계속 볼 수 있는 식으로 그리고 밑에 네모칸은 계속 대화로 갱신된 내 상태를 보여주는거지 예를들어 처음에는 프로필에 넣어둔 상태가 표시되는거고 만약 독립보행가능이라고 써뒀으면 그 상태가 떠있는데 대화하면서 걷기 힘들어 이러면 그때 ai가 판단해서 독립보행가능 빠지고 걷기 힘듬의 상태가 갱신 되는거지 그리고 마지막에는 "상태에 따른 대피로를 안내해드릴 까요?" 이렇게 떠서 해달라고 하면 3d 대피로를 안내해주든 아니면 다른 방법을 알려주든 하는 화면으로 넘어가는거지 그리고 ai가 마지막을 판단못할수있ㄹ으니까 중간에 대피로안내해줘라던가 뭘 알려달라는식의 말을해도 다음 화면으로 넘어가는식으로
`````

<a id="m054"></a>
## M054 · 답변 — GPS 알림·대화 상태 갱신

원문 메시지 ID: `49a05e0a-02bf-467d-a4df-29745af4670c`

`````text
이렇게 구성하면 **별도의 'AI 분석 결과 화면' 없이 음성 대화 하나로 상황 파악부터 맞춤형 대피 안내까지 연결**할 수 있어.

올려준 스케치에서 중요한 건 세 가지야.

1. **상단:** 음성에 반응하는 움직이는 파형과 실시간 대화 스크립트
2. **하단:** 대화하면서 계속 갱신되는 내 현재 상태
3. **대화 결과:** 상황에 맞는 대피 방법을 안내하되, 사용자가 도중에 요청해도 즉시 다음 단계로 진행

이 구조를 기준으로 기존 화면 설계를 수정해보자.

## 1. 수정된 전체 화면 흐름

<box border radius="xl" padding={3} gap={2}>
  <box background="surface-secondary" radius="lg" padding={3} align="center" gap={1}>
    **① 평상시 홈**
    <text color="secondary" size="xs">설정 반경 내 지역 재난·안전 소식</text>
  </box>
  <row justify="center">
    <icon name="arrow-down" color="tertiary"/>
  </row>
  <box border radius="lg" padding={3} align="center" gap={1}>
    **② 재난 발생 전용 화면**
    <text color="secondary" size="xs">재난 종류 · 영향 지역 지도 · 공식 대피 지시</text>
    <badge color="secondary">내 상황에 맞는 대피 안내 받기</badge>
  </box>
  <row justify="center">
    <icon name="arrow-down" color="tertiary"/>
  </row>
  <box border radius="lg" padding={3} align="center" gap={1}>
    **③ 음성 대화 및 실시간 상태 갱신**
    <text color="secondary" size="xs">음성 파형 · 스크립트 · 내 상태 요약</text>
    <text color="secondary" size="xs">대화 중 언제든 대피 안내 요청 가능</text>
  </box>
  <row justify="center">
    <icon name="git-branch" color="tertiary"/>
  </row>
  <grid columns={2} gap={2}>
    <grid-item>
      <box background="surface-secondary" radius="lg" padding={3} gap={1} align="center" height="100%">
        **④-A 대피경로 안내**
        <text size="xs" color="secondary" textAlign="center">3D 지도와 음성 안내</text>
      </box>
    </grid-item>
    <grid-item>
      <box background="surface-secondary" radius="lg" padding={3} gap={1} align="center" height="100%">
        **④-B 긴급 지원**
        <text size="xs" color="secondary" textAlign="center">119 전화 · 보호자 연락</text>
      </box>
    </grid-item>
  </grid>
</box>

프로필 화면은 평상시 홈에서 접근하는 별도 설정 화면으로 두면 돼.

## 2. 재난 발생 전용 화면의 버튼 문구

네 의견처럼 첫 화면에서는 'AI에게 말하기'보다 **서비스가 실제로 무엇을 해주는지 알려주는 문구**가 적합해.

다만 '피난로 찾기'라고 하면 혼자 이동할 수 없는 사람에게도 경로를 제공하는 서비스처럼 보일 수 있어.

| 문구 | 평가 |
|---|---|
| AI에게 말하기 | 기술 중심. 사용자 목적이 불명확 |
| 피난로 찾기 | 직관적이지만 경로 안내에만 한정 |
| 내 상황 알려주기 | 대화 시작의 의미는 명확 |
| **내 상황에 맞는 대피 안내** | 개인별 대피 방법·지원 안내까지 포괄 |
| 대피 도움받기 | 가장 간단하지만 기능 설명이 다소 넓음 |

나는 메인 버튼을 **'내 상황에 맞는 대피 안내 받기'**로 추천해.

상황이 급박하므로 그 아래에 '119 긴급전화'를 별도로 두고, AI 대화를 거치지 않아도 바로 전화할 수 있게 하는 편이 좋아.

## 3. 음성 대화 화면 구체화

네 손그림을 바탕으로 화면을 나누면 이렇게 돼.

<box border radius="2xl" padding={3} gap={3} maxWidth="390px">
  <row align="center" justify="between">
    <row align="center" gap={2}>
      <icon name="arrow-left"/>
      **대피 안내**
    </row>
    <box background="rgba(185,62,44,0.10)" radius="full" padding={{x:3,y:1}}>
      <text color="danger" weight="medium" size="xs">홍수 대피 명령</text>
    </box>
  </row>
  <box align="center" gap={2} padding={{top:3,bottom:2}}>
    <text size="sm" color="secondary">음성 안내 중</text>
    <svg viewBox="0 0 320 112" width="100%" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="voiceg" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0" stopColor="#3C909E"/>
          <stop offset="0.5" stopColor="#4B78BB"/>
          <stop offset="1" stopColor="#9C72C5"/>
        </linearGradient>
      </defs>
      {#each Array.from({length:55},(_,i)=>i) as i}
        <rect x={11+i*5.5} y={56-(6+Math.pow(Math.sin(i*.43)*Math.cos(i*.17),2)*37+Math.abs(Math.sin(i*.19))*11)/2} width="3.5" height={6+Math.pow(Math.sin(i*.43)*Math.cos(i*.17),2)*37+Math.abs(Math.sin(i*.19))*11} rx="2" fill="url(#voiceg)" opacity={.55+Math.abs(Math.sin(i*.23))*.45}/>
      {/each}
    </svg>
    <caption>실제 구현에서는 말하는 동안 파형이 움직이고, 대기 중에는 작게 표시</caption>
  </box>
  <divider color="subtle"/>
  <box gap={3} minHeight="142px">
    <box align="start" gap={1}>
      <text size="xs" color="secondary">안내 음성</text>
      **현재 혼자 이동하실 수 있으신가요?**
    </box>
    <box align="end" gap={1}>
      <text size="xs" color="secondary">나</text>
      <box background="surface-secondary" radius="lg" padding={3}>
        지금은 다리가 아파서 오래 걷기 힘들어.
      </box>
    </box>
    <box align="start" gap={1}>
      <text size="xs" color="secondary">안내 음성</text>
      오래 걷기 어려우시군요. 계단은 이용하실 수 있으신가요?
    </box>
  </box>
  <divider color="subtle"/>
  <box gap={2}>
    <row justify="between" align="center">
      **현재 확인된 내 상태**
      <icon name="refresh-cw" color="secondary" size="sm"/>
    </row>
    <row wrap="wrap" gap={2}>
      <badge color="secondary">1인 가구</badge>
      <badge color="secondary">장거리 보행 어려움</badge>
      <badge color="secondary">계단 이용 확인 필요</badge>
    </row>
    <text size="xs" color="secondary">대화를 통해 갱신되는 정보 · 잘못 인식했다면 수정 가능</text>
  </box>
  <spacer/>
  <box background="surface-secondary" radius="lg" padding={3} gap={2} align="center">
    <row align="center" gap={2}>
      <icon name="mic" size="lg"/>
      **말씀해 주세요**
    </row>
    <text color="secondary" size="xs">듣는 중 · 직접 입력도 가능</text>
  </box>
  <row gap={2}>
    <box flex="1" border radius="lg" padding={3} align="center">
      <text weight="medium" size="sm">대피 방법 보기</text>
    </box>
    <box flex="1" border radius="lg" padding={3} align="center">
      <row align="center" gap={1}>
        <icon name="phone" color="danger" size="sm"/>
        <text weight="medium" size="sm">119 전화</text>
      </row>
    </box>
  </row>
</box>
<caption>개발용 정적 화면 예시. 음성 파형과 대화는 실제로 작동하는 상태가 아니야.</caption>

이 화면에서 대화 스크립트는 최신 대화가 아래에 나타나고, 이전 대화는 위로 밀려 올라가도록 하면 돼. 화면에 보이는 건 최근 2~3개 발화 정도로 제한하고, 이전 대화가 필요하면 위로 스크롤해서 확인하는 구조가 적합해.

반면 **내 상태 박스는 스크롤하지 않고 하단에 고정**하는 편이 좋아. 그래야 대화하면서 정보가 어떻게 바뀌는지 계속 확인할 수 있어.

## 4. 상태 갱신은 이렇게 처리하면 돼

{@body const [stage,setStage] = DIL.useState("initial")}
<box border radius="xl" padding={3} gap={3}>
  **대화에 따른 상태 변경 예시**
  <segmented-control block size="md" value={stage} onChange={setStage} options={[{label:"대화 전",value:"initial"},{label:"대화 중",value:"updated"},{label:"추가 확인",value:"confirmed"}]}/>
  <box background="surface-secondary" radius="lg" padding={3} gap={2}>
    <text color="secondary" size="xs">대화 스크립트</text>
    {#if stage==="initial"}
      **안내 음성:** 평소에는 혼자 걸으실 수 있다고 등록되어 있습니다. 지금도 이동할 수 있으신가요?
    {:else if stage==="updated"}
      **나:** 지금은 다리가 아파서 오래 걷기 힘들어.

      **안내 음성:** 오래 걷기 어려우시군요. 계단은 이용하실 수 있나요?
    {:else}
      **나:** 계단은 괜찮은데 오래 못 걸어.

      **안내 음성:** 알겠습니다. 이동거리를 고려해 대피 방법을 확인하겠습니다.
    {/if}
  </box>
  <box border radius="lg" padding={3} gap={2}>
    **현재 내 상태**
    <row wrap="wrap" gap={2}>
      <badge>1인 가구</badge>
      {#if stage==="initial"}
        <badge>독립 보행 가능</badge>
        <badge>계단 이용 가능</badge>
      {:else if stage==="updated"}
        <badge color="warning">장거리 보행 어려움</badge>
        <badge>계단 이용 확인 필요</badge>
      {:else}
        <badge color="warning">장거리 보행 어려움</badge>
        <badge>계단 이용 가능</badge>
      {/if}
    </row>
  </box>
  <caption>단계 전환은 동작 원리를 보여주는 예시. 실제 구현에서는 음성 인식 결과와 사용자 확인을 반영해 변경</caption>
</box>

중요한 건 이전 프로필과 현재 상태가 다를 때, **이전 정보보다 현재 확인된 상태를 우선 적용한다는 것**이야.

다만 "걷기 힘들다"는 말만으로 '보행 불가능'이라고 판단해서는 안 돼. 장거리 보행이 힘든지, 아예 움직일 수 없는지, 도움이 필요한지 구분해야 하니까.

안전에 큰 영향을 주는 정보는 짧은 추가 질문으로 확인하되, 그 과정 때문에 긴급 연락이 지연되어서는 안 돼.

## 5. 대화가 끝나기 전에도 다음 화면으로 넘어갈 수 있어야 해

여기서는 **AI의 대화 완료 판단**과 **사용자의 직접 요청**을 별개로 처리하는 게 맞아.

| 발생 상황 | 화면 동작 |
|---|---|
| AI가 필요한 정보를 확보함 | "현재 상황에 맞는 대피 방법을 안내해 드릴까요?" |
| 사용자가 "대피로 알려줘"라고 말함 | 지금까지 확인된 정보로 경로를 조회 |
| 사용자가 "119에 연락해줘"라고 말함 | 즉시 긴급전화 연결 기능 안내 |
| 사용자가 "못 움직이겠어"라고 말함 | 이동 지원 필요 여부를 우선 확인하고 긴급 연락 제시 |
| 사용자가 "아까와 상황이 달라졌어"라고 말함 | 현재 상태 갱신 후 기존 추천 재검토 |
| 확인 가능한 경로가 없음 | 임의의 경로 생성 없이 공식 대피 지침 및 긴급 지원 안내 |

핵심은 **대화가 충분히 진행되기를 기다리게 하지 않는 것**이야.

사용자가 중간에 직접 요청하면 다음 단계로 진행하되, 경로의 안전성과 대피 가능성을 판단하는 데 필요한 정보가 부족하면 그 사실을 알려야 해.

마지막 안내 문구 역시 상황에 따라 달라지는 편이 자연스러워.

- 이동 가능하고 검증된 경로가 있을 때: **"현재 상황에 맞는 대피경로를 안내해 드릴까요?"**
- 혼자 이동하기 어려울 때: **"이동에 도움이 필요하신 것 같습니다. 긴급 지원을 요청하시겠어요?"**
- 경로 통행 여부를 확인하지 못했을 때: **"현재 이동 가능한 경로를 확인하지 못했습니다. 공식 대피 지침과 도움 요청 방법을 안내하겠습니다."**

그리고 119 신고는 실제 연동 없이 'AI가 대신 신고했다'고 안내하면 안 돼. 해커톤 MVP에서는 사용자가 직접 연결하는 전화 기능과 모의 신고 절차를 구분해야 해.

## 6. 이제 화면별 역할은 이렇게 정리하면 되겠어

| 화면 | 내용 | 진입 조건 |
|---|---|---|
| 평상시 홈 | 설정 반경의 주변 재난·안전 소식 | 일반 상태 |
| 내 프로필 | 평상시 이동 상태, 거주 형태, 연락처 | 사용자가 설정 |
| 재난 알림 | 재난 종류, 내 위치·영향 지역, 공식 지시, 대피 안내 시작 | 해당 지역의 공식 대피 지시 등 |
| 음성 대화 | 반응형 파형, 스크립트, 갱신되는 상태 박스 | 사용자가 안내 요청 |
| 3D 대피경로 | 검증된 이동 경로, 안내 음성, 상황 변경 | 이용 가능한 경로가 확인된 경우 |
| 긴급 지원 | 119 전화, 보호자 연락 등 | 사용자 요청 또는 지원 필요 확인 |

별도의 'AI 분석 중', '프로필 분석 결과', '대피 추천 분석 결과' 페이지는 만들 필요 없어. **음성 대화 화면 안에서 상태를 갱신하고, 결과가 정해졌을 때 필요한 화면으로 넘어가는 구조**면 충분해.

그리고 해커톤 시연 영상에서는 같은 홍수 상황에서 사용자 A는 대화 후 3D 경로 화면으로, 사용자 B는 이동이 어렵다고 말해 긴급 지원 화면으로 넘어가는 장면을 비교하면 돼.

현재까지의 설계에서 내가 추가로 제안한 것은 **음성 대화 중에도 항상 누를 수 있는 '대피 방법 보기'와 '119 전화' 버튼**이야. 이용자가 음성 인식에 의존하지 않고도 다음 행동을 선택할 수 있도록 하기 위한 것이고, 네가 원하는 대화 중심 UI는 그대로 유지할 수 있어.
`````

<a id="m055"></a>
## M055 · 사용자 — 원형 음성 UI·자동 인식·끼어들기

원문 메시지 ID: `25985c26-a444-4916-b468-138e20c01f70`

`````text
[이미지 첨부: image_asset_pointer; sediment://file_00000000c5308211a8633dd6f770c837?shared_conversation_id=6ae4872b-c438-83ee-940c-d2385795e0c1]
좀더 화면 비율상 음성 인식하고있다는듯한 시리처럼 움직임이 있는 원형 모형? 같은게 있고 그 아래 가운데 정렬로 "" 안에는 ai 말 그아래 박스안에 유저 말 뜨는게 좋을것같고 그 ai 시리같은 원형과 대화스크립트가 2/3를 차지하면 좋겠어 그리고 그아래 말씀해주세요는 따로 없이 지피티한테 대화하듯 지피티는 말하는중간에 말걸어도 인식하잖아 이미 여기 화면들어온순간 음성인식 알아서 하게
`````

<a id="m056"></a>
## M056 · 답변 — 원형 음성 UI·자동 인식·끼어들기

원문 메시지 ID: `f408bdf6-dd00-4ee6-bc34-1c0009151156`

`````text
그럼 음성 대화 화면은 **채팅 앱 형태가 아니라, 시리(Siri)처럼 음성 대화가 중심인 화면**으로 설계하는 게 맞겠어.

올려준 스케치를 기준으로 상단 약 2/3는 움직이는 원형 음성 인터페이스와 대화 스크립트, 하단 약 1/3은 대화를 통해 갱신되는 현재 상태와 행동 버튼으로 구성하자.

## 1. 수정한 음성 대피 안내 화면

<AppBlock title="음성 대피 안내 모바일 화면 시안" icon="app-chatgpt" variant="inline">
<div id="evac-voice-preview" class="w-full flex justify-center p-2">
  <style>
    #evac-voice-preview .phone{width:min(100%,365px);height:665px;border:1px solid var(--viz-border);border-radius:25px;background:var(--viz-card);overflow:hidden;display:flex;flex-direction:column;color:var(--viz-text);font-family:inherit;box-shadow:0 8px 28px #0000000D}
    #evac-voice-preview .top{height:67%;display:flex;flex-direction:column;border-bottom:1px solid var(--viz-border);padding:18px 19px 10px}
    #evac-voice-preview .head{display:flex;align-items:center;justify-content:space-between;font-size:14px;font-weight:700}
    #evac-voice-preview .danger{background:#FCE8E5;color:#AE382E;padding:7px 9px;border-radius:7px;font-size:11px;font-weight:700}
    #evac-voice-preview .speaker{display:flex;flex:1;min-height:0;flex-direction:column;align-items:center;justify-content:center;gap:20px}
    #evac-voice-preview .orbit{width:171px;height:171px;position:relative;display:grid;place-items:center;isolation:isolate}
    #evac-voice-preview .halo{position:absolute;inset:13px;border-radius:45% 55% 60% 40%;background:conic-gradient(from 45deg,#6ED5B3,#4B9EAB,#617FCB,#B0A2DE,#6ED5B3);filter:blur(12px);opacity:.55;animation:evac-spin 9s linear infinite}
    #evac-voice-preview .blob{position:absolute;inset:22px;border-radius:43% 57% 56% 44%/52% 43% 57% 48%;background:radial-gradient(circle at 30% 24%,#C5F6E9 0%,#6DCCCA 26%,#547FCE 65%,#857FD5 100%);box-shadow:inset -9px -12px 27px #253D9250,0 8px 25px #6285CC3B;animation:evac-morph 4.2s ease-in-out infinite alternate}
    #evac-voice-preview .shine{position:absolute;width:55px;height:43px;border-radius:50%;background:#FFFFFF68;filter:blur(18px);transform:translate(-20px,-23px)}
    #evac-voice-preview .question{font-size:19px;line-height:1.5;text-align:center;font-weight:720;max-width:305px;letter-spacing:-.4px}
    #evac-voice-preview .reply{width:100%;border:1px solid var(--viz-border);border-radius:12px;padding:12px 15px;background:var(--viz-panel);font-size:14px;line-height:1.6;min-height:75px;display:flex;flex-direction:column;justify-content:center;gap:3px}
    #evac-voice-preview .speaker-label{font-size:11px;color:var(--viz-muted)}
    #evac-voice-preview .bottom{flex:1;padding:16px 17px;display:flex;flex-direction:column;gap:10px;min-height:0}
    #evac-voice-preview .status{display:flex;justify-content:space-between;align-items:center;font-size:14px;font-weight:750}
    #evac-voice-preview .statebox{border:1px solid var(--viz-border);border-radius:12px;padding:12px;display:flex;gap:6px;flex-wrap:wrap}
    #evac-voice-preview .chip{background:var(--viz-panel);color:var(--viz-text);font-size:12px;font-weight:600;padding:7px 9px;border-radius:7px}
    #evac-voice-preview .chip.new{background:#FEF1DB;color:#8F5610}
    #evac-voice-preview .actions{margin-top:auto;display:grid;grid-template-columns:1.1fr 1fr;gap:9px}
    #evac-voice-preview .action{padding:13px 4px;text-align:center;border-radius:9px;font-size:14px;font-weight:750;border:1px solid var(--viz-border)}
    #evac-voice-preview .action.primary{background:#245F55;color:white;border-color:#245F55}
    #evac-voice-preview .action.sos{border-color:#E9A29D;color:#B23B32}
    #evac-voice-preview .mic-indicator{font-size:11px;color:#378F77;display:flex;align-items:center;gap:5px}
    #evac-voice-preview .mic-dot{height:6px;width:6px;border-radius:50%;background:#35A889;animation:evac-pulse 1.5s ease-in-out infinite}
    @keyframes evac-spin{to{transform:rotate(360deg)}}
    @keyframes evac-morph{0%{transform:scale(.96) rotate(-9deg);border-radius:43% 57% 56% 44%/52% 43% 57% 48%}100%{transform:scale(1.05) rotate(12deg);border-radius:59% 41% 44% 56%/39% 55% 45% 61%}}
    @keyframes evac-pulse{50%{opacity:.3}}
    @media(prefers-reduced-motion:reduce){#evac-voice-preview .halo,#evac-voice-preview .blob,#evac-voice-preview .mic-dot{animation:none}}
  </style>
  <div class="phone">
    <div class="top">
      <div class="head"><span>‹ &nbsp;대피 안내</span><span class="danger">홍수 대피 명령</span></div>
      <div class="speaker">
        <div class="orbit" aria-label="움직이는 원형 음성 인터페이스">
          <div class="halo"></div><div class="blob"></div><div class="shine"></div>
        </div>
        <div class="question">“계단은 이용하실 수 있나요?”</div>
        <div class="reply"><span class="speaker-label">나</span><span>지금은 다리가 아파서 오래 걷기 힘들어.</span></div>
        <div class="mic-indicator"><span class="mic-dot"></span>음성 인식 중</div>
      </div>
    </div>
    <div class="bottom">
      <div class="status"><span>현재 내 상태</span><span style="font-size:12px;color:var(--viz-muted);font-weight:500">수정 ✎</span></div>
      <div class="statebox">
        <span class="chip">1인 가구</span>
        <span class="chip new">장거리 보행 어려움</span>
        <span class="chip">계단 이용 확인 중</span>
      </div>
      <div class="actions"><div class="action primary">대피 방법 보기</div><div class="action sos">☎ 119 전화</div></div>
    </div>
  </div>
</div>
</AppBlock>

<caption>화면 비율과 원형 모션을 보여주는 시각적 시안이야. 실제 음성 인식·전화·대피경로 기능이 연결된 화면은 아니며 색상도 임시로 사용했어.</caption>

## 2. 원형 애니메이션과 대화는 이렇게 작동하면 돼

| 상태 | 원형 애니메이션 | 대화 스크립트 |
|---|---|---|
| 안내 음성이 말하는 중 | 물결치듯 크게 움직임 | AI가 말하는 문장이 중앙에 표시 |
| 사용자가 말하는 중 | 사용자 목소리에 반응 | 하단 박스에 인식된 사용자 발화 표시 |
| 다음 응답을 준비하는 중 | 느리게 움직임 | 직전 대화 유지 |
| 음성 대화가 일시 중지됨 | 움직임 감소 또는 정지 | 기존 스크립트 유지 |

대화가 계속 이어지면 이전 문장은 위로 올라가면서 사라지고, **최신 AI 문장과 사용자의 최근 발화가 중앙에 유지**되는 방식이야. 필요하면 이전 대화를 위로 스크롤해서 볼 수 있도록 할 수도 있어.

## 3. 음성 대화 방식도 변경

네가 말한 대로 별도의 '말씀해 주세요' 버튼이나 음성 녹음 버튼은 두지 않는 방향이야.

음성 대화 화면에 진입하면 마이크 권한이 허용되어 있는 경우 자동으로 대화가 시작되고, 사용자는 별도로 버튼을 누를 필요가 없어.

특히 필요한 것은 **Barge-in(발화 중 끼어들기)** 기능이야.

예를 들면 AI가 "현재 상태를 기준으로 대피 경로를…"이라고 말하고 있을 때 사용자가 "아니, 지금 못 움직이겠어"라고 하면 AI 음성 출력을 중단하고 사용자의 말을 우선 인식하는 방식이지.

이 기능을 구현하려면 단순한 음성 인식·합성 연결만으로는 부족하고, 실시간 음성 입력, 발화 감지, AI 음성 출력 중단, 스피커 소리의 재인식 방지 등을 처리해야 해.

다만 화면에 마이크 버튼이 없어도 **마이크 작동 상태는 작게 표시하고 끌 수 있는 수단은 제공해야 해.** 최초 이용 시 마이크 권한을 받아야 한다는 점도 고려해야 하고.

## 4. 내 상태 박스의 갱신 규칙

이 부분은 기존 프로필과 재난 당시 상태를 분리하는 것이 중요해.

<box border radius="lg" padding={3} gap={2}>
  **대화 전 — 저장된 기본 프로필**
  <row gap={2} wrap="wrap">
    <badge>1인 가구</badge>
    <badge>독립 보행 가능</badge>
  </row>
  <row align="center" justify="center">
    <icon name="arrow-down" color="tertiary"/>
  </row>
  **대화 중 — 현재 상황 반영**
  <box background="surface-secondary" radius="lg" padding={3}>
    "지금은 다리가 아파서 오래 걷기 힘들어."
  </box>
  <row align="center" justify="center">
    <icon name="arrow-down" color="tertiary"/>
  </row>
  **갱신된 현재 상태**
  <row gap={2} wrap="wrap">
    <badge>1인 가구</badge>
    <badge color="warning">장거리 보행 어려움</badge>
    <badge>계단 이용 확인 필요</badge>
  </row>
</box>

기존 '독립 보행 가능'이라는 표시를 그대로 두기보다, 현재 이동에 제약이 생겼다는 사실이 보이도록 갱신하는 거야.

단, "걷기 힘들다"를 "전혀 걸을 수 없다"로 해석하면 안 되므로, 필요한 경우 짧게 추가 확인해야 해. 그리고 재난 중에 갱신한 일시적인 상태가 평상시 기본 프로필을 영구적으로 덮어쓰지 않도록 분리하는 것이 좋아.

## 5. 대화 종료와 화면 전환

AI가 필요한 조건을 확인하면 다음처럼 안내하면 돼.

"현재 상황에 맞는 대피 방법을 안내해 드릴까요?"

사용자가 동의하면 검증된 경로가 있는 경우 3D 대피로로, 혼자 이동하기 어려운 경우 긴급 지원 안내로 이동해.

그런데 네가 지적한 것처럼 AI가 대화를 끝내지 않거나 질문을 계속할 수도 있지. 그래서 하단의 **'대피 방법 보기' 버튼은 언제든 사용할 수 있도록** 유지하는 게 적절해.

사용자가 대화 도중 "지금 대피로 알려줘", "119에 전화해 줘"라고 말하는 경우에도 해당 요청을 먼저 처리해야 해. 단, 대피로 안전성을 확인하지 못했다면 임의로 경로를 생성해 보여주지 않는 것이 원칙이야.

---

### 현재까지 반영한 화면 설계

- 상단 약 2/3: 원형 음성 애니메이션 + 중앙 AI 발화 + 하단 사용자 발화
- 하단 약 1/3: 실시간 갱신되는 내 상태 + 대피 방법 보기 + 119 전화
- 화면 진입 후 별도 녹음 버튼 없이 음성 대화 시작
- AI가 말하는 중에도 사용자 발화 인식
- 최신 대화 중심으로 스크립트 자동 갱신
- 상황이 바뀌면 상태 박스를 갱신하고 대피 추천 재평가
- 대화 중 언제든 음성 명령이나 버튼으로 다음 화면 진입 가능

**이 구조에서는 별도의 대화 완료 버튼이나 AI 분석 결과 화면이 필요하지 않아.** 중앙은 자연스러운 음성 대화에 집중하고, 하단 상태 박스만 갱신하면서 개인화 추천이 이루어지는 과정을 보여주면 돼.

해커톤 시연에서도 동일한 재난을 두고 사용자 발화가 달라지면 하단 상태와 최종 대피 방법이 달라지는 장면을 직접 비교할 수 있어.

---

If you want, I can:

- 계속해서 재난 알림 단계별 동작 구조 설명 이어가기
- AI 음성 대화 기능 상세 설계 예시 제공하기
- 대피 경로 3D 안내 기능 UX 흐름 구상 계속하기
`````
