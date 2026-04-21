import { NextRequest, NextResponse } from "next/server";

import { siteConfig } from "@/lib/site";

export async function GET(request: NextRequest) {
  const search = request.nextUrl.searchParams;
  const limit = search.get("limit") ?? "24";
  const offset = search.get("offset") ?? "0";
  const response = await fetch(
    `${siteConfig.apiBaseUrl}/jobs?limit=${encodeURIComponent(limit)}&offset=${encodeURIComponent(offset)}`,
    {
      method: "GET",
      cache: "no-store",
    }
  );

  const contentType = response.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    const body = await response.json();
    return NextResponse.json(body, { status: response.status });
  }

  const text = await response.text();
  return new NextResponse(text, { status: response.status });
}

export async function POST(request: NextRequest) {
  let payload: unknown;
  try {
    payload = await request.json();
  } catch {
    return NextResponse.json({ detail: "invalid_json" }, { status: 400 });
  }

  const response = await fetch(`${siteConfig.apiBaseUrl}/jobs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    cache: "no-store",
  });

  const contentType = response.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    const body = await response.json();
    return NextResponse.json(body, { status: response.status });
  }

  const text = await response.text();
  return new NextResponse(text, { status: response.status });
}
