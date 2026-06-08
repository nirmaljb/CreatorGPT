import { NextResponse } from "next/server";

import { backendApiBase } from "../../../../lib/apiBase";

async function backendFailureReason(response: Response) {
  try {
    const body = (await response.json()) as { detail?: unknown };
    return typeof body.detail === "string" ? body.detail : null;
  } catch {
    return null;
  }
}

export async function GET(request: Request) {
  const fallbackUrl = new URL("/", request.url);
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
    // The home page will also show the unavailable connection status from /api/me.
    fallbackUrl.searchParams.set("reason", "OAuth service is unreachable.");
  }

  return NextResponse.redirect(fallbackUrl, 303);
}
