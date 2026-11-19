import { headers } from "next/headers";

export function firstForwardedAddress(forwardedFor: string | null): string | null {
  const first = forwardedFor?.split(",")[0]?.trim();
  return first ? first : null;
}

export async function requestClientIp(): Promise<string | null> {
  const requestHeaders = await headers();
  return (
    firstForwardedAddress(requestHeaders.get("x-forwarded-for")) ??
    requestHeaders.get("x-real-ip")
  );
}
