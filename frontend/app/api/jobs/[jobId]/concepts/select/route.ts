import { NextResponse } from "next/server";

import { siteConfig } from "@/lib/site";

type Params = { params: Promise<{ jobId: string }> };

export async function POST(request: Request, { params }: Params) {
  const { jobId } = await params;

  let payload: unknown;
  try {
    payload = await request.json();
  } catch {
    return NextResponse.json({ detail: "invalid_json" }, { status: 400 });
  }

  const response = await fetch(
    `${siteConfig.apiBaseUrl}/jobs/${encodeURIComponent(jobId)}/concepts/select`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
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
