import { z } from "zod";
import { normalizeUrlInput } from "@/lib/report/normalize-url";

const MAX_URL_LENGTH = 2048;

export const websiteUrlSchema = z
  .string()
  .max(MAX_URL_LENGTH)
  .transform(normalizeUrlInput)
  .pipe(z.url({ protocol: /^https?$/, hostname: z.regexes.domain }));
