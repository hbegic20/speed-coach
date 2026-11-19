import json
from typing import Any

import pytest

from app.models.audit import Language, Platform
from app.models.device_report import Device
from app.models.recommendation import Effort, Impact
from app.schemas.recommendation import RecommendationDraft, RecommendationSet
from app.schemas.report import DeviceReportData, Finding
from app.services.gemini import GeminiError
from app.services.recommendations import (
    MAX_ATTEMPTS,
    MAX_FINDINGS_PER_DEVICE,
    RecommendationsUnavailableError,
    RecommendationWriter,
    build_prompt,
    build_system_instruction,
    recommendation_schema,
)
from tests.fakes import sample_report
from tests.gemini_payloads import sample_recommendation_set

URL = "https://example.com/"


def finding(lighthouse_id: str, description: str = "Plain description.") -> Finding:
    return Finding(
        lighthouse_id=lighthouse_id,
        title=f"Title {lighthouse_id}",
        description=description,
        score=0.2,
        display_value=None,
        savings_ms=100,
        savings_bytes=None,
    )


def report_with(findings: list[Finding], device: Device = Device.MOBILE) -> DeviceReportData:
    return sample_report(device).model_copy(update={"findings": findings})


class ScriptedGenerator:
    def __init__(self, outputs: list[str | Exception]) -> None:
        self.outputs = outputs
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    async def generate_json(
        self, system_instruction: str, prompt: str, schema: dict[str, Any]
    ) -> str:
        self.calls.append((system_instruction, prompt, schema))
        output = self.outputs[len(self.calls) - 1]
        if isinstance(output, Exception):
            raise output
        return output


def as_json(recommendation_set: RecommendationSet) -> str:
    return recommendation_set.model_dump_json()


async def write(generator: ScriptedGenerator, reports: list[DeviceReportData]) -> RecommendationSet:
    return await RecommendationWriter(generator).write(
        URL, Platform.WORDPRESS, Language.ENGLISH, reports
    )


def test_prompt_contains_platform_scores_and_findings() -> None:
    reports = [sample_report(Device.MOBILE, 41), sample_report(Device.DESKTOP, 88)]

    audit_data = json.loads(build_prompt(URL, Platform.SHOPIFY, reports).split("\n", 1)[1])

    assert audit_data["url"] == URL
    assert audit_data["platform"] == "shopify"
    assert [report["performance_score"] for report in audit_data["reports"]] == [41, 88]
    assert audit_data["reports"][0]["findings"][0]["lighthouse_id"] == "render-blocking-resources"


def test_prompt_strips_markdown_links_from_descriptions() -> None:
    description = "Defer offscreen images. [Learn more](https://developer.chrome.com/docs/x)."
    prompt = build_prompt(
        URL, Platform.UNKNOWN, [report_with([finding("offscreen-images", description)])]
    )

    assert "Defer offscreen images. Learn more." in prompt
    assert "developer.chrome.com" not in prompt


def test_prompt_limits_findings_per_device() -> None:
    findings = [finding(f"audit-{index}") for index in range(MAX_FINDINGS_PER_DEVICE + 5)]

    prompt = build_prompt(URL, Platform.UNKNOWN, [report_with(findings)])

    assert f"audit-{MAX_FINDINGS_PER_DEVICE - 1}" in prompt
    assert f'"audit-{MAX_FINDINGS_PER_DEVICE}"' not in prompt


@pytest.mark.parametrize(
    ("language", "expected"),
    [
        (Language.BOSNIAN, "Bosnian (bosanski jezik)"),
        (Language.ENGLISH, "Write all text in English"),
    ],
)
def test_system_instruction_names_the_output_language(language: Language, expected: str) -> None:
    assert expected in build_system_instruction(language)


def test_schema_mirrors_the_recommendation_models() -> None:
    schema = recommendation_schema(["unused-css"])
    item = schema["properties"]["recommendations"]["items"]

    assert set(schema["required"]) == set(RecommendationSet.model_fields)
    assert set(item["required"]) == set(RecommendationDraft.model_fields)
    assert item["properties"]["impact"]["enum"] == [impact.value for impact in Impact]
    assert item["properties"]["effort"]["enum"] == [effort.value for effort in Effort]
    assert item["properties"]["devices"]["items"]["enum"] == [device.value for device in Device]


def test_schema_only_allows_known_lighthouse_ids() -> None:
    schema = recommendation_schema(["unused-css", "render-blocking-resources"])
    item = schema["properties"]["recommendations"]["items"]

    assert item["properties"]["lighthouse_ids"]["items"]["enum"] == [
        "unused-css",
        "render-blocking-resources",
    ]


async def test_writer_returns_the_validated_recommendations() -> None:
    expected = sample_recommendation_set()
    generator = ScriptedGenerator([as_json(expected)])

    assert await write(generator, [sample_report(Device.MOBILE)]) == expected


async def test_writer_sends_each_finding_id_once_in_the_schema() -> None:
    generator = ScriptedGenerator([as_json(sample_recommendation_set())])

    await write(generator, [sample_report(Device.MOBILE), sample_report(Device.DESKTOP)])

    [(_, _, schema)] = generator.calls
    item = schema["properties"]["recommendations"]["items"]
    assert item["properties"]["lighthouse_ids"]["items"]["enum"] == ["render-blocking-resources"]


async def test_writer_drops_lighthouse_ids_that_were_not_in_the_audit() -> None:
    invented = sample_recommendation_set(["render-blocking-resources", "made-up-audit"])
    generator = ScriptedGenerator([as_json(invented)])

    result = await write(generator, [sample_report(Device.MOBILE)])

    assert result.recommendations[0].lighthouse_ids == ["render-blocking-resources"]


@pytest.mark.parametrize(
    "first_failure",
    [
        "not json at all",
        '{"summary": "Missing recommendations"}',
        '{"summary": "x", "recommendations": [{"title": "No other fields"}]}',
        GeminiError("HTTP 503"),
    ],
)
async def test_writer_retries_once_after_a_bad_attempt(first_failure: str | Exception) -> None:
    expected = sample_recommendation_set()
    generator = ScriptedGenerator([first_failure, as_json(expected)])

    assert await write(generator, [sample_report(Device.MOBILE)]) == expected
    assert len(generator.calls) == MAX_ATTEMPTS


async def test_writer_gives_up_after_two_bad_attempts() -> None:
    generator = ScriptedGenerator(["{}", GeminiError("HTTP 500")])

    with pytest.raises(RecommendationsUnavailableError):
        await write(generator, [sample_report(Device.MOBILE)])
