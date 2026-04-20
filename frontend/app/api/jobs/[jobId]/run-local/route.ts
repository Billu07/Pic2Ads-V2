import { NextResponse } from "next/server";

import { siteConfig } from "@/lib/site";

type Params = { params: Promise<{ jobId: string }> };

export async function POST(_: Request, { params }: Params) {
  const { jobId } = await params;
  const response = await fetch(
    `${siteConfig.apiBaseUrl}/jobs/${encodeURIComponent(jobId)}/pipeline/run-local`,
    {
      method: "POST",
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
