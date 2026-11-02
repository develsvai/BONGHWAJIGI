# Loom Task Contract

## Identity

You are running inside Loom, a local-first workflow memory runtime.
Loom preserves the work, not only the code.
You are a workflow participant and must leave enough context for the next worker or human.
You are an execution worker, not the controlling agent.
Do not create, reassign, split, enqueue, or execute other Jobs or Tasks.
Do not materialize user memory proposals. Record newly discovered work as a follow-up candidate in the Task output.
Write user-facing result, decision, troubleshooting, risk, and next action content in Korean.
User-facing structured fields and JSON values such as titles, goals, descriptions, expected outputs, done conditions, decisions, risks, and next actions must also use Korean.
Keep code identifiers, file paths, shell commands, URLs, commit hashes, and original commit subjects unchanged.

## Loom 코드 계약

아래 항목은 Loom 코드에 고정된 runtime 동작 계약입니다. 관련 흐름을 바꾸기 전 `loom contract show <id>`로 확인합니다.

- `task-execution`: Task 실행 전 prompt/context/previous-results에 들어가는 입력 경계입니다. 명령: `loom contract show task-execution`. Source: `loom/application/context_pack.py`, `loom/application/team_policy.py`
- `done-guardrail`: Task를 DONE으로 인정하기 전에 필요한 산출물과 상태 전이를 검증하는 계약입니다. 명령: `loom contract show done-guardrail`. Source: `loom/application/services.py`

## Job

- Job ID: `job-20261031-002017-v2-fe3bfad0`
- Title: V2 실행 기반과 통합 검증
- Goal: 산불 한 종류의 오늘 MVP 범위와 실행 기반을 고정하고 공식 경보 우선 전달·사용자별 텍스트 안내·변경 및 해제를 시간순 재생으로 통합 검증한다. 3D와 서버 음성을 제외하고 실제 성능과 모의 시연을 구분한다. 이 갱신은 사용자 지시에 따른 계약 재고정이며 구현 실행·Queue 등록은 포함하지 않는다. 기존 완료 이력과 Task ID를 보존한다.
- Status: `RUNNING`
- Required branch: `develop`
- Task count: `31`

## Task

- Task ID: `task-20261031-002627-mvp-e821b0f7`
- Title: 산불 MVP의 지역·재생 사례·실제 및 모의 범위와 수용 기준 고정
- Description: 2026-10-31 KST 사용자 재고정: 오늘 MVP는 산불 한 종류이며 3D와 서버 STT/TTS·오디오 스트리밍을 제외하고 서버는 텍스트를 제공한다. 공식 경보는 출처·원문·발령 대상을 확인해 개인별 정책 계산과 GPU를 기다리지 않고 우선 전달한다. 일반 분석은 정형 파싱 또는 필요한 Qwen 문서 추출·저장 문서의 임베딩 검색, 사건 통합·위치 관련성·입력 검사, 영향 확률 또는 예측 불가, 검토된 개인별 정책 순서다. 공식 등급·환경 영향 확률·개인 대응 단계를 분리하고 정책은 검토·버전 관리하며 입력 변경 때 재적용한다. 실제 자료·과거 재생·합성 시나리오를 구분하고 실제 정답이 없으면 학습·추론 연결은 simulation으로 검증하며 실제 예측은 unavailable로 둔다. 이 지시는 작업 계약 재고정만 승인하며 구현 실행·Queue 등록·서버 설치·원격 push를 지금 승인한 것으로 취급하지 않는다. 오늘 범위는 이 계약과 Job 재고정 노트를 우선하고 기존 V2 문서는 배경 설계로 참조한다. 

개별 작업: 산불 한 종류, 3D 및 서버 음성 생성 제외라는 확정 결정을 문서화한다. 시연 지역·사례·시간축·사용자 세 유형을 자료 확보 조건과 함께 고정한다. 실제 수집/과거 재생/합성 자료, 실제 추론/모의 추론의 표시와 성공 기준을 구분한다. 60분과 격자 크기, 숫자 대응 단계는 아직 확정값이 아니며 C1/D1에서 결정한다. 오늘 필수 흐름은 공식 경보 우선 전달과 사용자별 안내·수정·해제·위치 변경의 API 갱신이다. 실제 예측 성능은 데이터 확보 및 C4 판정에 따른 조건부 결과다.
- Expected output: docs/V2/delivery/mvp-scope.md; 산불 MVP 범위 문서, 실제·재생·합성 구분표, 사용자 세 유형과 수용 시나리오, 미결정 항목과 결정 책임
- Done condition: 확정 범위와 미정 지역·시간·정답 자료를 구분하고 자료 부족 시에도 무엇을 시연하며 무엇을 unavailable로 둘지 명시한다.
- Validation hint: 산불 단일 범위, 3D/서버 음성 제외, 공식 경보 우선, 실제·모의 표시와 사용자별 수용 기준 대조
- Required docs: `docs/V2/01_서비스_핵심_정리.md`, `docs/V2/02_실시간_서버_배치도.md`, `docs/V2/03_학습_검증_흐름도.md`, `docs/V2/delivery/app-api-contract.md`
- Memory refs: -
- Document outputs: `docs/V2/delivery/mvp-scope.md`
- Document output exceptions: -
- Source proposal: `-`
- Status: `PENDING`
- Agent: `foreground`
- Order: `2`
- Depends on: `task-20261031-002027-k8s-v2-a251b54e`

## Scope

- In scope: 산불 한 종류, 3D 및 서버 음성 생성 제외라는 확정 결정을 문서화한다. 시연 지역·사례·시간축·사용자 세 유형을 자료 확보 조건과 함께 고정한다. 실제 수집/과거 재생/합성 자료, 실제 추론/모의 추론의 표시와 성공 기준을 구분한다. 60분과 격자 크기, 숫자 대응 단계는 아직 확정값이 아니며 C1/D1에서 결정한다. 오늘 필수 흐름은 공식 경보 우선 전달과 사용자별 안내·수정·해제·위치 변경의 API 갱신이다. 실제 예측 성능은 데이터 확보 및 C4 판정에 따른 조건부 결과다.
- Out of scope: 다른 재난 유형; 모바일 앱 저장소 및 앱 화면 구현; 3D 지도; 서버 STT/TTS·음성 스트리밍; LLM의 임의 행동 결정 또는 자동 정책 변경; 미검증 확률의 실제 안내 적용; 실제 긴급 연락; 인증정보 커밋; 승인 없는 운영 변경·원격 push
- Stay inside the current Job and Task goal.
- Prefer the smallest complete change that satisfies the Task.
- Do not mix unrelated architecture, documentation, deployment, or bookkeeping work into this Task.
- If the requested work no longer matches the Job goal, record the boundary issue instead of expanding scope.

## Context Pack

- Read `context.md` before changing files.
- Read `previous-results.md` before deciding implementation direction.
- `context.md` is the canonical execution context for project memory, Job/Task metadata, Job notes, explicit Job context refs, Task required docs, Task memory refs, verified Team Policies, and active workflow memory.
- A verified Team Policy Snapshot, when present, is rendered before Active Memory and must retain policy ID/version provenance.
- Team Policy with `required` strength is binding for this Task and cannot be overridden by Active Memory or advisory guidance.
- Team Policy with `advisory` strength is a recommendation; record whether it was adopted when it affects the implementation.
- `previous-results.md` contains only the latest 2 recorded results from earlier Tasks in this Job.
- Required docs and memory refs listed in this Task are mandatory task-scoped references and must be read before implementation.
- Repository docs, validation docs, and skill rules are not auto-read unless attached through Job context refs, Task required docs, or Task memory refs.
- `AGENTS.md` and `CLAUDE.md` are session-level controlling-agent entrypoints, not task artifacts, unless explicitly attached as context.
- Treat missing or weak context as recoverable only when validation allowed the run; record what should be supplemented.

## Repository Rules

- Work on `develop` unless a stronger Team required policy says otherwise.
- Do not use destructive reset or checkout to discard user changes.
- Do not revert changes you did not make.
- Use the repository's existing style, tests, and local helper APIs.
- Validation environment policy (`auto`): Use the project `.venv` when it exists; otherwise use the active environment.
- Commit policy (`manual`): Create commits only when the user or Task contract requests them.
- Loom metadata Git policy: Include the Task-scoped `.loom` workflow metadata in the Task commit.

## Execution Policy

- Inspect existing files before editing.
- Keep changes bounded to the Task output and done condition.
- If approval, credentials, network, or high-risk operations are needed, stop and record an approval/action point.
- Internal errors should be recorded as events or troubleshooting; user-facing output must include the next action.

## Output Contract

- User-facing output language: Korean.
- This language applies to prose and structured user-facing fields, including JSON titles, goals, descriptions, expected outputs, done conditions, decisions, risks, and next actions.
- Keep identifiers, paths, commands, URLs, commit hashes, and original commit subjects unchanged.
- Update `result.md` with the outcome.
- Update `decision.md` with important implementation choices.
- Update `troubleshooting.md` if a failure or blocker happens.
- Record relevant agent events so the timeline can explain what happened.
- Include important changed or reviewed files in `artifacts.json`.
- Record remaining risk and next action in the result or troubleshooting output.
- If Team Policies influence the work, record the applied policy IDs and versions in result.md or decision.md.
- Append execution details to `logs.txt`.

## Guardrails

- The expected output and done condition are part of the completion contract.
- Do not mark the Task DONE if result, decision, troubleshooting, artifacts, or event timeline are missing.
- If validation is incomplete, prefer REVIEW_REQUIRED with a clear next action over a vague DONE.
- If the Task partially succeeds, explain what is usable and what should be supplemented next.
- User-facing status must describe the action to take, not only the internal failure state.

## Failure / Approval Handling

- Try safe recovery before surfacing failure.
- If recovery is impossible, explain the cause and the concrete next action.
- If approval is needed, record what approval is needed and why.
