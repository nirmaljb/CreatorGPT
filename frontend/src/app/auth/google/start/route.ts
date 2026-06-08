import { NextResponse } from "next/server";

import { backendApiBase } from "../../../../lib/apiBase";

const ALLOWED_FALLBACK_PATHS = new Set(["/auth", "/login"]);

async function backendFailureReason(response: Response) {
  try {
    const body = (await response.json()) as { detail?: unknown };
    return typeof body.detail === "string" ? body.detail : null;
  } catch {
    return null;
  }
}

function fallbackPathFromRequest(request: Request) {
  const url = new URL(request.url);
  const returnTo = url.searchParams.get("returnTo") || "/auth";
  return ALLOWED_FALLBACK_PATHS.has(returnTo) ? returnTo : "/auth";
}

export async function GET(request: Request) {
  const fallbackUrl = new URL(fallbackPathFromRequest(request), request.url);
  fallbackUrl.searchParams.set("auth", "unavailable");

  try {
    const response = await fetch(`${backendApiBase()}/auth/google/start`, {
      cache: "no-store",
      redirect: "manual"
    });
    const location = response.headers.get("location");

    if (response.status >= 300 && response.status < 400 && location) {
      return NextResponse.redirect(location, 302);
    }
    const reason = await backendFailureReason(response);
    if (reason) fallbackUrl.searchParams.set("reason", reason);
  } catch {
    // The initiating page owns safe consent-start failure messaging.
    fallbackUrl.searchParams.set("reason", "OAuth service is unreachable.");
  }

  return NextResponse.redirect(fallbackUrl, 303);
}
