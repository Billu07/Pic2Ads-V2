import { randomUUID } from "crypto";
import { NextResponse } from "next/server";

export const runtime = "nodejs";

const MAX_UPLOAD_BYTES = 15 * 1024 * 1024;

function inferExtension(fileName: string, contentType: string): string {
  const fromName = fileName.split(".").pop()?.toLowerCase();
  if (fromName && /^[a-z0-9]+$/.test(fromName)) {
    return fromName;
  }

  if (contentType === "image/jpeg") return "jpg";
  if (contentType === "image/png") return "png";
  if (contentType === "image/webp") return "webp";
  if (contentType === "image/gif") return "gif";
  return "bin";
}

export async function POST(request: Request) {
  const supabaseUrl = process.env.SUPABASE_URL;
  const serviceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY;
  const bucket = process.env.SUPABASE_STORAGE_BUCKET ?? "product-images";

  if (!supabaseUrl || !serviceRoleKey) {
    return NextResponse.json(
      {
        detail: "storage_not_configured_set_SUPABASE_URL_and_SUPABASE_SERVICE_ROLE_KEY",
      },
      { status: 503 }
    );
  }

  const formData = await request.formData();
  const maybeFile = formData.get("file");
  if (!(maybeFile instanceof File)) {
    return NextResponse.json({ detail: "file_required" }, { status: 400 });
  }
  if (maybeFile.size <= 0) {
    return NextResponse.json({ detail: "file_empty" }, { status: 400 });
  }
  if (maybeFile.size > MAX_UPLOAD_BYTES) {
    return NextResponse.json({ detail: "file_too_large_max_15mb" }, { status: 413 });
  }

  const contentType = maybeFile.type || "application/octet-stream";
  const extension = inferExtension(maybeFile.name, contentType);
  const datePrefix = new Date().toISOString().slice(0, 10);
  const objectPath = `uploads/${datePrefix}/${randomUUID()}.${extension}`;
  const objectUrl = `${supabaseUrl.replace(/\/+$/, "")}/storage/v1/object/${bucket}/${objectPath}`;

  const bytes = await maybeFile.arrayBuffer();
  const uploadResponse = await fetch(objectUrl, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${serviceRoleKey}`,
      apikey: serviceRoleKey,
      "content-type": contentType,
      "x-upsert": "false",
    },
    body: Buffer.from(bytes),
    cache: "no-store",
  });

  if (!uploadResponse.ok) {
    const detail = await uploadResponse.text();
    return NextResponse.json(
      { detail: detail || `supabase_upload_failed_${uploadResponse.status}` },
      { status: 502 }
    );
  }

  const publicBase =
    process.env.SUPABASE_STORAGE_PUBLIC_URL?.replace(/\/+$/, "") ??
    `${supabaseUrl.replace(/\/+$/, "")}/storage/v1/object/public`;
  const publicUrl = `${publicBase}/${bucket}/${objectPath}`;

  return NextResponse.json({
    url: publicUrl,
    path: objectPath,
    bucket,
    content_type: contentType,
    size: maybeFile.size,
  });
}
