from typing import Any

METRIC_AUDITS: dict[str, dict[str, Any]] = {
    "first-contentful-paint": {"numericValue": 1800.5, "score": 0.8},
    "largest-contentful-paint": {"numericValue": 4200.0, "score": 0.3},
    "total-blocking-time": {"numericValue": 350.0, "score": 0.6},
    "cumulative-layout-shift": {"numericValue": 0.12, "score": 0.7},
    "speed-index": {"numericValue": 3900.0, "score": 0.5},
    "interactive": {"numericValue": 7000.0, "score": 0.4},
}

FINDING_AUDITS: dict[str, dict[str, Any]] = {
    "unused-javascript": {
        "score": 0.5,
        "scoreDisplayMode": "metricSavings",
        "displayValue": "Est savings of 180 KiB",
        "metricSavings": {"LCP": 300, "FCP": 0},
        "details": {"type": "opportunity", "overallSavingsMs": 300, "overallSavingsBytes": 184320},
    },
    "render-blocking-resources": {
        "score": 0,
        "scoreDisplayMode": "metricSavings",
        "displayValue": "Est savings of 1,200 ms",
        "metricSavings": {"LCP": 1200, "FCP": 900},
        "details": {"type": "opportunity", "overallSavingsMs": 1200},
    },
    "uses-long-cache-ttl": {
        "score": 0.4,
        "scoreDisplayMode": "numeric",
        "displayValue": "12 resources found",
    },
    "uses-http2": {"score": 1, "scoreDisplayMode": "binary"},
    "diagnostics": {"score": None, "scoreDisplayMode": "informative"},
    "uses-rel-preconnect": {"score": None, "scoreDisplayMode": "notApplicable"},
}


def _audit(audit_id: str, fields: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": audit_id,
        "title": f"Title for {audit_id}",
        "description": f"Description for {audit_id}",
        "scoreDisplayMode": "numeric",
        **fields,
    }


def lighthouse_payload(
    score: float | None = 0.42, runtime_error: dict[str, str] | None = None
) -> dict[str, Any]:
    audits = {
        audit_id: _audit(audit_id, fields)
        for audit_id, fields in {**METRIC_AUDITS, **FINDING_AUDITS}.items()
    }
    lighthouse_result: dict[str, Any] = {
        "lighthouseVersion": "12.8.2",
        "categories": {"performance": {"id": "performance", "score": score}},
        "audits": audits,
    }
    if runtime_error is not None:
        lighthouse_result["runtimeError"] = runtime_error
    return {"id": "https://example.com/", "lighthouseResult": lighthouse_result}
