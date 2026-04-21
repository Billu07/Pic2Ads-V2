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
  runLocalPipeline,
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
};

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
      if (created.mode === "tv") {
        await refreshTvWorkflow(created.id);
      }

      if (form.auto_run_local) {
        setIsRunning(true);
        try {
          const runResult = await runLocalPipeline(created.id);
          setPipelineResult(runResult);
        } finally {
          setIsRunning(false);
        }
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
    setError(null);
    setIsRunning(true);
    try {
      const runResult = await runLocalPipeline(createdJob.id);
      setPipelineResult(runResult);
    } catch (runError) {
      setError(summarizeError(runError));
    } finally {
      setIsRunning(false);
    }
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
            Auto-run local pipeline after creation
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
    </div>
  );
}
