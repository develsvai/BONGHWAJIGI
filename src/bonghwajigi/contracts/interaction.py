from typing import Literal

from pydantic import AwareDatetime, Field, field_validator

from bonghwajigi.contracts.app import ContextOverrides, StatePatch, Strict
from bonghwajigi.contracts.policy import Identifier
from bonghwajigi.contracts.routes import ReferenceRoute


class TextTurnWrite(Strict):
    client_turn_id: Identifier
    text: str = Field(min_length=1, max_length=1000)
    base_response_revision: int = Field(ge=1)
    base_context_revision: int = Field(ge=0)

    @field_validator("text")
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError("대화 내용을 입력하세요.")
        return value.strip()


class ProposalEvidence(Strict):
    field: str
    value: bool | str
    quote: str


class ContextProposal(Strict):
    requires_confirmation: Literal[True] = True
    base_revision: int
    state: StatePatch
    overrides: ContextOverrides
    evidence: list[ProposalEvidence]


class DialogueAssistant(Strict):
    text: str
    source: Literal["qwen_grounded", "reviewed_policy_fallback"]
    action_ids: list[str]


class TextTurnData(Strict):
    turn_id: str
    response_id: str
    status: Literal["processing", "complete"]
    response_revision: int
    context_revision: int
    valid_until: AwareDatetime
    assistant: DialogueAssistant | None
    proposal: ContextProposal | None
    reason_code: str | None


class SimulationRoute(ReferenceRoute):
    valid_until: AwareDatetime
    input_versions: dict[str, int]


class RouteData(Strict):
    status: Literal["simulation", "unavailable"]
    route: SimulationRoute | None
    reason: str
