from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class GeminiApiModel(BaseModel):
    model_config = ConfigDict(frozen=True)


class InteractionStatus(StrEnum):
    IN_PROGRESS = "in_progress"
    REQUIRES_ACTION = "requires_action"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    INCOMPLETE = "incomplete"
    REQUIRES_CONTINUATION = "requires_continuation"


class ContentPart(GeminiApiModel):
    type: str
    text: str | None = None


class InteractionStep(GeminiApiModel):
    type: str
    content: list[ContentPart] = []


class Interaction(GeminiApiModel):
    status: InteractionStatus
    steps: list[InteractionStep] = []

    def output_text(self) -> str:
        return "".join(
            part.text
            for step in self.steps
            if step.type == "model_output"
            for part in step.content
            if part.type == "text" and part.text
        )
