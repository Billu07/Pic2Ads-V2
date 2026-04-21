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
export type JobLanguage = "en" | "bn" | "hi" | "es";
export type DeliverableAspect = "9:16" | "1:1" | "16:9";
export type CreativeHookStyle =
  | "problem_first"
  | "social_proof"
  | "demo_first"
  | "storytime_confession"
  | "authority_insight";
export type CreativeOfferAngle =
  | "speed_convenience"
  | "premium_quality"
  | "value_savings"
  | "emotional_relief"
  | "performance_proof";
export type CreativeCtaStyle =
  | "soft_invite"
  | "direct_command"
  | "question_prompt"
  | "urgency_push";

export type CreativeDecisionsPayload = {
  tone?: string;
  hook_style?: CreativeHookStyle;
  offer_angle?: CreativeOfferAngle;
  cta_style?: CreativeCtaStyle;
  must_include?: string[];
  must_avoid?: string[];
};

export type CreateJobPayload = {
  mode: CreateJobMode;
  language: JobLanguage;
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
  creative_decisions?: CreativeDecisionsPayload;
};

export type JobCreatedResponse = {
  id: string;
  status: string;
  mode: CreateJobMode;
  duration_s: number;
};

export type JobListItem = {
  id: string;
  status: string;
  mode: CreateJobMode;
  duration_s: number;
  created_at: string;
};

export type JobListResponse = {
  items: JobListItem[];
  total: number;
  limit: number;
  offset: number;
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

export type RunLocalPipelinePayload = {
  generate_audio?: boolean;
  render_all_variants?: boolean;
  selected_variant_id?: string;
};

export type ScriptVariant = {
  variant_id: string;
  angle: string;
  setting: string;
  tone: string;
  filming_method: string;
  first_frame_description: string;
  product_feature_focus: string;
  hook: string;
  render_pattern_hint: string;
  segment_count_hint: number | null;
  authenticity_markers: string[];
};

export type ScriptRunResponse = {
  job_id: string;
  cached: boolean;
  agent_name: string;
  prompt_version: string;
  output: {
    mode: CreateJobMode;
    scripts: ScriptVariant[];
  };
};

export type TvGateStatus = {
  job_id: string;
  required: boolean;
  concept_selected: boolean;
  selected_concept_id: string | null;
  storyboard_generated: boolean;
  storyboard_approved: boolean;
  ready_for_render: boolean;
};

export type TvConcept = {
  concept_id: string;
  title: string;
  logline: string;
  treatment: string;
  audience_angle: string;
  style_notes: string[];
};

export type TvConceptListResponse = {
  job_id: string;
  generated: boolean;
  concepts: TvConcept[];
};

export type TvConceptGenerateResponse = {
  job_id: string;
  cached: boolean;
  concepts: TvConcept[];
};

export type TvConceptSelectResponse = {
  job_id: string;
  concept_id: string;
  concept_selected: boolean;
  storyboard_generated: boolean;
  storyboard_approved: boolean;
  ready_for_render: boolean;
};

export type TvStoryboardShot = {
  shot_id: string;
  sequence: number;
  duration_s: number;
  purpose: string;
  visual_description: string;
  camera_intent: string;
  transition_in: "opening" | "hard_cut" | "extend_from_previous";
};

export type TvStoryboardListResponse = {
  job_id: string;
  concept_id: string | null;
  generated: boolean;
  shots: TvStoryboardShot[];
};

export type TvStoryboardGenerateResponse = {
  job_id: string;
  concept_id: string;
  cached: boolean;
  shots: TvStoryboardShot[];
};

export type TvStoryboardApproveResponse = {
  job_id: string;
  storyboard_generated: boolean;
  storyboard_approved: boolean;
  concept_selected: boolean;
  ready_for_render: boolean;
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

export async function listJobs(limit = 24, offset = 0): Promise<JobListResponse> {
  const response = await fetch(`/api/jobs?limit=${limit}&offset=${offset}`, {
    cache: "no-store",
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `list_jobs_failed_${response.status}`);
  }
  return (await response.json()) as JobListResponse;
}

export async function runLocalPipeline(
  jobId: string,
  payload?: RunLocalPipelinePayload
): Promise<LocalPipelineResponse> {
  const response = await fetch(`/api/jobs/${encodeURIComponent(jobId)}/run-local`, {
    method: "POST",
    headers: payload ? { "Content-Type": "application/json" } : undefined,
    body: payload ? JSON.stringify(payload) : undefined,
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `run_pipeline_failed_${response.status}`);
  }

  return (await response.json()) as LocalPipelineResponse;
}

export async function runScripts(jobId: string): Promise<ScriptRunResponse> {
  const response = await fetch(`/api/jobs/${encodeURIComponent(jobId)}/scripts`, {
    method: "POST",
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `run_scripts_failed_${response.status}`);
  }

  return (await response.json()) as ScriptRunResponse;
}

export async function getTvGateStatus(jobId: string): Promise<TvGateStatus> {
  const response = await fetch(`/api/jobs/${encodeURIComponent(jobId)}/tv/gates`, {
    cache: "no-store",
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `tv_gates_fetch_failed_${response.status}`);
  }
  return (await response.json()) as TvGateStatus;
}

export async function generateTvConcepts(jobId: string): Promise<TvConceptGenerateResponse> {
  const response = await fetch(`/api/jobs/${encodeURIComponent(jobId)}/concepts/generate`, {
    method: "POST",
  });
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `tv_concepts_generate_failed_${response.status}`);
  }
  return (await response.json()) as TvConceptGenerateResponse;
}

export async function listTvConcepts(jobId: string): Promise<TvConceptListResponse> {
  const response = await fetch(`/api/jobs/${encodeURIComponent(jobId)}/concepts`, {
    cache: "no-store",
  });
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `tv_concepts_list_failed_${response.status}`);
  }
  return (await response.json()) as TvConceptListResponse;
}

export async function selectTvConcept(
  jobId: string,
  conceptId: string
): Promise<TvConceptSelectResponse> {
  const response = await fetch(`/api/jobs/${encodeURIComponent(jobId)}/concepts/select`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ concept_id: conceptId }),
  });
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `tv_concept_select_failed_${response.status}`);
  }
  return (await response.json()) as TvConceptSelectResponse;
}

export async function generateTvStoryboard(jobId: string): Promise<TvStoryboardGenerateResponse> {
  const response = await fetch(`/api/jobs/${encodeURIComponent(jobId)}/storyboard/generate`, {
    method: "POST",
  });
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `tv_storyboard_generate_failed_${response.status}`);
  }
  return (await response.json()) as TvStoryboardGenerateResponse;
}

export async function getTvStoryboard(jobId: string): Promise<TvStoryboardListResponse> {
  const response = await fetch(`/api/jobs/${encodeURIComponent(jobId)}/storyboard`, {
    cache: "no-store",
  });
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `tv_storyboard_fetch_failed_${response.status}`);
  }
  return (await response.json()) as TvStoryboardListResponse;
}

export async function approveTvStoryboard(
  jobId: string,
  approved: boolean
): Promise<TvStoryboardApproveResponse> {
  const response = await fetch(`/api/jobs/${encodeURIComponent(jobId)}/storyboard/approve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ approved }),
  });
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `tv_storyboard_approve_failed_${response.status}`);
  }
  return (await response.json()) as TvStoryboardApproveResponse;
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
