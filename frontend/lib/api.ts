import { siteConfig } from "@/lib/site";

export type ExportSegment = {
  unit_id: number;
  unit_sequence: number;
  unit_pattern: string;
  segment_id: number;
  segment_order: number;
  duration_s: number;
  status: string;
  prompt_seed: string | null;
  output_video_url: string | null;
  output_last_frame_url: string | null;
  ready: boolean;
};

export type ExportManifest = {
  job_id: string;
  status: "empty" | "incomplete" | "ready";
  total_units: number;
  total_segments: number;
  ready_segments: number;
  missing_segments: number;
  total_duration_s: number;
  ready_duration_s: number;
  timeline: ExportSegment[];
};

export type CreateJobMode = "ugc" | "pro_arc" | "tv";
export type DeliverableAspect = "9:16" | "1:1" | "16:9";

export type CreateJobPayload = {
  mode: CreateJobMode;
  duration_s: number;
  product: {
    product_name: string;
    product_image_url: string;
  };
  deliverables: Array<{
    aspect: DeliverableAspect;
    duration: number;
  }>;
  brand_id?: string;
  brief?: string;
};

export type JobCreatedResponse = {
  id: string;
  status: string;
  mode: CreateJobMode;
  duration_s: number;
};

export type LocalPipelineResponse = {
  job_id: string;
  product_intel_status: string;
  brand_strategy_status: string;
  casting_status: string;
  script_status: string;
  tv_gate_status: string;
  duration_plan_status: string;
  video_generate_status: string;
};

export type MediaUploadResponse = {
  url: string;
  path: string;
  bucket: string;
  content_type: string;
  size: number;
};

export async function getExportManifest(jobId: string): Promise<ExportManifest | null> {
  const url = `${siteConfig.apiBaseUrl}/jobs/${encodeURIComponent(jobId)}/export/manifest`;
  const response = await fetch(url, { cache: "no-store" });

  if (response.status === 404) {
    return null;
  }
  if (!response.ok) {
    throw new Error(`manifest_fetch_failed_${response.status}`);
  }

  return (await response.json()) as ExportManifest;
}

export async function createJob(payload: CreateJobPayload): Promise<JobCreatedResponse> {
  const response = await fetch("/api/jobs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `create_job_failed_${response.status}`);
  }

  return (await response.json()) as JobCreatedResponse;
}

export async function runLocalPipeline(jobId: string): Promise<LocalPipelineResponse> {
  const response = await fetch(`/api/jobs/${encodeURIComponent(jobId)}/run-local`, {
    method: "POST",
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `run_pipeline_failed_${response.status}`);
  }

  return (await response.json()) as LocalPipelineResponse;
}

export function uploadProductImage(
  file: File,
  opts?: { onProgress?: (percent: number) => void }
): Promise<MediaUploadResponse> {
  return new Promise((resolve, reject) => {
    const formData = new FormData();
    formData.append("file", file);

    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/api/media/upload");

    xhr.upload.onprogress = (event) => {
      if (!opts?.onProgress || !event.lengthComputable) {
        return;
      }
      const percent = Math.max(0, Math.min(100, Math.round((event.loaded / event.total) * 100)));
      opts.onProgress(percent);
    };

    xhr.onerror = () => reject(new Error("media_upload_network_error"));
    xhr.onabort = () => reject(new Error("media_upload_aborted"));
    xhr.onload = () => {
      const text = xhr.responseText || "";
      if (xhr.status < 200 || xhr.status >= 300) {
        reject(new Error(text || `media_upload_failed_${xhr.status}`));
        return;
      }
      try {
        resolve(JSON.parse(text) as MediaUploadResponse);
      } catch {
        reject(new Error("media_upload_invalid_json"));
      }
    };

    xhr.send(formData);
  });
}
