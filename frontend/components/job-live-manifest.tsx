"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import type { ExportManifest } from "@/lib/api";

type JobLiveManifestProps = {
  jobId: string;
  initialManifest: ExportManifest;
};

type ManifestTab = "progress" | "outputs";

function formatTimeLabel(iso: string): string {
  const dt = new Date(iso);
  if (Number.isNaN(dt.getTime())) {
    return "just now";
  }
  return dt.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export function JobLiveManifest({ jobId, initialManifest }: JobLiveManifestProps) {
  const [manifest, setManifest] = useState<ExportManifest>(initialManifest);
  const [activeTab, setActiveTab] = useState<ManifestTab>("progress");
  const [lastUpdatedAt, setLastUpdatedAt] = useState<string>(new Date().toISOString());
  const [error, setError] = useState<string | null>(null);

  const refreshManifest = useCallback(async () => {
    const response = await fetch(`/api/jobs/${encodeURIComponent(jobId)}/export/manifest`, {
      method: "GET",
      cache: "no-store",
    });
    const text = await response.text();
    if (!response.ok) {
      throw new Error(text || `manifest_fetch_failed_${response.status}`);
    }
    const parsed = JSON.parse(text) as ExportManifest;
    setManifest(parsed);
    setLastUpdatedAt(new Date().toISOString());
    setError(null);
    return parsed;
  }, [jobId]);

  useEffect(() => {
    let cancelled = false;
    let timeoutRef: ReturnType<typeof setTimeout> | null = null;

    const loop = async () => {
      try {
        const next = await refreshManifest();
        if (cancelled) {
          return;
        }
        const delay = next.status === "ready" ? 15000 : 4000;
        timeoutRef = setTimeout(loop, delay);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "manifest_refresh_failed");
          timeoutRef = setTimeout(loop, 6000);
        }
      }
    };

    timeoutRef = setTimeout(loop, 4000);
    return () => {
      cancelled = true;
      if (timeoutRef) {
        clearTimeout(timeoutRef);
      }
    };
  }, [refreshManifest]);

  const completionPct = useMemo(() => {
    if (manifest.total_segments <= 0) {
      return 0;
    }
    return Math.round((manifest.ready_segments / manifest.total_segments) * 100);
  }, [manifest.ready_segments, manifest.total_segments]);

  const completedSegments = useMemo(
    () => manifest.timeline.filter((segment) => segment.ready && Boolean(segment.output_video_url)),
    [manifest.timeline]
  );

  return (
    <div className="panel job-live-shell">
      <div className="job-live-head">
        <div>
          <p className="eyebrow">Render Manifest</p>
          <h1 className="job-live-title">Job {manifest.job_id}</h1>
          <p className="caption job-live-subline">
            Live tracking enabled. Last updated at {formatTimeLabel(lastUpdatedAt)}.
          </p>
        </div>
        <div className="job-live-head-meta">
          <span className={`status-pill ${manifest.status === "ready" ? "is-ok" : "is-pending"}`}>
            Status: {manifest.status}
          </span>
          <button type="button" className="btn btn-secondary" onClick={() => refreshManifest()}>
            Refresh
          </button>
        </div>
      </div>

      {error ? <p className="hint">Refresh warning: {error}</p> : null}

      <div className="job-tabs">
        <button
          type="button"
          className={`job-tab ${activeTab === "progress" ? "active" : ""}`}
          onClick={() => setActiveTab("progress")}
        >
          Live Progress
        </button>
        <button
          type="button"
          className={`job-tab ${activeTab === "outputs" ? "active" : ""}`}
          onClick={() => setActiveTab("outputs")}
        >
          Output Preview
        </button>
      </div>

      {activeTab === "progress" ? (
        <section className="job-pane">
          <div className="job-progress-card">
            <div className="job-progress-row">
              <p className="status-title">Overall Completion</p>
              <p className="caption status-copy">{completionPct}%</p>
            </div>
            <div className="job-progress-track" aria-hidden>
              <div className="job-progress-fill" style={{ width: `${completionPct}%` }} />
            </div>
            <p className="hint">
              Ready segments: {manifest.ready_segments}/{manifest.total_segments} | Ready duration:{" "}
              {manifest.ready_duration_s}s / {manifest.total_duration_s}s
            </p>
          </div>

          <div className="segment-grid">
            {manifest.timeline.map((segment) => {
              const cardStatusClass = segment.ready ? "is-ok" : "is-pending";
              return (
                <article key={segment.segment_id} className="segment-card">
                  <div className="segment-card-head">
                    <p className="status-title">
                      Unit #{segment.unit_sequence} ({segment.unit_pattern}) | Segment #{segment.segment_order}
                    </p>
                    <span className={`status-pill ${cardStatusClass}`}>{segment.status}</span>
                  </div>
                  <p className="hint">Target duration: {segment.duration_s}s</p>

                  {segment.output_video_url ? (
                    <video
                      className="segment-preview"
                      src={segment.output_video_url}
                      poster={segment.output_last_frame_url ?? undefined}
                      muted
                      controls
                      playsInline
                      preload="metadata"
                    />
                  ) : segment.output_last_frame_url ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      className="segment-preview"
                      src={segment.output_last_frame_url}
                      alt={`Segment ${segment.segment_id} preview`}
                      loading="lazy"
                    />
                  ) : (
                    <div className="segment-preview segment-placeholder">Preview pending</div>
                  )}

                  <div className="segment-actions">
                    {segment.output_video_url ? (
                      <Link href={segment.output_video_url} target="_blank" className="btn btn-secondary">
                        Open Video URL
                      </Link>
                    ) : (
                      <span className="hint">Output not ready yet.</span>
                    )}
                  </div>
                </article>
              );
            })}
          </div>
        </section>
      ) : (
        <section className="job-pane">
          {completedSegments.length > 0 ? (
            <div className="output-grid">
              {completedSegments.map((segment) => (
                <article key={segment.segment_id} className="output-card">
                  <p className="status-title">
                    Unit #{segment.unit_sequence} / Segment #{segment.segment_order}
                  </p>
                  <video
                    className="segment-preview"
                    src={segment.output_video_url ?? undefined}
                    poster={segment.output_last_frame_url ?? undefined}
                    controls
                    playsInline
                    preload="metadata"
                  />
                  <div className="segment-actions">
                    <Link
                      href={segment.output_video_url as string}
                      target="_blank"
                      className="btn btn-secondary"
                    >
                      Open Full Video
                    </Link>
                  </div>
                </article>
              ))}
            </div>
          ) : (
            <p className="hint">No completed outputs yet. Keep this tab open, previews appear automatically.</p>
          )}
        </section>
      )}
    </div>
  );
}

