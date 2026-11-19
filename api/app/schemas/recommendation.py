from pydantic import BaseModel, ConfigDict, Field

from app.models.device_report import Device
from app.models.recommendation import Effort, Impact

MAX_RECOMMENDATIONS = 8
MAX_STEPS = 6


class RecommendationDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1)
    explanation: str = Field(min_length=1)
    steps: list[str] = Field(min_length=1, max_length=MAX_STEPS)
    impact: Impact
    effort: Effort
    devices: list[Device] = Field(min_length=1)
    lighthouse_ids: list[str] = Field(min_length=1)


class RecommendationSet(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str = Field(min_length=1)
    recommendations: list[RecommendationDraft] = Field(max_length=MAX_RECOMMENDATIONS)


class RecommendationResponse(RecommendationDraft):
    model_config = ConfigDict(from_attributes=True)

    rank: int
    lighthouse_ids: list[str]
