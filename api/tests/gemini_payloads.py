import json
from typing import Any

from app.models.device_report import Device
from app.models.recommendation import Effort, Impact
from app.schemas.recommendation import RecommendationDraft, RecommendationSet


def sample_recommendation_set(lighthouse_ids: list[str] | None = None) -> RecommendationSet:
    return RecommendationSet(
        summary="Your site loads slowly on phones. Start with render-blocking files.",
        recommendations=[
            RecommendationDraft(
                title="Load scripts after the page appears",
                explanation="Scripts in the page header delay the first paint on phones.",
                steps=["Install a caching plugin", "Enable 'Delay JavaScript execution'"],
                impact=Impact.HIGH,
                effort=Effort.LOW,
                devices=[Device.MOBILE, Device.DESKTOP],
                lighthouse_ids=lighthouse_ids or ["render-blocking-resources"],
            ),
            RecommendationDraft(
                title="Set long cache times",
                explanation="Returning visitors download the same files again.",
                steps=["Turn on browser caching in your caching plugin"],
                impact=Impact.LOW,
                effort=Effort.LOW,
                devices=[Device.MOBILE],
                lighthouse_ids=["uses-long-cache-ttl"],
            ),
        ],
    )


def interaction_payload(text: str, status: str = "completed") -> dict[str, Any]:
    return {
        "id": "v1_test",
        "object": "interaction",
        "model": "gemini-3.8-flash",
        "status": status,
        "steps": [
            {"type": "thought", "content": [{"type": "text", "text": "Thinking..."}]},
            {"type": "model_output", "content": [{"type": "text", "text": text}]},
        ],
        "usage": {"total_tokens": 120},
    }


def recommendation_interaction(recommendation_set: RecommendationSet) -> dict[str, Any]:
    return interaction_payload(json.dumps(recommendation_set.model_dump(mode="json")))
