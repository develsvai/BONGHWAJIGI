# 대화 원문 02 — 청년 경험·아동 서비스

[문서 안내](../README.md) · [출처 및 보존 범위](../source-and-coverage.md)

원문의 텍스트를 그대로 보존합니다. 답변의 UI 표현 태그·코드·조건식도 텍스트 블록 안에 포함했습니다. 제안, 통계, 외부 서비스 설명은 당시 대화 내용이며 이번 작업에서 사실 재검증한 결과가 아닙니다.

<a id="m009"></a>
## M009 · 사용자 — 취업 공백 청년 지원

원문 메시지 ID: `c02b3c9d-468f-443d-a1f4-71008f79c52d`

`````text
당신은 가치가 있습니다. 취직을 못하고 오랫동안 실의에 빠져있는 젊은이타겟의 뭔가 없을까
`````

<a id="m010"></a>
## M010 · 답변 — 취업 공백 청년 지원

원문 메시지 ID: `6190d00b-9cd8-4898-bdfb-bfc3bc2dd272`

`````text
**“당신은 가치가 있습니다.”**

이 문장을 중심으로, 오랫동안 취업하지 못해 자신감을 잃은 청년들을 위한 서비스를 만들 수 있어. 그리고 AI 기반 추천 서비스라는 해커톤 주제와도 연결할 수 있어.

다만 나는 일반적인 취업 추천이나 AI 심리상담 서비스보다는 **취업 여부와 관계없이 자신의 존재와 가능성을 다시 인식하고, 사회와 연결될 기회를 제공하는 서비스**가 더 적합하다고 생각해.

## 1. 먼저 어떤 문제를 해결할 것인가?

장기 미취업 청년을 모두 같은 상태로 보면 안 돼.

| 겪을 수 있는 문제 | 일반적인 해결책 | 새로운 접근 |
|---|---|---|
| 반복적인 취업 실패 | 이력서 첨삭, 일자리 추천 | 취업 평가와 무관한 경험 제공 |
| 자신감 저하 | 긍정적 메시지, 상담 | 자신의 행동이 만든 실제 변화를 확인 |
| 사회적 고립 | 커뮤니티, 모임 추천 | 부담이 적은 사회적 연결부터 시작 |
| 경력 공백에 대한 부담 | 자격증, 직업훈련 추천 | 공백 기간에도 존재했던 경험을 발견 |
| 무엇부터 해야 할지 모름 | 목표 설정, 계획 추천 | 지금 감당할 수 있는 작은 선택지 제시 |

이 문제는 정책적으로도 이미 인식되고 있어. 고용노동부의 <Link url="https://www.moel.go.kr/policyitrd/policyItrdView.do?policy_itrd_sn=242" title="청년도전지원사업"/>은 구직단념 청년의 자신감 회복과 구직 의욕 향상을 지원하고, 서울시도 고립·은둔 청년을 위한 일상 회복·관계 형성 프로그램을 운영하고 있어. <Cite refs={["turn178632search4","turn926179search3"]}/>

따라서 단순히 '힘내라는 말을 해주는 AI'나 '청년에게 취업 프로그램을 추천하는 AI'로는 차별화가 약해.

**서비스가 실제로 어떤 경험을 만들어 주느냐**가 중요해.

## 2. 발전시켜 볼 만한 세 가지 서비스

<box gap={4}>
  <row align="start" gap={3}>
    <box background="surface-secondary" radius="lg" padding={3}>
      <icon name="hand-heart" size="xl"/>
    </box>
    <box flex="1" gap={1}>
      <title size="lg">A. 당신을 필요로 하는 순간</title>
      <text color="secondary" size="xs" weight="medium">AI 기반 사회적 기여 기회 추천</text>
      취업할 회사를 추천하는 대신, 지금 이 사람의 작은 도움이 필요한 상황을 찾아주는 서비스.

      **예시:** "컴퓨터를 조금 다룰 수 있어요. 하지만 사람을 직접 만나는 건 부담스러워요."

      AI는 비대면으로 참여할 수 있는 작은 활동을 추천해. 실제 도움을 받은 사람이 감사 메시지를 남기면 이를 전달하지.

      핵심은 AI가 "넌 대단해"라고 칭찬하는 게 아니라, 실제로 자신이 다른 사람에게 도움이 된 경험을 만드는 거야.
    </box>
  </row>
  <divider color="subtle"/>
  <row align="start" gap={3}>
    <box background="surface-secondary" radius="lg" padding={3}>
      <icon name="footprints" size="xl"/>
    </box>
    <box flex="1" gap={1}>
      <title size="lg">B. 세상으로 돌아가는 가장 작은 문</title>
      <text color="secondary" size="xs" weight="medium">AI 기반 사회적 연결 단계 추천</text>
      사람마다 외부 활동에 대한 부담이 다르다는 점에 집중해.

      **예시:** "취업 준비도 지겹고 사람을 만나기도 싫지만 집에만 있기는 답답해요."

      AI가 바로 취업 박람회나 모임에 나가라고 권하는 대신, 혼자 갈 수 있는 전시, 비대면 공동 활동, 소규모 모임처럼 사용자가 선택한 부담 수준에 맞는 기회를 추천해.

      중요한 것은 다음 단계로 진행해야만 성공하는 서비스로 만들지 않는 거야.
    </box>
  </row>
  <divider color="subtle"/>
  <row align="start" gap={3}>
    <box background="surface-secondary" radius="lg" padding={3}>
      <icon name="book-heart" size="xl"/>
    </box>
    <box flex="1" gap={1}>
      <title size="lg">C. 공백이 아니라, 내 이야기</title>
      <text color="secondary" size="xs" weight="medium">AI 기반 경험 재발견 및 활동 추천</text>
      이력서에 적지 못하는 시간도 그 사람의 삶이라는 관점이야.

      **예시:** "취업 준비한 3년 동안 아무것도 한 게 없는 것 같아요."

      AI가 사용자의 실제 기록을 바탕으로 취미, 관심사, 배운 것, 어려움을 해결한 경험을 정리해. 이를 바탕으로 새롭게 시도할 만한 활동을 추천하지.

      없는 경력을 만들어 주는 게 아니라, 사용자가 잊고 있던 경험을 확인하도록 돕는 방식이야.
    </box>
  </row>
</box>

## 3. 내가 가장 발전 가능성이 높다고 보는 아이디어

<box border radius="xl" padding={3} gap={3}>
  <box gap={1}>
    <text color="secondary" weight="medium" size="xs">서비스 콘셉트</text>
    <title size="xl">증명하지 않아도</title>
    **당신은 가치가 있습니다.**

    <text color="secondary" size="sm">취업 성과나 사회적 지위로 자신을 증명하지 않아도, 원할 때 다시 세상과 연결될 수 있도록 돕는 AI 추천 서비스.</text>
  </box>
  <divider color="subtle"/>
  <text weight="medium" size="sm">사용자 경험 예시</text>
  <box background="surface-secondary" padding={3} radius="lg" gap={2}>
    <text color="secondary" size="xs">STEP 1 · 오늘의 상태를 직접 선택</text>
    {@body const [energy,setEnergy] = DIL.useState("low")}
    <radio-group direction="col" value={energy} onChange={setEnergy}>
      <radio value="low">오늘은 혼자 있고 싶어요</radio>
      <radio value="mid">누군가와 간단히 소통할 수 있어요</radio>
      <radio value="high">밖에 나가서 무언가 해보고 싶어요</radio>
    </radio-group>
    <divider color="subtle"/>
    <text color="secondary" size="xs">STEP 2 · 상태에 따라 달라지는 추천 예시</text>
    <box background="surface" radius="md" padding={3} gap={1}>
      {#if energy === "low"}
        **혼자서 참여하는 작은 활동**

        지역 문화시설의 안내문을 읽고 이해하기 어려운 부분을 제보하는 활동은 어때요? 다른 사람과 직접 대화할 필요는 없어요.
      {:else if energy === "mid"}
        **누군가와 연결되는 작은 활동**

        동네 행사에 방문하려는 사람의 간단한 질문에 온라인으로 답해주는 활동은 어때요? 원할 때만 참여할 수 있어요.
      {:else}
        **밖에서 경험하는 새로운 활동**

        지역 도서관의 소규모 행사 준비를 함께 해보는 건 어때요? 단시간 참여할 수 있는 활동부터 살펴볼 수 있어요.
      {/if}
    </box>
    <caption>실제 모집 정보가 아닌 서비스 동작을 설명하기 위한 예시야.</caption>
  </box>
  <box gap={2}>
    <text color="secondary" size="xs">STEP 3 · 실제 연결의 결과</text>
    <box border radius="lg" padding={3} gap={2}>
      <row align="center" gap={2}>
        <icon name="message-square-heart" color="secondary"/>
        **상대방이 직접 남긴 메시지**
      </row>
      <text italic>“안내문에서 헷갈리는 부분을 알려주셔서 수정하는 데 도움이 됐어요. 감사합니다.”</text>
      <caption>실제 이용자의 피드백이 있을 때에만 표시. AI가 만들어낸 감사 인사는 사용하지 않음.</caption>
    </box>
  </box>
</box>

이 서비스는 AI가 사람의 가치를 점수로 매기지 않아. 사용자가 선택한 관심사와 참여 부담 수준을 바탕으로, 실제로 참여할 수 있는 기회를 찾아주는 역할만 해.

## 4. 참신성은 어디에서 나오는가?

완전히 새로운 서비스 분야는 아니야. 예를 들어 영국의 <Link url="https://www.goodgym.org/missions" title="GoodGym"/>은 지역의 도움이 필요한 사람과 봉사자를 연결하고 있어. <Cite ref="turn926179search0"/>

그래서 단순한 봉사활동 추천으로 구현하면 기존 플랫폼과 크게 다르지 않을 수 있어.

차별화하려면 다음 조건들이 중요해.

| 기존 방식 | 제안하는 방식 |
|---|---|
| 참여할 수 있는 활동을 검색 | 오늘 감당 가능한 부담에 맞춰 추천 |
| 경력과 기술 중심 매칭 | 관심사와 참여 방식 중심 매칭 |
| 활동 실적과 봉사시간 누적 | 사용자가 원할 때 실제 경험과 피드백 확인 |
| 사회적 활동 참여를 목표로 설정 | 참여하지 않을 자유까지 보장 |
| 구직 의욕 회복에 집중 | 취업과 무관한 사회적 연결도 인정 |

해커톤에서의 MVP는 **사용자 선택 → AI 활동 추천 → 추천 이유 설명 → 활동 참여 → 실제 피드백 표시** 정도로 제한할 수 있어. 실제 제휴기관이나 활동 데이터가 없다면 시연용 가상 데이터를 사용했다는 사실도 분명히 밝혀야 하고.

정보보호와 연결한다면 취업 여부, 실명, 경력 공백을 상대방에게 공개하지 않고도 활동에 참여하도록 하는 구조를 추가할 수 있지만, 이 경우에도 핵심 출품 분야는 AI 추천이 더 자연스러워.

## 5. 기획에서 주의해야 할 점

이 타깃에게는 서비스가 오히려 새로운 부담이 되지 않도록 해야 해.

- **활동하지 못해도 실패가 아님.** 연속 참여 일수, 기여 점수, 순위 경쟁은 배제하는 편이 적합해.
- **가치와 기여를 동일시하지 않음.** 다른 사람에게 도움이 되어야만 가치 있는 존재라는 메시지가 되어서는 안 돼.
- **취약한 상황을 이용하지 않음.** 무급 노동을 유도하거나, 개인정보를 과도하게 수집하거나, 검증되지 않은 일대일 만남을 추천하지 않도록 설계해야 해.
- **효과를 과장하지 않음.** 이 서비스가 자신감이나 우울감을 개선한다는 주장은 실제 이용자 검증 없이 할 수 없어.

---

여기서 서비스 방향을 결정하는 핵심 질문이 하나 있어.

**네가 말한 "당신은 가치가 있습니다"는 어떤 의미에 더 가까워?**

{@body const [meaning,setMeaning] = DIL.useState("self")}
<box gap={2}>
  <radio-group direction="col" value={meaning} onChange={setMeaning}>
    <radio value="self">**① 자신의 가치를 다시 발견하기**

    <text color="secondary" size="sm">취업하지 못했다고 아무것도 아닌 사람이 된 것은 아니라는 걸 스스로 인식하도록 돕기</text></radio>
    <radio value="connection">**② 사회에서 자신의 자리를 다시 찾기**

    <text color="secondary" size="sm">누군가와 연결되고 실제 사회의 구성원으로 참여하는 경험 만들기</text></radio>
    <radio value="recover">**③ 다시 살아갈 의욕과 방향 찾기**

    <text color="secondary" size="sm">취업 압박에서 벗어나 좋아하는 것, 하고 싶은 것, 삶의 방향을 조금씩 찾아가기</text></radio>
  </radio-group>
  <button block onClick={()=>GenUI.issueNewTurn(({self:"'당신은 가치가 있습니다'라는 해커톤 아이디어를 자신의 가치를 다시 발견하도록 돕는 서비스로 발전시켜줘. 흔한 AI 상담이나 일기 앱과 다른 참신한 방식으로.",connection:"'당신은 가치가 있습니다'라는 해커톤 아이디어를 사회에서 자신의 자리를 다시 찾도록 돕는 서비스로 발전시켜줘. 흔한 봉사 매칭 플랫폼과 차별화해줘.",recover:"'당신은 가치가 있습니다'라는 해커톤 아이디어를 장기 미취업 청년이 취업 압박 없이 삶의 의욕과 방향을 다시 찾아가는 서비스로 발전시켜줘. 흔한 자기계발 서비스와 차별화해줘."})[meaning])}>이 방향으로 구체화하기</button>
</box>
`````

<a id="m011"></a>
## M011 · 사용자 — 공백이 아니라 내 이야기

원문 메시지 ID: `a2ec7e9c-3a76-4020-b10e-b52cc18d3227`

`````text
C. 공백이 아니라, 내 이야기 이게 괜찮은데
`````

<a id="m012"></a>
## M012 · 답변 — 공백이 아니라 내 이야기

원문 메시지 ID: `f4b9a83d-465c-464b-84ba-45c296280d19`

`````text
**C. 공백이 아니라, 내 이야기**는 해커톤 주제로 더 발전시켜 볼 만해.

특히 좋은 점은 **취업하지 못한 시간을 실패한 시간으로만 바라보는 관점을 바꾸는 것**이야.

다만 서비스를 단순히 'AI가 내 이야기를 듣고 좋은 말로 바꿔준다'는 형태로 만들면 흔한 AI 상담·일기 앱과 비슷해져.

나는 이 아이디어의 핵심을 이렇게 잡는 게 좋겠어.

> **이력서에는 공백으로 남은 시간에도, 그 사람의 삶에는 이야기가 있었다.**
>
> AI는 없었던 성과를 만들어내는 것이 아니라, 사용자가 지나쳐 온 실제 경험을 발견하고 정리하며 그 경험에서 출발할 수 있는 다음 선택지를 추천한다.

여기서 중요한 건 두 가지야.

- **과거를 다시 발견하는 기능:** '아무것도 하지 않았다'고 생각했던 기간을 실제 기록과 경험을 통해 돌아보기
- **미래를 추천하는 기능:** 발견한 관심사와 경험을 바탕으로, 취업 성과와 무관하게 새롭게 해볼 수 있는 일을 제안하기

이렇게 하면 단순 회고 앱이 아니라 해커톤 주제인 **AI 기반 추천 서비스**로 연결할 수 있어.

## 서비스는 이런 식으로 작동할 수 있어

<box border radius="xl" padding={3} gap={3}>
  <text color="secondary" weight="medium" size="xs">가상의 사용자 시나리오</text>
  <box background="surface-secondary" radius="lg" padding={3} gap={1}>
    **사용자**

    "졸업하고 2년 동안 취업 준비만 했어요. 이제는 제가 뭘 좋아하는지도 모르겠어요."
  </box>
  <box gap={2}>
    <row align="center" gap={2}>
      <icon name="messages-square" color="secondary"/>
      **1. AI가 과거의 이야기를 묻는다**
    </row>
    "취업 준비 말고, 그동안 시간을 보내면서 기억에 남는 일이 있었나요?"

    사용자가 취미, 가족과의 시간, 일상에서 겪은 일 등을 자유롭게 이야기해.
  </box>
  <divider color="subtle"/>
  <box gap={2}>
    <row align="center" gap={2}>
      <icon name="book-open" color="secondary"/>
      **2. AI가 삶의 기록을 재구성한다**
    </row>
    <box background="surface-secondary" radius="lg" padding={3} gap={2}>
      <text color="secondary" size="xs">나의 이야기 · 발견한 경험</text>
      <list marker="bullet" gap={1}>
        <list-item>혼자 요리하며 새로운 레시피를 시도했던 시간</list-item>
        <list-item>가족의 스마트폰 사용을 도와주었던 경험</list-item>
        <list-item>꾸준히 관심을 가졌던 영화와 영상 콘텐츠</list-item>
      </list>
    </box>
    AI가 단순한 일상에서도 관심사나 행동 패턴을 찾아 보여주되, 이를 임의로 전문 역량이나 성과로 포장하지는 않아.
  </box>
  <divider color="subtle"/>
  <box gap={2}>
    <row align="center" gap={2}>
      <icon name="compass" color="secondary"/>
      **3. AI가 다음 경험을 추천한다**
    </row>
    "새로운 요리법을 시도했던 경험이 있네요. 요리가 여전히 재미있다면 이번에는 지역의 무료 요리 프로그램을 찾아볼까요?"

    추천은 반드시 취업으로 연결될 필요가 없어. 새로운 관심사를 탐색하는 것만으로도 충분해.
  </box>
</box>

## 기존 서비스와 차별화할 부분

조사해보니 <Link url="https://rememberthis.ai/" title="Remember This"/>나 <Link url="https://thenfold.com/" title="thenfold"/>처럼 사진·메모·과거 기록을 AI로 정리하거나 생각의 변화를 되짚는 서비스가 이미 있어.

또한 고용24의 <Link url="https://www.work24.go.kr/cm/c/f/1100/selecSystInfo.do?systClId=SC00000189&systId=SI00000319" title="청년도전지원사업"/>에서도 자신감 회복과 진로 탐색을 제공하고 있어. <Cite refs={["turn686484search3","turn686484search5","turn686484search0"]}/>

따라서 차별화의 중심은 **취업 공백을 겪는 사람이 자신의 경험을 해석하는 방식을 바꾸고, 그 경험에서 새로운 선택지를 발견하도록 돕는 과정**이어야 해.

해커톤 MVP라면 자유 대화 입력, AI 경험 분석, 개인 타임라인, 관심사 기반 다음 활동 추천의 네 가지 기능으로 시작할 수 있겠어.

다만 본격적으로 기획하기 전에 한 가지는 정해야 해.

**이 서비스의 최종 목적을 어디에 두고 싶어?**

{@body const [goal,setGoal] = DIL.useState("life")}
<box gap={2}>
  <radio-group direction="col" value={goal} onChange={setGoal}>
    <radio value="life">**A. 취업과 관계없이 자신을 다시 발견하는 것**

    <text color="secondary" size="sm">일상의 의미, 관심사, 잊고 있었던 경험을 발견하고 삶을 이어갈 동기를 찾는 서비스</text></radio>
    <radio value="career">**B. 취업 공백기를 새로운 관점으로 해석하는 것**

    <text color="secondary" size="sm">공백기 동안의 실제 경험에서 역량과 강점을 찾아 진로 탐색과 취업 준비로 연결하는 서비스</text></radio>
    <radio value="both">**C. A에서 시작해서 B까지 이어지는 것**

    <text color="secondary" size="sm">자신의 삶을 다시 이해하는 것이 먼저이고, 취업과 사회 복귀는 이후에 선택할 수 있는 방향 중 하나인 서비스</text></radio>
  </radio-group>
  <button block onClick={()=>GenUI.issueNewTurn(({life:"공백이 아니라, 내 이야기 서비스는 취업과 무관하게 자신을 재발견하고 삶을 이어갈 동기를 찾는 것이 목적이야. 이 방향으로 독창적인 핵심 기능을 기획해보자.",career:"공백이 아니라, 내 이야기 서비스는 공백기의 실제 경험을 강점과 역량으로 재해석해서 진로 탐색과 취업 준비로 연결하는 것이 목적이야. 이 방향으로 기획해보자.",both:"공백이 아니라, 내 이야기 서비스는 먼저 자신을 재발견하고, 취업과 사회 복귀는 이후 선택할 수 있도록 하고 싶어. 이 방향으로 기획해보자."})[goal])}>이 방향으로 기획하기</button>
</box>
`````

<a id="m013"></a>
## M013 · 사용자 — 경험 기반 사람 추천

원문 메시지 ID: `ce1e5012-2d47-45a5-a5b7-68dab4eeecd2`

`````text
ai로 추천? 너무 형식적인거같아 ai가 뭘추천해줄수있는데 차라리 추천해줄수있는 사람을 ai가 찾는게 낫지
`````

<a id="m014"></a>
## M014 · 답변 — 경험 기반 사람 추천

원문 메시지 ID: `9cdac18e-14fb-4e60-9d96-6877bdb86686`

`````text
그 방향이면 AI의 역할이 훨씬 명확해져. **AI가 인생의 방향을 추천하는 게 아니라, 내 이야기를 이해하고 현실적인 조언을 해줄 수 있는 사람을 찾아주는 서비스**인 거지.

이렇게 하면 해커톤 주제인 'AI 기반 추천 서비스'에도 부합해. 추천 대상이 활동이나 직업이 아니라 **사람**이 되는 거야.

## 공백이 아니라, 내 이야기

<text color="secondary" size="sm">서비스 콘셉트: 나의 시간을 이해할 수 있는 사람을 연결하는 AI 매칭 서비스</text>

예를 들어 사용자가 이렇게 이야기해.

<box background="surface-secondary" radius="lg" padding={3} gap={1}>
  "대학교 졸업하고 3년 동안 취업 준비를 했는데 계속 떨어졌어요. 이제는 제가 뭘 잘하는지도 모르겠고, 다른 길을 찾아야 할지도 모르겠어요."
</box>

일반적인 AI 상담 서비스라면 자신감을 회복하는 방법이나 새로운 진로를 제안하겠지.

하지만 이 서비스의 AI는 다르게 작동해.

**AI가 이 사람과 실제로 대화해 줄 수 있는 사람을 찾는 거야.**

<box border radius="xl" padding={3} gap={3}>
  <row align="center" gap={2}>
    <icon name="users" color="secondary"/>
    **AI가 찾아준 연결 후보 — 가상 예시**
  </row>
  <box gap={1}>
    <row justify="between" align="center">
      **A · 장기 취업 준비 경험자**
      <badge>경험 공유</badge>
    </row>
    4년 동안 취업을 준비하다가 새로운 직무를 선택한 사람. 비슷한 상황에서 어떤 고민을 했는지 이야기할 수 있어.
  </box>
  <divider color="subtle"/>
  <box gap={1}>
    <row justify="between" align="center">
      **B · 다른 분야로 진로를 변경한 사람**
      <badge>진로 탐색</badge>
    </row>
    원래 전공과 다른 분야에서 일하고 있는 사람. 진로를 바꿀 때 무엇을 고려했는지 공유할 수 있어.
  </box>
  <divider color="subtle"/>
  <box gap={1}>
    <row justify="between" align="center">
      **C · 비슷한 고민을 하는 또래**
      <badge>동료 연결</badge>
    </row>
    지금도 진로를 고민하고 있는 사람. 반드시 해결책을 제시하지 않아도 서로 경험을 나눌 수 있어.
  </box>
  <caption>모두 설명을 위해 만든 가상 인물이며, 실제 이용자 데이터가 아니야.</caption>
</box>

## 여기서 AI가 실제로 하는 일

핵심은 단순히 나이, 전공, 희망 직종이 비슷한 사람을 연결하는 게 아니야.

1. **이야기 이해:** 사용자가 겪은 경험, 현재 고민, 어떤 대화를 원하는지 분석
2. **경험 기반 매칭:** 연결에 동의한 사람들의 실제 경험과 비교해 적합한 후보 탐색
3. **연결 이유 제시:** 왜 이 사람이 도움이 될 수 있는지, 어떤 부분에서 경험이 겹치는지 설명
4. **대화 지원:** 사용자가 원하면 대화를 시작할 질문을 정리

다만 비슷한 경험을 했다고 반드시 서로를 잘 이해하는 건 아니야. 그래서 AI의 매칭 결과는 후보 추천에 그치고, 실제 연결은 양측이 선택해야 해.

## 이 아이디어에서 중요한 차별점

일반적인 멘토링 서비스는 '누가 더 많은 경력과 전문성을 가지고 있는가'에 초점을 맞추는 경우가 많아.

여기서는 오히려 **어떤 시간을 살아왔고, 어떤 경험을 공유할 수 있는가**에 집중하는 거야.

취업에 성공한 사람만 멘토가 되는 것도 아니고, 현재 취업하지 않은 사람도 다른 사람에게 자신의 경험을 나눌 수 있지.

다만 이것만으로 기존 멘토 매칭 플랫폼과 차별화됐다고 단정할 수는 없어. 유사 서비스 비교가 필요하고, 특히 참여자를 모집하고 신뢰할 수 있는 관계를 만드는 것이 실질적인 개발 과제야.

---

그런데 여기서 하나 확인하고 싶어.

**네가 생각하는 '추천해 줄 수 있는 사람'이 어느 쪽에 가까워?**

{@body const [kind,setKind] = DIL.useState("mentor")}
<box gap={2}>
  <radio-group direction="col" value={kind} onChange={setKind}>
    <radio value="mentor">**① 나에게 조언해 줄 사람**

    <text color="secondary" size="sm">비슷한 경험을 했거나 먼저 그 시간을 지나온 사람을 찾아 연결</text></radio>
    <radio value="opportunity">**② 나의 가능성을 발견하고 기회를 줄 사람**

    <text color="secondary" size="sm">내 이야기를 바탕으로 내가 가진 경험이나 잠재력을 필요로 하는 사람과 연결</text></radio>
    <radio value="peer">**③ 나와 비슷한 이야기를 가진 사람**

    <text color="secondary" size="sm">가르치거나 평가하는 관계가 아니라, 서로의 경험을 나누는 관계</text></radio>
  </radio-group>
  <button block onClick={()=>GenUI.issueNewTurn(({mentor:"공백이 아니라, 내 이야기에서 AI가 비슷한 경험을 지나온 조언자를 찾아 연결하는 방향이야. 이 구조를 더 참신하게 발전시켜보자.",opportunity:"공백이 아니라, 내 이야기에서 AI가 사용자의 경험과 잠재력을 필요로 하는 사람을 찾아 연결하는 방향이야. 이 구조를 더 참신하게 발전시켜보자.",peer:"공백이 아니라, 내 이야기에서 AI가 비슷한 이야기를 가진 사람들을 서로 연결하는 방향이야. 이 구조를 더 참신하게 발전시켜보자."})[kind])}>선택한 방향으로 발전시키기</button>
</box>
`````

<a id="m015"></a>
## M015 · 사용자 — 아이들을 위한 서비스

원문 메시지 ID: `52679ef4-68a5-4313-a7ac-a8a603f59312`

`````text
바꿔보자 아이들을 위한 서비스 없을까
`````

<a id="m016"></a>
## M016 · 답변 — 아이들을 위한 서비스

원문 메시지 ID: `01c61248-dd0b-4d74-946a-af6b22a3571f`

`````text
아이들을 대상으로 한다면 꽤 다양한 방향이 나올 수 있어. 특히 이번 해커톤에서는 **아이에게 무언가를 추천해주는 AI**보다, 아이들이 일상에서 겪는 문제를 새로운 방식으로 해결하는 서비스가 더 차별화될 수 있다고 봐.

여기서는 일단 **초등학생(약 7~12세)**을 주요 대상으로 가정할게. 유아나 중·고등학생이면 문제와 서비스 설계가 달라져.

내가 주목하고 싶은 관점은 두 가지야.

- **AI 추천:** 아이에게 무엇을 추천할 것인가가 아니라, 아이가 어떤 경험을 할 수 있도록 도울 것인가?
- **AI 정보보호:** 아이를 감시하거나 인터넷을 차단하는 대신, 아이가 스스로 자신의 정보와 권리를 지킬 수 있을까?

## 1. AI 기반 추천 서비스

<box gap={3}>
  <row align=start gap={3}>
    <box background="surface-secondary" radius="lg" padding={3}>
      <icon name="users-round" size="xl"/>
    </box>
    <box flex="1" gap={1}>
      <title size="lg">① 우리 모두 놀 수 있는 놀이</title>
      <text color="secondary" weight="medium" size="xs">AI가 추천하는 것은 놀이가 아니라, 모두 참여할 수 있는 놀이 규칙</text>
      친구들과 놀고 싶지만 체력, 성격, 언어, 장애 등 여러 이유로 같은 놀이에 참여하기 어려운 아이들이 있을 수 있어.

      **상황:** "우리 반에서 술래잡기를 하고 싶은데 한 친구는 뛰기 어려워요."

      AI는 술래잡기 대신 다른 놀이를 추천하는 것이 아니라, 술래잡기를 모두가 참여할 수 있도록 규칙을 바꿔 제안해.

      **AI 역할:** 참여 인원과 각자의 활동 조건을 이해하고, 기존 놀이를 변형한 규칙 생성. 교사나 보호자가 안전성을 확인.
    </box>
  </row>
  <divider color="subtle"/>
  <row align=start gap={3}>
    <box background="surface-secondary" radius="lg" padding={3}>
      <icon name="lightbulb" size="xl"/>
    </box>
    <box flex="1" gap={1}>
      <title size="lg">② 세상 모든 것이 장난감이 되는 날</title>
      <text color="secondary" weight="medium" size="xs">AI가 주변 사물의 새로운 가능성을 추천</text>
      아이가 집에 있는 물건을 사진으로 찍으면 AI가 그 물건들로 해볼 수 있는 놀이, 실험, 창작 활동을 추천해.

      **상황:** 종이컵 5개, 빨대 3개, 고무줄 하나를 촬영.

      AI가 "이 재료로 얼마나 높은 탑을 만들 수 있을까?" 같은 도전 과제를 만들고 안전한 제작 방법을 제안해.

      **차별점:** 장난감이나 교육 콘텐츠 구매를 유도하는 게 아니라, 이미 가지고 있는 물건으로 새로운 경험을 만드는 추천.
    </box>
  </row>
  <divider color="subtle"/>
  <row align=start gap={3}>
    <box background="surface-secondary" radius="lg" padding={3}>
      <icon name="message-circle" size="xl"/>
    </box>
    <box flex="1" gap={1}>
      <title size="lg">③ 누구에게 어떻게 말해야 할까?</title>
      <text color="secondary" weight="medium" size="xs">AI가 정답 대신 도움을 요청하는 방법을 추천</text>
      아이가 어려운 상황을 겪더라도 누구에게 어떻게 이야기해야 하는지 모를 수 있어.

      **상황:** "친구가 자꾸 내 물건을 가져가는데 싫다고 말하기 어려워요."

      AI가 아이의 상황에 맞춰 친구에게 의사를 표현하는 문장이나 신뢰할 수 있는 어른에게 도움을 요청하는 방법을 추천해.

      **차별점:** AI가 상담자나 문제 해결자가 되는 게 아니라, 아이와 실제 사람 사이의 소통을 지원하는 역할. 위험한 상황에서는 AI 대화보다 즉각적인 사람의 지원이 우선돼야 해.
    </box>
  </row>
</box>

## 2. AI 기반 정보보호 서비스

이쪽은 **기존 보호 방식의 관점을 뒤집는 아이디어**가 가능해.

<box gap={3}>
  <row align=start gap={3}>
    <box background="surface-secondary" radius="lg" padding={3}>
      <icon name="image-off" size="xl"/>
    </box>
    <box flex="1" gap={1}>
      <title size="lg">④ 내 사진인데 왜 어른 마음대로 올려요?</title>
      <text color="secondary" weight="medium" size="xs">아이의 개인정보를 보호자로부터도 보호하는 서비스</text>
      보호자가 아이의 사진을 SNS에 올릴 때, 아이는 해당 게시물에 대해 의견을 표현할 기회가 없을 수 있어.

      **상황:** 부모가 자녀의 입학식 사진을 SNS에 올리려고 해.

      AI가 학교 이름, 교복, 명찰, 위치 단서를 분석하고 아이와 보호자에게 공개 전 확인할 사항을 알려줘. 아이가 원치 않으면 게시하지 않거나 다른 사진을 고르도록 지원해.

      **차별점:** 보호자가 아이를 감시하는 서비스가 아니라, 아이의 개인정보 자기결정권을 보호자가 존중하도록 돕는 서비스.
    </box>
  </row>
  <divider color="subtle"/>
  <row align=start gap={3}>
    <box background="surface-secondary" radius="lg" padding={3}>
      <icon name="gamepad-2" size="xl"/>
    </box>
    <box flex="1" gap={1}>
      <title size="lg">⑤ 게임 속에서 나를 얼마나 알 수 있을까?</title>
      <text color="secondary" weight="medium" size="xs">개인정보를 직접 말하지 않아도 발생하는 노출 위험 탐지</text>
      아이들이 온라인 게임에서 집 주소나 전화번호를 알려주지는 않더라도, 닉네임·프로필·채팅·사진에 신원 단서가 남을 수 있어.

      **상황:** 게임 친구에게 보내려고 채팅 화면을 캡처했어.

      AI가 캡처 화면의 학교 이름, 실명, 연락처 등 노출 가능한 정보를 탐지하고 어린이가 이해할 수 있는 설명을 제공해.

      **차별점:** 게임 자체를 차단하는 것이 아니라, 아이가 안전하게 소통하는 방법을 배우도록 돕는 것.
    </box>
  </row>
  <divider color="subtle"/>
  <row align=start gap={3}>
    <box background="surface-secondary" radius="lg" padding={3}>
      <icon name="palette" size="xl"/>
    </box>
    <box flex="1" gap={1}>
      <title size="lg">⑥ 내 작품은 보여주고 싶지만, 내 정보는 아니에요</title>
      <text color="secondary" weight="medium" size="xs">어린이 작품의 창작물과 개인정보를 분리</text>
      아이의 그림이나 글짓기를 온라인에 공개할 때 작품에 이름, 학교, 학년, 얼굴 등이 포함될 수 있어.

      AI가 작품의 창작 내용은 유지하고 개인정보가 포함된 부분만 찾아 비공개 처리 방식을 추천해.

      **상황:** 그림대회에 출품한 그림에 이름과 학교가 적혀 있어.

      AI는 아이와 보호자 또는 교사의 확인을 거쳐 공개용 사본을 만드는 과정을 도와줘.

      **차별점:** 개인정보 보호를 위해 공개를 포기하는 것이 아니라, 개인정보와 창작물을 분리해서 공개할 수 있도록 돕는 것.
    </box>
  </row>
</box>

## 3. 실제로 필요한 문제일까?

아이들의 온라인 개인정보 보호는 이미 정부가 대응하고 있는 영역이야.

개인정보보호위원회는 아동·청소년 시절 작성한 게시물의 삭제를 지원하는 '지우개 서비스'를 운영하고 있어. 2026년 9월 보도에 따르면 2023년 4월부터 2026년 7월까지 신청이 4만 7천 건을 넘었어. <Cite ref="turn900687search2"/>

또한 UNICEF의 2025년 아동 AI 가이드라인은 개인정보 보호뿐 아니라 아이의 권리, 자율성, 안전, 설명 가능성을 강조하고 있어. <Cite ref="turn900313search0"/>

이런 자료는 아이들의 정보보호가 실제 정책 과제라는 근거는 되지만, 위에 제시한 개별 서비스의 수요나 독창성이 검증됐다는 뜻은 아니야.

## 4. 해커톤 관점에서 비교

| 아이디어 | 관점의 차별성 | MVP 구현 부담 | 주의할 점 |
|---|---|---|---|
| 모두가 놀 수 있는 놀이 | 높음 | 중간 | 실제 놀이 규칙의 안전성 |
| 주변 물건 활용 놀이 | 중간 | 낮음~중간 | 기존 AI 놀이 추천과 유사 |
| 도움 요청 방법 추천 | 중간~높음 | 중간 | 아동 안전과 응답 오류 |
| 내 사진의 결정권 | 높음 | 중간 | 아이의 의사를 확인하는 설계 |
| 게임 속 정보 노출 탐지 | 중간 | 중간 | 기존 보안 도구와 차별화 |
| 내 작품과 개인정보 분리 | 높음 | 낮음~중간 | 작품 내용 훼손 방지 |

이 중에서 개인적으로 더 검토할 가치는 **① 모두가 놀 수 있는 놀이**와 **④ 내 사진인데 왜 어른 마음대로 올려요?** 두 가지에 있다고 판단해.

①은 AI 추천을 상품 추천이 아닌 *참여 기회의 확대*로 해석하고, ④는 AI 정보보호를 아이에 대한 *감시가 아닌 권리 보호*로 해석한다는 점에서 주제 해석이 독특해.

특히 ④는 실제 사진을 업로드해 노출 요소를 탐지하고, 공개 전 위험을 설명하며, 아이의 선택에 따라 수정하는 시연 흐름도 만들 수 있어.

---

그런데 중요한 질문이 있어.

**네가 생각하는 '아이들을 위한 서비스'는 초등학생이 직접 사용하는 서비스야, 아니면 부모나 교사가 아이들을 위해 사용하는 서비스도 괜찮아?**

이 차이에 따라 아이디어가 상당히 달라져. 아이들이 직접 사용하는 쪽이라면 놀이·의사표현·권리 중심으로, 어른이 사용하는 것도 괜찮다면 아이들이 겪는 문제를 발견하거나 예방하는 방향까지 더 넓혀볼 수 있어.
`````
