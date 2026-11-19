import json
from collections.abc import Callable
from typing import Any

import httpx
import pytest
from pydantic import SecretStr

from app.services.gemini import API_REVISION, INTERACTIONS_ENDPOINT, GeminiClient, GeminiError
from tests.gemini_payloads import interaction_payload

API_KEY = "test-gemini-key"
SCHEMA = {"type": "object", "properties": {"summary": {"type": "string"}}}

Handler = Callable[[httpx.Request], httpx.Response]


def client_for(handler: Handler) -> GeminiClient:
    http_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return GeminiClient(
        http_client, api_key=SecretStr(API_KEY), model="gemini-3.8-flash", timeout_seconds=30
    )


def respond_with(status_code: int, body: Any) -> Handler:
    return lambda _request: httpx.Response(status_code, json=body)


async def generate(client: GeminiClient) -> str:
    return await client.generate_json("Be helpful.", "Audit data: {}", SCHEMA)


async def test_sends_a_structured_output_interaction() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=interaction_payload('{"summary": "ok"}'))

    await generate(client_for(handler))

    [request] = requests
    assert str(request.url) == INTERACTIONS_ENDPOINT
    assert request.headers["x-goog-api-key"] == API_KEY
    assert request.headers["Api-Revision"] == API_REVISION
    assert json.loads(request.content) == {
        "model": "gemini-3.8-flash",
        "system_instruction": "Be helpful.",
        "input": "Audit data: {}",
        "response_format": {"type": "text", "mime_type": "application/json", "schema": SCHEMA},
        "generation_config": {"thinking_level": "low"},
        "store": False,
    }


async def test_returns_only_the_model_output_text() -> None:
    client = client_for(respond_with(200, interaction_payload('{"summary": "ok"}')))

    assert await generate(client) == '{"summary": "ok"}'


@pytest.mark.parametrize("status", ["incomplete", "failed", "cancelled", "requires_action"])
async def test_rejects_unfinished_interactions(status: str) -> None:
    client = client_for(respond_with(200, interaction_payload('{"summ', status=status)))

    with pytest.raises(GeminiError):
        await generate(client)


async def test_rejects_interactions_without_output() -> None:
    client = client_for(respond_with(200, {"status": "completed", "steps": []}))

    with pytest.raises(GeminiError):
        await generate(client)


@pytest.mark.parametrize("status_code", [400, 403, 429, 500, 503])
async def test_rejects_error_responses(status_code: int) -> None:
    client = client_for(respond_with(status_code, {"error": {"code": status_code}}))

    with pytest.raises(GeminiError):
        await generate(client)


async def test_rejects_malformed_payloads() -> None:
    client = client_for(respond_with(200, {"status": "thinking-hard"}))

    with pytest.raises(GeminiError):
        await generate(client)


async def test_reports_timeouts() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timed out", request=request)

    with pytest.raises(GeminiError):
        await generate(client_for(handler))
