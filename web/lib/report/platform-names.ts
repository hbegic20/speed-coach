import type { Platform } from "@/lib/api/schemas";

const PLATFORM_NAMES: Record<Exclude<Platform, "unknown">, string> = {
  wordpress: "WordPress",
  shopify: "Shopify",
  wix: "Wix",
  squarespace: "Squarespace",
  webflow: "Webflow",
  joomla: "Joomla",
  drupal: "Drupal",
  nextjs: "Next.js",
  nuxt: "Nuxt",
};

export function platformName(platform: Platform | null): string | null {
  if (platform === null || platform === "unknown") return null;
  return PLATFORM_NAMES[platform];
}
