import { NextResponse, type NextRequest } from "next/server";
import { pathnameHasLocale } from "@/lib/i18n/locales";
import { negotiateLocale } from "@/lib/i18n/negotiate-locale";

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  if (pathnameHasLocale(pathname)) return NextResponse.next();

  const locale = negotiateLocale(request.headers.get("accept-language"));
  request.nextUrl.pathname = pathname === "/" ? `/${locale}` : `/${locale}${pathname}`;
  return NextResponse.redirect(request.nextUrl);
}

export const config = {
  matcher: ["/((?!_next|favicon.ico).*)"],
};
