import { randomBytes } from "node:crypto";
import { cookies } from "next/headers";

const OWNER_COOKIE = "speedcoach_owner";
const OWNER_TOKEN_PATTERN = /^[A-Za-z0-9_-]{43}$/;
const OWNER_TOKEN_BYTES = 32;
const MAX_COOKIE_AGE_SECONDS = 400 * 24 * 60 * 60;

export function isOwnerToken(value: string | undefined): value is string {
  return value !== undefined && OWNER_TOKEN_PATTERN.test(value);
}

export async function readOwnerToken(): Promise<string | null> {
  const value = (await cookies()).get(OWNER_COOKIE)?.value;
  return isOwnerToken(value) ? value : null;
}

export async function ensureOwnerToken(): Promise<string> {
  const existing = await readOwnerToken();
  if (existing) return existing;

  const token = randomBytes(OWNER_TOKEN_BYTES).toString("base64url");
  (await cookies()).set(OWNER_COOKIE, token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: MAX_COOKIE_AGE_SECONDS,
  });
  return token;
}
