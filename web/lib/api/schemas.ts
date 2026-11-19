import { z } from "zod";

export const devices = ["mobile", "desktop"] as const;
export const platforms = [
  "wordpress",
  "shopify",
  "wix",
  "squarespace",
  "webflow",
  "joomla",
  "drupal",
  "nextjs",
  "nuxt",
  "unknown",
] as const;
export const failureReasons = [
  "queue_unavailable",
  "site_unreachable",
  "pagespeed_quota_exceeded",
  "pagespeed_unavailable",
  "recommendations_unavailable",
  "internal_error",
] as const;

const score = z.number().int().min(0).max(100);
const deviceSchema = z.enum(devices);

const findingSchema = z.object({
  lighthouse_id: z.string(),
  title: z.string(),
  description: z.string(),
  score: z.number(),
  display_value: z.string().nullable(),
  savings_ms: z.number().nullable(),
  savings_bytes: z.number().nullable(),
});

const deviceReportSchema = z.object({
  device: deviceSchema,
  performance_score: score,
  accessibility_score: score.nullable(),
  best_practices_score: score.nullable(),
  seo_score: score.nullable(),
  first_contentful_paint_ms: z.number().nullable(),
  largest_contentful_paint_ms: z.number().nullable(),
  total_blocking_time_ms: z.number().nullable(),
  cumulative_layout_shift: z.number().nullable(),
  speed_index_ms: z.number().nullable(),
  findings: z.array(findingSchema),
});

const recommendationSchema = z.object({
  rank: z.number().int().positive(),
  title: z.string(),
  explanation: z.string(),
  steps: z.array(z.string()),
  impact: z.enum(["high", "medium", "low"]),
  effort: z.enum(["low", "medium", "high"]),
  devices: z.array(deviceSchema),
  lighthouse_ids: z.array(z.string()),
});

export const auditSchema = z.object({
  id: z.uuid(),
  url: z.string(),
  language: z.enum(["bs", "en"]),
  status: z.enum(["queued", "running", "completed", "failed"]),
  failure_reason: z.enum(failureReasons).nullable(),
  platform: z.enum(platforms).nullable(),
  summary: z.string().nullable(),
  created_at: z.iso.datetime({ offset: true }),
  updated_at: z.iso.datetime({ offset: true }),
  reports: z.array(deviceReportSchema),
  recommendations: z.array(recommendationSchema),
});

const auditStatusSchema = auditSchema.shape.status;

const siteCheckSchema = z.object({
  audit_id: z.uuid(),
  checked_at: z.iso.datetime({ offset: true }),
  platform: z.enum(platforms).nullable(),
  mobile_performance_score: score.nullable(),
  desktop_performance_score: score.nullable(),
});

export const siteSchema = z.object({
  id: z.uuid(),
  url: z.string(),
  created_at: z.iso.datetime({ offset: true }),
  latest_audit: z.object({ audit_id: z.uuid(), status: auditStatusSchema }).nullable(),
  checks: z.array(siteCheckSchema),
});

export const sitesSchema = z.array(siteSchema);

export type Audit = z.infer<typeof auditSchema>;
export type Site = z.infer<typeof siteSchema>;
export type SiteCheck = z.infer<typeof siteCheckSchema>;
export type DeviceReport = z.infer<typeof deviceReportSchema>;
export type Recommendation = z.infer<typeof recommendationSchema>;
export type Device = z.infer<typeof deviceSchema>;
export type Platform = (typeof platforms)[number];
export type FailureReason = (typeof failureReasons)[number];
export type Impact = Recommendation["impact"];
