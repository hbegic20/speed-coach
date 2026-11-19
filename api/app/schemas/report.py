from pydantic import BaseModel, ConfigDict, Field

from app.models.device_report import Device


class Finding(BaseModel):
    lighthouse_id: str
    title: str
    description: str
    score: float = Field(ge=0, le=1)
    display_value: str | None
    savings_ms: float | None
    savings_bytes: float | None


class DeviceReportData(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    device: Device
    performance_score: int = Field(ge=0, le=100)
    first_contentful_paint_ms: float | None
    largest_contentful_paint_ms: float | None
    total_blocking_time_ms: float | None
    cumulative_layout_shift: float | None
    speed_index_ms: float | None
    findings: list[Finding]
