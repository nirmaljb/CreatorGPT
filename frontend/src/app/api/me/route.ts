import { NextResponse } from "next/server";

import { backendApiBase } from "../../../lib/apiBase";

export async function GET(request: Request) {
  try {
    const response = await fetch(`${backendApiBase()}/me`, {
      cache: "no-store",
      headers: {
        cookie: request.headers.get("cookie") || ""
      }
    });

    return new Response(await response.text(), {
      headers: {
        "Cache-Control": response.headers.get("cache-control") || "no-store",
        "Content-Type": response.headers.get("content-type") || "application/json"
      },
      status: response.status
    });
  } catch {
    return NextResponse.json({ detail: "Connection status is unavailable." }, { status: 503 });
  }
}
