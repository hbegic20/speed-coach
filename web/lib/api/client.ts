import { z } from "zod";

const apiUrlSchema = z.url({ protocol: /^https?$/ });

export function apiUrl(path: string): string {
  const baseUrl = apiUrlSchema.parse(process.env.API_URL);
  return new URL(path, baseUrl).toString();
}
