import type { Impact } from "@/lib/api/schemas";
import type { Tone } from "@/lib/report/tone";

export const TONE_TEXT: Record<Tone, string> = {
  good: "text-good",
  needsWork: "text-needs-work",
  poor: "text-poor",
};

export const TONE_BADGE: Record<Tone, string> = {
  good: "bg-good-soft text-good",
  needsWork: "bg-needs-work-soft text-needs-work-strong",
  poor: "bg-poor-soft text-poor",
};

export const IMPACT_BADGE: Record<Impact, string> = {
  high: TONE_BADGE.poor,
  medium: TONE_BADGE.needsWork,
  low: "bg-slate-100 text-slate-700",
};
