import type { Audit, DeviceReport, Recommendation } from "@/lib/api/schemas";

export function deviceReport(overrides: Partial<DeviceReport> = {}): DeviceReport {
  return {
    device: "mobile",
    performance_score: 42,
    accessibility_score: 78,
    best_practices_score: 83,
    seo_score: 91,
    first_contentful_paint_ms: 1800,
    largest_contentful_paint_ms: 4800,
    total_blocking_time_ms: 180,
    cumulative_layout_shift: 0.21,
    speed_index_ms: 3900,
    findings: [
      {
        lighthouse_id: "render-blocking-resources",
        title: "Eliminate render-blocking resources",
        description: "Resources are blocking the first paint.",
        score: 0,
        display_value: "Est savings of 1,200 ms",
        savings_ms: 1200,
        savings_bytes: null,
      },
      {
        lighthouse_id: "uses-long-cache-ttl",
        title: "Serve static assets with an efficient cache policy",
        description: "A long cache lifetime can speed up repeat visits.",
        score: 0.4,
        display_value: "12 resources found",
        savings_ms: null,
        savings_bytes: null,
      },
    ],
    ...overrides,
  };
}

export function recommendation(overrides: Partial<Recommendation> = {}): Recommendation {
  return {
    rank: 1,
    title: "Load scripts after the page appears",
    explanation: "Scripts in the page header delay the first paint on phones.",
    steps: ["Install a caching plugin", "Enable 'Delay JavaScript execution'"],
    impact: "high",
    effort: "low",
    devices: ["mobile", "desktop"],
    lighthouse_ids: ["render-blocking-resources"],
    ...overrides,
  };
}

export function audit(overrides: Partial<Audit> = {}): Audit {
  return {
    id: "6f1c2a8e-3b4d-4c5e-9f60-7a8b9c0d1e2f",
    url: "https://www.example-restaurant.ba/",
    language: "en",
    status: "completed",
    failure_reason: null,
    platform: "wordpress",
    summary: "Your site loads slowly on phones. Start with render-blocking files.",
    created_at: "2026-11-19T09:14:00Z",
    updated_at: "2026-11-19T09:15:10Z",
    reports: [deviceReport(), deviceReport({ device: "desktop", performance_score: 88 })],
    recommendations: [
      recommendation(),
      recommendation({
        rank: 2,
        title: "Set long cache times",
        impact: "low",
        lighthouse_ids: ["uses-long-cache-ttl"],
      }),
    ],
    ...overrides,
  };
}
