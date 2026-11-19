from pydantic import BaseModel, ConfigDict, Field


class PageSpeedApiModel(BaseModel):
    model_config = ConfigDict(frozen=True)


class LighthouseAuditDetails(PageSpeedApiModel):
    overall_savings_ms: float | None = Field(default=None, alias="overallSavingsMs")
    overall_savings_bytes: float | None = Field(default=None, alias="overallSavingsBytes")


class LighthouseAudit(PageSpeedApiModel):
    id: str
    title: str
    description: str = ""
    score: float | None = None
    score_display_mode: str = Field(default="", alias="scoreDisplayMode")
    display_value: str | None = Field(default=None, alias="displayValue")
    numeric_value: float | None = Field(default=None, alias="numericValue")
    metric_savings: dict[str, float] | None = Field(default=None, alias="metricSavings")
    details: LighthouseAuditDetails | None = None


class PerformanceCategory(PageSpeedApiModel):
    score: float | None = None


class LighthouseCategories(PageSpeedApiModel):
    performance: PerformanceCategory


class LighthouseRuntimeError(PageSpeedApiModel):
    code: str
    message: str = ""


class LighthouseResult(PageSpeedApiModel):
    categories: LighthouseCategories
    audits: dict[str, LighthouseAudit]
    runtime_error: LighthouseRuntimeError | None = Field(default=None, alias="runtimeError")


class PageSpeedResponse(PageSpeedApiModel):
    lighthouse_result: LighthouseResult = Field(alias="lighthouseResult")


class PageSpeedErrorDetail(PageSpeedApiModel):
    message: str = ""


class PageSpeedErrorResponse(PageSpeedApiModel):
    error: PageSpeedErrorDetail
