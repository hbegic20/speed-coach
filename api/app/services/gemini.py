import logging
from typing import Any

import httpx
from pydantic import SecretStr, ValidationError

from app.schemas.gemini_api import Interaction, InteractionStatus

logger = logging.getLogger(__name__)

INTERACTIONS_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/interactions"
API_REVISION = "2026-05-20"


class GeminiError(Exception):
    pass


class GeminiClient:
    def __init__(
        self,
        http_client: httpx.AsyncClient,
        api_key: SecretStr,
        model: str,
        timeout_seconds: float,
    ) -> None:
        self._http_client = http_client
        self._api_key = api_key
        self._model = model
        self._timeout_seconds = timeout_seconds

    async def generate_json(
        self, system_instruction: str, prompt: str, schema: dict[str, Any]
    ) -> str:
        response = await self._post(
            {
                "model": self._model,
                "system_instruction": system_instruction,
                "input": prompt,
                "response_format": {
                    "type": "text",
                    "mime_type": "application/json",
                    "schema": schema,
                },
                "generation_config": {"thinking_level": "low"},
                "store": False,
            }
        )
        interaction = _parse_interaction(response)
        if interaction.status is not InteractionStatus.COMPLETED:
            logger.warning("Gemini interaction ended with status %s", interaction.status)
            raise GeminiError(f"Interaction {interaction.status}")
        text = interaction.output_text()
        if not text:
            raise GeminiError("Interaction returned no text")
        return text

    async def _post(self, body: dict[str, Any]) -> httpx.Response:
        try:
            response = await self._http_client.post(
                INTERACTIONS_ENDPOINT,
                json=body,
                headers={
                    "x-goog-api-key": self._api_key.get_secret_value(),
                    "Api-Revision": API_REVISION,
                },
                timeout=self._timeout_seconds,
            )
        except httpx.HTTPError as error:
            logger.warning("Gemini request failed", exc_info=True)
            raise GeminiError("Request failed") from error
        if not response.is_success:
            logger.error("Gemini responded %s: %s", response.status_code, response.text[:500])
            raise GeminiError(f"HTTP {response.status_code}")
        return response


def _parse_interaction(response: httpx.Response) -> Interaction:
    try:
        return Interaction.model_validate_json(response.content)
    except ValidationError as error:
        logger.exception("Gemini returned an unexpected payload")
        raise GeminiError("Unexpected payload") from error
