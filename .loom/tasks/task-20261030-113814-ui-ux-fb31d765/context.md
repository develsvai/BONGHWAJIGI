# Context

## Loom 코드 계약

아래 항목은 Loom 코드에 고정된 runtime 동작 계약입니다. 관련 흐름을 바꾸기 전 `loom contract show <id>`로 확인합니다.

- `task-execution`: Task 실행 전 prompt/context/previous-results에 들어가는 입력 경계입니다. 명령: `loom contract show task-execution`. Source: `loom/application/context_pack.py`, `loom/application/team_policy.py`
- `done-guardrail`: Task를 DONE으로 인정하기 전에 필요한 산출물과 상태 전이를 검증하는 계약입니다. 명령: `loom contract show done-guardrail`. Source: `loom/application/services.py`

## Project Memory

# BONGHWAJIGI

Loom 프로젝트 메모리 루트입니다.

이 파일은 `loom init`으로 생성되며 `loom analyze-repo`로 보강할 수 있습니다.

## Workspace Policy

- Output language: `ko`
- Agent provider: `claude`
- Agent model: `adapter-default`
- Reasoning effort: `high`
- Required branch: `develop`
- Dirty branch switch: `blocked`
- Commit policy: `manual`
- Include `.loom` metadata in Git: `yes`
- Read-only parallel execution: `allowed`
- Validation environment: `auto`
- Previous Task result limit: `2`
- Workspace required docs: -
- Loom fixed guardrails and verified Team required policies take precedence over this Workspace Policy.

## Job

- Title: BONGHWAJIGI 초기 설계 문서 정리
- Goal: 사용자 요청에 따라 Loom workspace를 초기화하고 현재 대화와 회의 전사의 설계를 docs에 정리한다. UI/UX 수령 전에는 기능 구현과 배포를 진행하지 않는다.
- Branch: develop
- Task count: `1`

## Task

- Title: 초기 설계와 회의 대조 및 UI UX 인계 문서 작성
- Description: 사용자가 현재 에이전트에게 요청한 loom init과 docs 정리를 수행한다. 재난 대응 서비스 요구사항, 다중 출처 수집, 주변 영향 평가, 개인별 대응, AI 역할 제한, GPU 모델 후보와 회의 미결정을 구분해 기록한다.
- Expected output: 프로젝트 README, docs 문서 6개, 로컬 파일 제외 규칙, 검증된 Loom 작업 기록
- Done condition: docs에서 서비스 흐름과 확정 및 제안 및 미결 항목을 확인할 수 있고 내부 링크와 비밀정보 제외 및 Loom strict 검증을 통과하며 변경과 완료 기록이 커밋되어 있다.
- In scope: Loom 초기화 기록; README.md; .gitignore; docs 아래 설계와 인계 문서; 문서 검증; 로컬 커밋
- Out of scope: 기능 구현; 서버 접속; 모델 설치 및 학습; 배포; 원격 push; UI UX 확정; 회의 원문 또는 인증정보 저장
- Validation hint: 내부 Markdown 링크와 문서 내용 및 민감정보 검토, git diff --check, loom validate --strict
- Required docs: -
- Memory refs: -
- Document outputs: `docs/README.md`, `docs/product-and-scenarios.md`, `docs/architecture-and-data-flow.md`, `docs/ai-and-infrastructure.md`, `docs/decisions-and-meeting-review.md`, `docs/ui-ux-handoff.md`
- Document output exceptions: -
- Source proposal: `-`
- Status: PENDING
- Assigned agent: -

## Advisor Source Prompt

No Advisor source prompt recorded for this Task.

## Inclusion Policy

- Mandatory execution files: `prompt.md`, `context.md`, and `previous-results.md`.
- Always included: project memory, current Job/Task metadata, and Job notes.
- Previous results: up to the latest 2 recorded results from earlier Tasks in this Job.
- Job context refs: explicit Job-scoped references selected by the controlling agent or user.
- Task required docs: mandatory Task-scoped documents; missing refs block validation and execution.
- Task memory refs: mandatory Task-scoped workflow memory references; missing or non-memory refs block validation and execution.
- Repository documents, validation documents, and skill rules: included only through explicit Job context refs, Task required docs, or Task memory refs.
- Verified Team Policy Snapshot: included before Active Memory; required policy cannot be overridden by lower-priority context.
- Active workflow memory with an `always` category is included automatically while its status is `ACTIVE`.
- `task_selected` and `reference_only` memory is included only through explicit Task memory refs.
- Consumed proposals, rejected proposals, resolved memory, superseded memory, and archived memory are excluded.
- Unreferenced repository files and results from other Jobs are not included.
- `AGENTS.md` and `CLAUDE.md` remain session-level controlling-agent entrypoints and are not treated as task context artifacts by default.

## Job Notes

# Notes

## Context References

No explicit context references recorded for this job.

## Required Documents and Memory

No task-level required docs or memory refs recorded.

## Verified Team Policies

No verified Team Policy Snapshot is active.

## Active Workflow Memory

No active workflow memory recorded.
