import { z } from "zod";

const apiUrlSchema = z.url({ protocol: /^https?$/ });

const CLIENT_IP_HEADER = "X-SpeedCoach-Client-IP";
const PROXY_SECRET_HEADER = "X-SpeedCoach-Proxy-Secret";

export const TOO_MANY_REQUESTS = 429;

export function apiUrl(path: string): string {
  const baseUrl = apiUrlSchema.parse(process.env.API_URL);
  return new URL(path, baseUrl).toString();
}

export function proxyHeaders(clientIp: string | null): Record<string, string> {
  const secret = process.env.WEB_PROXY_SECRET;
  if (!secret || !clientIp) return {};
  return { [CLIENT_IP_HEADER]: clientIp, [PROXY_SECRET_HEADER]: secret };
}
