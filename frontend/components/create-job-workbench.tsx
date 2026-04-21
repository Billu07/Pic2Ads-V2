"use client";

import Link from "next/link";
import { ChangeEvent, DragEvent, FormEvent, useCallback, useEffect, useMemo, useState } from "react";

import {
  approveTvStoryboard,
  CreativeCtaStyle,
  CreativeHookStyle,
  CreativeOfferAngle,
  createJob,
  CreateJobMode,
  DeliverableAspect,
  JobLanguage,
  generateTvConcepts,
  generateTvStoryboard,
  getTvGateStatus,
  getTvStoryboard,
  JobCreatedResponse,
  LocalPipelineResponse,
  listTvConcepts,
  MediaUploadResponse,
  runScripts,
  runLocalPipeline,
  ScriptVariant,
  selectTvConcept,
  TvConcept,
  TvGateStatus,
  TvStoryboardShot,
  uploadProductImage,
} from "@/lib/api";

type FormState = {
  mode: CreateJobMode;
  language: JobLanguage;
  duration_s: number;
  product_name: string;
  product_image_url: string;
  brief: string;
  brand_id: string;
  aspect: DeliverableAspect;
  deliverable_duration: number;
  auto_run_local: boolean;
  creative_tone: string;
  hook_style: CreativeHookStyle;
  offer_angle: CreativeOfferAngle;
  cta_style: CreativeCtaStyle;
  must_include_csv: string;
  must_avoid_csv: string;
  generate_audio: boolean;
};

type RecentJobEntry = {
  id: string;
  mode: CreateJobMode;
  created_at: string;
  last_pipeline_status: string | null;
};

const RECENT_JOBS_STORAGE_KEY = "pic2ads_recent_jobs_v1";
const MAX_RECENT_JOBS = 12;

const MODE_PRESETS: Record<CreateJobMode, { label: string; duration: number; note: string }> = {
  ugc: {
    label: "Mode A - UGC",
    duration: 15,
    note: "Fast single-shot output for paid social testing loops.",
  },
  pro_arc: {
    label: "Mode B - Professional UGC",
    duration: 30,
    note: "Narrative creator-style ads with optional extend continuity.",
  },
  tv: {
    label: "Mode C - TV Commercial",
    duration: 30,
    note: "Multi-shot render planning for polished campaign cuts.",
  },
};

const CREATIVE_PRESETS: Record<
  CreateJobMode,
  {
    tone: string;
    hook_style: CreativeHookStyle;
    offer_angle: CreativeOfferAngle;
    cta_style: CreativeCtaStyle;
  }
> = {
  ugc: {
    tone: "raw and relatable",
    hook_style: "demo_first",
    offer_angle: "speed_convenience",
    cta_style: "soft_invite",
  },
  pro_arc: {
    tone: "cinematic but grounded",
    hook_style: "storytime_confession",
    offer_angle: "emotional_relief",
    cta_style: "question_prompt",
  },
  tv: {
    tone: "premium narrative clarity",
    hook_style: "problem_first",
    offer_angle: "performance_proof",
    cta_style: "direct_command",
  },
};

const HOOK_STYLE_OPTIONS: Array<{ value: CreativeHookStyle; label: string }> = [
  { value: "problem_first", label: "Problem First" },
  { value: "social_proof", label: "Social Proof" },
  { value: "demo_first", label: "Demo First" },
  { value: "storytime_confession", label: "Storytime Confession" },
  { value: "authority_insight", label: "Authority Insight" },
];

const OFFER_ANGLE_OPTIONS: Array<{ value: CreativeOfferAngle; label: string }> = [
  { value: "speed_convenience", label: "Speed & Convenience" },
  { value: "premium_quality", label: "Premium Quality" },
  { value: "value_savings", label: "Value Savings" },
  { value: "emotional_relief", label: "Emotional Relief" },
  { value: "performance_proof", label: "Performance Proof" },
];

const CTA_STYLE_OPTIONS: Array<{ value: CreativeCtaStyle; label: string }> = [
  { value: "soft_invite", label: "Soft Invite" },
  { value: "direct_command", label: "Direct Command" },
  { value: "question_prompt", label: "Question Prompt" },
  { value: "urgency_push", label: "Urgency Push" },
];

const LANGUAGE_OPTIONS: Array<{ value: JobLanguage; label: string }> = [
  { value: "en", label: "English" },
  { value: "bn", label: "Bengali" },
  { value: "hi", label: "Hindi" },
  { value: "es", label: "Spanish" },
];

function summarizeError(error: unknown): string {
  if (!(error instanceof Error)) {
    return "Unexpected request failure.";
  }
  try {
    const parsed = JSON.parse(error.message) as { detail?: string };
    if (parsed.detail) {
      return parsed.detail;
    }
  } catch {
    return error.message;
  }
  return error.message;
}

function parseCsvList(input: string): string[] {
  return input
    .split(",")
    .map((item) => item.trim())
    .filter((item, index, list) => item.length > 0 && list.indexOf(item) === index)
    .slice(0, 6);
}

function formatRecentTimeLabel(iso: string): string {
  const dt = new Date(iso);
  if (Number.isNaN(dt.getTime())) {
    return "unknown time";
  }
  return dt.toLocaleString([], {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function CreateJobWorkbench() {
  const [form, setForm] = useState<FormState>({
    mode: "ugc",
    language: "en",
    duration_s: MODE_PRESETS.ugc.duration,
    product_name: "",
    product_image_url: "",
    brief: "",
    brand_id: "",
    aspect: "9:16",
    deliverable_duration: 15,
    auto_run_local: true,
    creative_tone: CREATIVE_PRESETS.ugc.tone,
    hook_style: CREATIVE_PRESETS.ugc.hook_style,
    offer_angle: CREATIVE_PRESETS.ugc.offer_angle,
    cta_style: CREATIVE_PRESETS.ugc.cta_style,
    must_include_csv: "",
    must_avoid_csv: "",
    generate_audio: true,
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [isTvBusy, setIsTvBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [createdJob, setCreatedJob] = useState<JobCreatedResponse | null>(null);
  const [pipelineResult, setPipelineResult] = useState<LocalPipelineResponse | null>(null);
  const [tvGateState, setTvGateState] = useState<TvGateStatus | null>(null);
  const [tvConcepts, setTvConcepts] = useState<TvConcept[]>([]);
  const [tvStoryboardShots, setTvStoryboardShots] = useState<TvStoryboardShot[]>([]);
  const [scriptVariants, setScriptVariants] = useState<ScriptVariant[]>([]);
  const [selectedVariantId, setSelectedVariantId] = useState<string>("");
  const [recentJobs, setRecentJobs] = useState<RecentJobEntry[]>([]);
  const [isVariantModalOpen, setIsVariantModalOpen] = useState(false);
  const [modalVariantId, setModalVariantId] = useState<string>("");
  const [shouldAutoRunAfterVariantSelect, setShouldAutoRunAfterVariantSelect] = useState(false);

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isDraggingFile, setIsDraggingFile] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadResult, setUploadResult] = useState<MediaUploadResponse | null>(null);
  const [localPreviewUrl, setLocalPreviewUrl] = useState<string | null>(null);

  const modePreset = useMemo(() => MODE_PRESETS[form.mode], [form.mode]);

  useEffect(() => {
    if (!selectedFile) {
      setLocalPreviewUrl(null);
      return;
    }
    const objectUrl = URL.createObjectURL(selectedFile);
    setLocalPreviewUrl(objectUrl);
    return () => URL.revokeObjectURL(objectUrl);
  }, [selectedFile]);

  useEffect(() => {
    try {
      const raw = window.localStorage.getItem(RECENT_JOBS_STORAGE_KEY);
      if (!raw) {
        return;
      }
      const parsed = JSON.parse(raw) as unknown;
      if (!Array.isArray(parsed)) {
        return;
      }
      const normalized = parsed
        .map((item) => {
          if (
            !item ||
            typeof item !== "object" ||
            typeof (item as { id?: unknown }).id !== "string" ||
            typeof (item as { mode?: unknown }).mode !== "string" ||
            typeof (item as { created_at?: unknown }).created_at !== "string"
          ) {
            return null;
          }
          const mode = (item as { mode: string }).mode;
          if (mode !== "ugc" && mode !== "pro_arc" && mode !== "tv") {
            return null;
          }
          const lastPipelineRaw = (item as { last_pipeline_status?: unknown }).last_pipeline_status;
          const lastPipeline =
            typeof lastPipelineRaw === "string" ? lastPipelineRaw : lastPipelineRaw === null ? null : null;
          return {
            id: (item as { id: string }).id,
            mode,
            created_at: (item as { created_at: string }).created_at,
            last_pipeline_status: lastPipeline,
          } satisfies RecentJobEntry;
        })
        .filter((item): item is RecentJobEntry => item !== null)
        .slice(0, MAX_RECENT_JOBS);
      setRecentJobs(normalized);
    } catch {
      setRecentJobs([]);
    }
  }, []);

  const upsertRecentJob = useCallback(
    (entry: RecentJobEntry) => {
      setRecentJobs((prev) => {
        const deduped = [entry, ...prev.filter((item) => item.id !== entry.id)].slice(0, MAX_RECENT_JOBS);
        try {
          window.localStorage.setItem(RECENT_JOBS_STORAGE_KEY, JSON.stringify(deduped));
        } catch {
          // Ignore localStorage write failures.
        }
        return deduped;
      });
    },
    []
  );

  const updateRecentJobStatus = useCallback((jobId: string, status: string) => {
    setRecentJobs((prev) => {
      const next = prev.map((item) =>
        item.id === jobId ? { ...item, last_pipeline_status: status } : item
      );
      try {
        window.localStorage.setItem(RECENT_JOBS_STORAGE_KEY, JSON.stringify(next));
      } catch {
        // Ignore localStorage write failures.
      }
      return next;
    });
  }, []);

  function setMode(mode: CreateJobMode) {
    const preset = MODE_PRESETS[mode];
    const creativePreset = CREATIVE_PRESETS[mode];
    setForm((prev) => ({
      ...prev,
      mode,
      duration_s: preset.duration,
      deliverable_duration: Math.min(preset.duration, 30),
      creative_tone: creativePreset.tone,
      hook_style: creativePreset.hook_style,
      offer_angle: creativePreset.offer_angle,
      cta_style: creativePreset.cta_style,
    }));
  }

  const refreshTvWorkflow = useCallback(async (jobId: string) => {
    const [gate, concepts, storyboard] = await Promise.all([
      getTvGateStatus(jobId),
      listTvConcepts(jobId),
      getTvStoryboard(jobId),
    ]);
    setTvGateState(gate);
    setTvConcepts(concepts.concepts);
    setTvStoryboardShots(storyboard.shots);
  }, []);

  useEffect(() => {
    if (!createdJob || createdJob.mode !== "tv") {
      setTvGateState(null);
      setTvConcepts([]);
      setTvStoryboardShots([]);
      return;
    }
    refreshTvWorkflow(createdJob.id).catch(() => {});
  }, [createdJob, refreshTvWorkflow]);

  async function handleRunScripts(jobId: string): Promise<string | null> {
    const scriptRun = await runScripts(jobId);
    const variants = scriptRun.output.scripts ?? [];
    setScriptVariants(variants);
    if (variants.length > 0) {
      const firstId = variants[0].variant_id;
      setSelectedVariantId((prev) => prev || firstId);
      return firstId;
    }
    return null;
  }

  function openVariantSelectionModal(autoRunAfterSelect: boolean, preferredVariantId?: string) {
    const fallback = (preferredVariantId || selectedVariantId || scriptVariants[0]?.variant_id || "").trim();
    if (!fallback) {
      setError("No script variants available yet. Generate scripts first.");
      return;
    }
    setModalVariantId(fallback);
    setShouldAutoRunAfterVariantSelect(autoRunAfterSelect);
    setIsVariantModalOpen(true);
  }

  async function executePipeline(job: JobCreatedResponse, variantIdOverride?: string) {
    const selectedForRun =
      job.mode === "ugc" ? (variantIdOverride || selectedVariantId || "").trim() : undefined;
    if (job.mode === "ugc" && !selectedForRun) {
      setError("Select one script variant before rendering.");
      return;
    }

    setError(null);
    setIsRunning(true);
    try {
      const runResult = await runLocalPipeline(job.id, {
        generate_audio: form.generate_audio,
        render_all_variants: job.mode === "ugc" ? false : true,
        selected_variant_id: job.mode === "ugc" ? selectedForRun : undefined,
      });
      setPipelineResult(runResult);
      updateRecentJobStatus(job.id, runResult.video_generate_status);
    } catch (runError) {
      setError(summarizeError(runError));
    } finally {
      setIsRunning(false);
    }
  }

  async function confirmVariantSelection() {
    const chosenVariantId = (modalVariantId || scriptVariants[0]?.variant_id || "").trim();
    if (!chosenVariantId) {
      setError("Select a script variant to continue.");
      return;
    }

    setSelectedVariantId(chosenVariantId);
    setIsVariantModalOpen(false);

    const shouldRun = shouldAutoRunAfterVariantSelect;
    setShouldAutoRunAfterVariantSelect(false);
    if (shouldRun && createdJob) {
      await executePipeline(createdJob, chosenVariantId);
    }
  }

  async function handleGenerateTvConcepts() {
    if (!createdJob) {
      return;
    }
    setError(null);
    setIsTvBusy(true);
    try {
      const generated = await generateTvConcepts(createdJob.id);
      setTvConcepts(generated.concepts);
      await refreshTvWorkflow(createdJob.id);
    } catch (tvError) {
      setError(summarizeError(tvError));
    } finally {
      setIsTvBusy(false);
    }
  }

  async function handleSelectTvConcept(conceptId: string) {
    if (!createdJob) {
      return;
    }
    setError(null);
    setIsTvBusy(true);
    try {
      await selectTvConcept(createdJob.id, conceptId);
      await refreshTvWorkflow(createdJob.id);
    } catch (tvError) {
      setError(summarizeError(tvError));
    } finally {
      setIsTvBusy(false);
    }
  }

  async function handleGenerateTvStoryboard() {
    if (!createdJob) {
      return;
    }
    setError(null);
    setIsTvBusy(true);
    try {
      const generated = await generateTvStoryboard(createdJob.id);
      setTvStoryboardShots(generated.shots);
      await refreshTvWorkflow(createdJob.id);
    } catch (tvError) {
      setError(summarizeError(tvError));
    } finally {
      setIsTvBusy(false);
    }
  }

  async function handleApproveTvStoryboard(approved: boolean) {
    if (!createdJob) {
      return;
    }
    setError(null);
    setIsTvBusy(true);
    try {
      await approveTvStoryboard(createdJob.id, approved);
      await refreshTvWorkflow(createdJob.id);
    } catch (tvError) {
      setError(summarizeError(tvError));
    } finally {
      setIsTvBusy(false);
    }
  }

  async function handleUpload() {
    if (!selectedFile) {
      setUploadError("Select an image file first.");
      return null;
    }
    setUploadError(null);
    setUploadResult(null);
    setUploadProgress(0);
    setIsUploading(true);
    try {
      const uploaded = await uploadProductImage(selectedFile, {
        onProgress: (percent) => setUploadProgress(percent),
      });
      setUploadResult(uploaded);
      setForm((prev) => ({ ...prev, product_image_url: uploaded.url }));
      setUploadProgress(100);
      return uploaded.url;
    } catch (uploadFailure) {
      setUploadError(summarizeError(uploadFailure));
      return null;
    } finally {
      setIsUploading(false);
    }
  }

  function handleFilePicked(file: File | null) {
    setSelectedFile(file);
    setUploadError(null);
    setUploadResult(null);
    setUploadProgress(0);
  }

  function onFileInputChange(event: ChangeEvent<HTMLInputElement>) {
    handleFilePicked(event.currentTarget.files?.[0] ?? null);
  }

  function onDropFile(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setIsDraggingFile(false);
    const dropped = event.dataTransfer.files?.[0];
    if (!dropped) {
      return;
    }
    handleFilePicked(dropped);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setCreatedJob(null);
    setPipelineResult(null);
    setTvGateState(null);
    setTvConcepts([]);
    setTvStoryboardShots([]);
    setScriptVariants([]);
    setSelectedVariantId("");
    setModalVariantId("");
    setIsVariantModalOpen(false);
    setShouldAutoRunAfterVariantSelect(false);

    let resolvedImageUrl = form.product_image_url.trim();
    if (!resolvedImageUrl && selectedFile) {
      const uploadedUrl = await handleUpload();
      if (!uploadedUrl) {
        setError("Image upload failed. Please retry or paste a public image URL.");
        return;
      }
      resolvedImageUrl = uploadedUrl;
    }
    try {
      new URL(resolvedImageUrl);
    } catch {
      setError("Provide a valid product image URL (or select a file before creating).");
      return;
    }

    if (!form.product_name.trim()) {
      setError("Product name is required.");
      return;
    }

    setIsSubmitting(true);
    try {
      const mustInclude = parseCsvList(form.must_include_csv);
      const mustAvoid = parseCsvList(form.must_avoid_csv);
      const payload = {
        mode: form.mode,
        language: form.language,
        duration_s: form.duration_s,
        product: {
          product_name: form.product_name.trim(),
          product_image_url: resolvedImageUrl,
        },
        deliverables: [{ aspect: form.aspect, duration: form.deliverable_duration }],
        brief: form.brief.trim() || undefined,
        brand_id: form.brand_id.trim() || undefined,
        creative_decisions: {
          tone: form.creative_tone.trim() || undefined,
          hook_style: form.hook_style,
          offer_angle: form.offer_angle,
          cta_style: form.cta_style,
          must_include: mustInclude.length > 0 ? mustInclude : undefined,
          must_avoid: mustAvoid.length > 0 ? mustAvoid : undefined,
        },
      };

      const created = await createJob(payload);
      setCreatedJob(created);
      upsertRecentJob({
        id: created.id,
        mode: created.mode,
        created_at: new Date().toISOString(),
        last_pipeline_status: null,
      });
      const firstVariantId = await handleRunScripts(created.id);
      if (created.mode === "tv") {
        await refreshTvWorkflow(created.id);
      }

      if (created.mode === "ugc") {
        if (!firstVariantId) {
          setError("Script generation returned no variants for UGC mode.");
          return;
        }
        setSelectedVariantId(firstVariantId);
        openVariantSelectionModal(form.auto_run_local, firstVariantId);
        return;
      }

      if (form.auto_run_local) {
        await executePipeline(created);
      }
    } catch (submitError) {
      setError(summarizeError(submitError));
    } finally {
      setIsSubmitting(false);
    }
  }

  async function triggerPipeline() {
    if (!createdJob) {
      return;
    }

    if (createdJob.mode === "ugc") {
      if (scriptVariants.length === 0) {
        try {
          const firstVariantId = await handleRunScripts(createdJob.id);
          if (!firstVariantId) {
            setError("Script generation returned no variants for UGC mode.");
            return;
          }
          openVariantSelectionModal(true, firstVariantId);
        } catch (scriptError) {
          setError(summarizeError(scriptError));
        }
        return;
      }
      openVariantSelectionModal(true);
      return;
    }

    await executePipeline(createdJob);
  }

  return (
    <div className="workspace">
      <section className="panel panel-main reveal">
        <p className="eyebrow">Creative Workspace</p>
        <h2 className="panel-heading">Build your next job</h2>
        <p className="caption">{modePreset.note}</p>

        <div className="mode-switch">
          {(["ugc", "pro_arc", "tv"] as const).map((mode) => (
            <button
              type="button"
              key={mode}
              className={`mode-chip ${form.mode === mode ? "active" : ""}`}
              onClick={() => setMode(mode)}
            >
              {MODE_PRESETS[mode].label}
            </button>
          ))}
        </div>

        <form onSubmit={handleSubmit} className="job-form">
          <div className="field-grid">
            <div className="field">
              <label htmlFor="language">Language</label>
              <select
                id="language"
                className="select"
                value={form.language}
                onChange={(event) =>
                  setForm((prev) => ({ ...prev, language: event.target.value as JobLanguage }))
                }
              >
                {LANGUAGE_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="field">
              <label htmlFor="product_name">Product Name</label>
              <input
                id="product_name"
                className="input"
                value={form.product_name}
                onChange={(event) => setForm((prev) => ({ ...prev, product_name: event.target.value }))}
                placeholder="Glow Tonic Serum"
                required
              />
            </div>
            <div className="field">
              <label htmlFor="product_image_url">Product Image URL</label>
              <input
                id="product_image_url"
                className="input"
                value={form.product_image_url}
                onChange={(event) =>
                  setForm((prev) => ({ ...prev, product_image_url: event.target.value }))
                }
                placeholder="https://..."
              />
            </div>

            <div className="field field-full">
              <label htmlFor="product_upload">Or Upload Product Image</label>
              <div
                className={`dropzone ${isDraggingFile ? "active" : ""}`}
                onDragEnter={(event) => {
                  event.preventDefault();
                  setIsDraggingFile(true);
                }}
                onDragOver={(event) => {
                  event.preventDefault();
                  setIsDraggingFile(true);
                }}
                onDragLeave={(event) => {
                  event.preventDefault();
                  setIsDraggingFile(false);
                }}
                onDrop={onDropFile}
              >
                Drag and drop an image here, or choose a file.
              </div>
              <div className="upload-row">
                <input
                  id="product_upload"
                  type="file"
                  accept="image/png,image/jpeg,image/webp,image/gif"
                  className="input"
                  onChange={onFileInputChange}
                />
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={handleUpload}
                  disabled={isUploading || !selectedFile}
                >
                  {isUploading ? "Uploading..." : "Upload"}
                </button>
              </div>
              {isUploading && (
                <div className="upload-progress">
                  <div className="upload-progress-fill" style={{ width: `${uploadProgress}%` }} />
                </div>
              )}
              <p className="hint">
                Requires frontend server env: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, and
                storage bucket.
              </p>
              {uploadError && <p className="hint">Upload error: {uploadError}</p>}
              {uploadResult && (
                <p className="hint">
                  Uploaded to `{uploadResult.bucket}` at `{uploadResult.path}`.
                </p>
              )}
              {(localPreviewUrl || form.product_image_url) && (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={localPreviewUrl ?? form.product_image_url}
                  alt="Product preview"
                  className="product-preview"
                  loading="lazy"
                />
              )}
            </div>

            <div className="field">
              <label htmlFor="duration_s">Ad Duration (seconds)</label>
              <input
                id="duration_s"
                type="number"
                min={10}
                max={60}
                className="input"
                value={form.duration_s}
                onChange={(event) =>
                  setForm((prev) => ({ ...prev, duration_s: Number(event.target.value || 0) }))
                }
              />
            </div>
            <div className="field">
              <label htmlFor="aspect">Deliverable Aspect</label>
              <select
                id="aspect"
                className="select"
                value={form.aspect}
                onChange={(event) =>
                  setForm((prev) => ({ ...prev, aspect: event.target.value as DeliverableAspect }))
                }
              >
                <option value="9:16">9:16 (Reels/TikTok)</option>
                <option value="1:1">1:1 (Feed)</option>
                <option value="16:9">16:9 (YouTube/Landing)</option>
              </select>
            </div>

            <div className="field">
              <label htmlFor="deliverable_duration">Deliverable Duration</label>
              <input
                id="deliverable_duration"
                type="number"
                min={6}
                max={60}
                className="input"
                value={form.deliverable_duration}
                onChange={(event) =>
                  setForm((prev) => ({
                    ...prev,
                    deliverable_duration: Number(event.target.value || 0),
                  }))
                }
              />
            </div>
            <div className="field">
              <label htmlFor="brand_id">Brand ID (optional)</label>
              <input
                id="brand_id"
                className="input"
                value={form.brand_id}
                onChange={(event) => setForm((prev) => ({ ...prev, brand_id: event.target.value }))}
                placeholder="brand_internal_001"
              />
            </div>

            <div className="field field-full">
              <label htmlFor="brief">Creative Brief (optional)</label>
              <textarea
                id="brief"
                className="textarea"
                value={form.brief}
                onChange={(event) => setForm((prev) => ({ ...prev, brief: event.target.value }))}
                placeholder="Audience, value proposition, mood, and CTA preferences."
              />
            </div>

            <div className="field">
              <label htmlFor="creative_tone">Creative Tone</label>
              <input
                id="creative_tone"
                className="input"
                value={form.creative_tone}
                onChange={(event) =>
                  setForm((prev) => ({ ...prev, creative_tone: event.target.value }))
                }
                placeholder="raw and relatable"
              />
            </div>
            <div className="field">
              <label htmlFor="hook_style">Hook Style</label>
              <select
                id="hook_style"
                className="select"
                value={form.hook_style}
                onChange={(event) =>
                  setForm((prev) => ({
                    ...prev,
                    hook_style: event.target.value as CreativeHookStyle,
                  }))
                }
              >
                {HOOK_STYLE_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="field">
              <label htmlFor="offer_angle">Offer Angle</label>
              <select
                id="offer_angle"
                className="select"
                value={form.offer_angle}
                onChange={(event) =>
                  setForm((prev) => ({
                    ...prev,
                    offer_angle: event.target.value as CreativeOfferAngle,
                  }))
                }
              >
                {OFFER_ANGLE_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label htmlFor="cta_style">CTA Style</label>
              <select
                id="cta_style"
                className="select"
                value={form.cta_style}
                onChange={(event) =>
                  setForm((prev) => ({
                    ...prev,
                    cta_style: event.target.value as CreativeCtaStyle,
                  }))
                }
              >
                {CTA_STYLE_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="field">
              <label htmlFor="must_include_csv">Must Include (comma separated)</label>
              <input
                id="must_include_csv"
                className="input"
                value={form.must_include_csv}
                onChange={(event) =>
                  setForm((prev) => ({ ...prev, must_include_csv: event.target.value }))
                }
                placeholder="natural handheld cadence, one tactile product beat"
              />
            </div>
            <div className="field">
              <label htmlFor="must_avoid_csv">Must Avoid (comma separated)</label>
              <input
                id="must_avoid_csv"
                className="input"
                value={form.must_avoid_csv}
                onChange={(event) =>
                  setForm((prev) => ({ ...prev, must_avoid_csv: event.target.value }))
                }
                placeholder="over-polished ad language, fake urgency"
              />
            </div>
          </div>

          <label className="inline-toggle">
            <input
              type="checkbox"
              checked={form.auto_run_local}
              onChange={(event) =>
                setForm((prev) => ({ ...prev, auto_run_local: event.target.checked }))
              }
            />
            Auto-run pipeline after script selection
          </label>
          <label className="inline-toggle">
            <input
              type="checkbox"
              checked={form.generate_audio}
              onChange={(event) =>
                setForm((prev) => ({ ...prev, generate_audio: event.target.checked }))
              }
            />
            Generate audio (default on)
          </label>

          <div className="cta-row form-actions">
            <button
              type="submit"
              className="btn btn-accent"
              disabled={isSubmitting || isRunning || isUploading}
            >
              {isSubmitting ? "Creating..." : "Create Job"}
            </button>
            {createdJob && (
              <button
                type="button"
                className="btn btn-secondary"
                onClick={triggerPipeline}
                disabled={isUploading}
              >
                {isRunning ? "Running..." : "Run Pipeline"}
              </button>
            )}
          </div>

          {error && <p className="hint">Error: {error}</p>}
        </form>
      </section>

      <aside className="panel panel-side reveal delay-1">
        <p className="eyebrow">Run State</p>
        <h3 className="panel-subheading">Production Snapshot</h3>
        <p className="caption">
          This workspace initializes a backend job and optionally starts the local pipeline runner.
        </p>

        <div className="status-box">
          <p className="status-title">Mode</p>
          <p className="caption status-copy">
            {modePreset.label}
          </p>
        </div>

        <div className="status-box">
          <p className="status-title">Job Creation</p>
          <p className="caption status-copy">
            {createdJob ? `Created: ${createdJob.id}` : "Awaiting submit"}
          </p>
          {createdJob && (
            <div className="cta-row compact-actions">
              <Link href={`/jobs/${createdJob.id}`} className="btn btn-primary">
                Open Manifest
              </Link>
            </div>
          )}
        </div>

        <div className="status-box">
          <p className="status-title">Pipeline</p>
          <p className="caption status-copy">
            {pipelineResult
              ? `Video status: ${pipelineResult.video_generate_status}`
              : isRunning
                ? "Running local pipeline..."
                : "Not started"}
          </p>
          {pipelineResult && (
            <p className="hint status-hint">
              Intel: {pipelineResult.product_intel_status} | Brand:{" "}
              {pipelineResult.brand_strategy_status} | Casting: {pipelineResult.casting_status} |
              Scripts: {pipelineResult.script_status} | TV gates: {pipelineResult.tv_gate_status} |
              Duration plan: {pipelineResult.duration_plan_status}
            </p>
          )}
        </div>

        <div className="status-box">
          <p className="status-title">Recent Jobs</p>
          <p className="caption status-copy">
            {recentJobs.length > 0
              ? "Track previous renders from here, even after starting a new job."
              : "No previous jobs yet. Create one and it will appear here."}
          </p>
          {recentJobs.length > 0 && (
            <div className="tv-list-block">
              <div className="tv-list">
                {recentJobs.map((job) => (
                  <div key={job.id} className="tv-item">
                    <p className="tv-item-title">{job.id}</p>
                    <p className="hint">
                      Mode: {job.mode} | {formatRecentTimeLabel(job.created_at)}
                    </p>
                    <p className="hint">
                      {job.last_pipeline_status ? `Last: ${job.last_pipeline_status}` : "Last: pending run"}
                    </p>
                    <div className="cta-row compact-actions">
                      <Link href={`/jobs/${job.id}`} className="btn btn-secondary">
                        Open Manifest
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {createdJob && (
          <div className="status-box">
            <p className="status-title">Script Review</p>
            <p className="caption status-copy">
              {scriptVariants.length > 0
                ? `${scriptVariants.length} script variants ready`
                : "Generate scripts to choose a render direction"}
            </p>
            <div className="cta-row compact-actions">
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => handleRunScripts(createdJob.id)}
                disabled={isSubmitting || isRunning}
              >
                Refresh Scripts
              </button>
              {createdJob.mode === "ugc" && scriptVariants.length > 0 && (
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={() => openVariantSelectionModal(false)}
                  disabled={isSubmitting || isRunning}
                >
                  Open Script Selector
                </button>
              )}
            </div>

            {scriptVariants.length > 0 && (
              <div className="tv-list-block">
                <div className="tv-list">
                  {scriptVariants.map((variant) => (
                    <div key={variant.variant_id} className="tv-item">
                      <p className="tv-item-title">{variant.variant_id}</p>
                      <p className="hint">{variant.hook}</p>
                      <button
                        type="button"
                        className="btn btn-secondary"
                        onClick={() => {
                          setSelectedVariantId(variant.variant_id);
                          setModalVariantId(variant.variant_id);
                        }}
                        disabled={createdJob.mode !== "ugc"}
                      >
                        {selectedVariantId === variant.variant_id ? "Selected" : "Select Script"}
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
            {createdJob.mode === "ugc" && (
              <p className="hint">
                UGC submits one selected variant only: `{selectedVariantId || scriptVariants[0]?.variant_id || "none"}`.
              </p>
            )}
          </div>
        )}

        {createdJob?.mode === "tv" && (
          <div className="status-box">
            <p className="status-title">TV Gate Flow</p>
            <p className="caption status-copy">
              {tvGateState
                ? `Ready for render: ${tvGateState.ready_for_render ? "yes" : "no"}`
                : "Loading TV workflow status..."}
            </p>

            <div className="tv-gate-grid">
              <span className={`status-pill ${tvGateState?.concept_selected ? "is-ok" : "is-pending"}`}>
                Concept: {tvGateState?.concept_selected ? "selected" : "pending"}
              </span>
              <span
                className={`status-pill ${tvGateState?.storyboard_generated ? "is-ok" : "is-pending"}`}
              >
                Storyboard: {tvGateState?.storyboard_generated ? "generated" : "pending"}
              </span>
              <span
                className={`status-pill ${tvGateState?.storyboard_approved ? "is-ok" : "is-pending"}`}
              >
                Approval: {tvGateState?.storyboard_approved ? "approved" : "pending"}
              </span>
            </div>

            <div className="cta-row compact-actions">
              <button
                type="button"
                className="btn btn-secondary"
                onClick={handleGenerateTvConcepts}
                disabled={isTvBusy}
              >
                {isTvBusy ? "Working..." : "Generate Concepts"}
              </button>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={handleGenerateTvStoryboard}
                disabled={isTvBusy || !tvGateState?.concept_selected}
              >
                {isTvBusy ? "Working..." : "Generate Storyboard"}
              </button>
              <button
                type="button"
                className="btn btn-primary"
                onClick={() => handleApproveTvStoryboard(true)}
                disabled={isTvBusy || !tvGateState?.storyboard_generated}
              >
                Approve Storyboard
              </button>
            </div>

            {tvConcepts.length > 0 && (
              <div className="tv-list-block">
                <p className="status-title">
                  Concepts
                </p>
                <div className="tv-list">
                  {tvConcepts.map((concept) => (
                    <div key={concept.concept_id} className="tv-item">
                      <p className="tv-item-title">{concept.title}</p>
                      <p className="hint">{concept.logline}</p>
                      <button
                        type="button"
                        className="btn btn-secondary"
                        onClick={() => handleSelectTvConcept(concept.concept_id)}
                        disabled={isTvBusy}
                      >
                        {tvGateState?.selected_concept_id === concept.concept_id
                          ? "Selected"
                          : "Select Concept"}
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {tvStoryboardShots.length > 0 && (
              <div className="tv-list-block">
                <p className="status-title">
                  Storyboard Shots
                </p>
                <div className="tv-list">
                  {tvStoryboardShots.map((shot) => (
                    <div key={shot.shot_id} className="tv-item">
                      <p className="tv-item-title">
                        {shot.shot_id} - {shot.duration_s}s
                      </p>
                      <p className="hint">{shot.purpose}</p>
                    </div>
                  ))}
                </div>
                <div className="cta-row compact-actions">
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={() => handleApproveTvStoryboard(false)}
                    disabled={isTvBusy}
                  >
                    Unapprove
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </aside>

      {isVariantModalOpen && createdJob?.mode === "ugc" && (
        <div className="variant-modal-overlay" role="presentation">
          <div className="variant-modal" role="dialog" aria-modal="true" aria-labelledby="ugc-variant-title">
            <div className="variant-modal-head">
              <p className="eyebrow">UGC Script Selection</p>
              <h3 id="ugc-variant-title" className="panel-subheading">
                Choose one script before rendering
              </h3>
              <p className="caption">
                Fal submission is blocked until a script is selected. Only one variant is submitted per run.
              </p>
            </div>

            <div className="variant-option-list">
              {scriptVariants.map((variant) => {
                const active = modalVariantId === variant.variant_id;
                return (
                  <button
                    type="button"
                    key={variant.variant_id}
                    className={`variant-option ${active ? "active" : ""}`}
                    onClick={() => setModalVariantId(variant.variant_id)}
                  >
                    <p className="variant-option-title">{variant.variant_id}</p>
                    <p className="variant-option-copy">{variant.hook}</p>
                    <p className="hint">
                      Angle: {variant.angle} | Setting: {variant.setting} | Tone: {variant.tone}
                    </p>
                  </button>
                );
              })}
            </div>

            <div className="cta-row compact-actions">
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => {
                  setIsVariantModalOpen(false);
                  setShouldAutoRunAfterVariantSelect(false);
                }}
              >
                Close
              </button>
              <button type="button" className="btn btn-accent" onClick={confirmVariantSelection}>
                Select Script
                {shouldAutoRunAfterVariantSelect ? " & Render" : ""}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
