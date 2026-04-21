"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import type { ExportManifest, JobListItem } from "@/lib/api";
import { listJobs } from "@/lib/api";

type ModeFilter = "all" | "ugc" | "pro_arc" | "tv";

function formatLocalDate(iso: string): string {
  const dt = new Date(iso);
  if (Number.isNaN(dt.getTime())) {
    return "Unknown time";
  }
  return dt.toLocaleString([], {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

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

export function GeneratedContentHub() {
  const [jobs, setJobs] = useState<JobListItem[]>([]);
  const [manifests, setManifests] = useState<Record<string, ExportManifest | null>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<ModeFilter>("all");

  const refresh = useCallback(async () => {
    setIsRefreshing(true);
    setError(null);
    try {
      const list = await listJobs(36, 0);
      setJobs(list.items);

      if (list.items.length === 0) {
        setManifests({});
        return;
      }

      const manifestEntries = await Promise.all(
        list.items.map(async (job) => {
          try {
            const response = await fetch(`/api/jobs/${encodeURIComponent(job.id)}/export/manifest`, {
              method: "GET",
              cache: "no-store",
            });
            if (!response.ok) {
              return [job.id, null] as const;
            }
            const parsed = (await response.json()) as ExportManifest;
            return [job.id, parsed] as const;
          } catch {
            return [job.id, null] as const;
          }
        })
      );

      setManifests(Object.fromEntries(manifestEntries));
    } catch (refreshError) {
      setError(summarizeError(refreshError));
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const filteredJobs = useMemo(() => {
    if (filter === "all") {
      return jobs;
    }
    return jobs.filter((job) => job.mode === filter);
  }, [jobs, filter]);

  return (
    <div className="panel generated-shell">
      <div className="generated-head">
        <div>
          <p className="eyebrow">Generated Content</p>
          <h1 className="job-live-title">Render Library</h1>
          <p className="caption generated-subline">
            One quiet place to monitor completed videos, in-progress jobs, and output previews.
          </p>
        </div>
        <div className="cta-row compact-actions">
          <button type="button" className="btn btn-secondary" onClick={() => void refresh()}>
            {isRefreshing ? "Refreshing..." : "Refresh"}
          </button>
          <Link href="/create" className="btn btn-primary">
            New Render
          </Link>
        </div>
      </div>

      <div className="generated-filters">
        {([
          ["all", "All"],
          ["ugc", "UGC"],
          ["pro_arc", "Professional"],
          ["tv", "TV"],
        ] as const).map(([value, label]) => (
          <button
            key={value}
            type="button"
            className={`generated-filter-chip ${filter === value ? "active" : ""}`}
            onClick={() => setFilter(value)}
          >
            {label}
          </button>
        ))}
      </div>

      {error ? <p className="hint">Error: {error}</p> : null}

      {isLoading ? (
        <p className="hint">Loading generated content...</p>
      ) : filteredJobs.length === 0 ? (
        <div className="generated-empty">
          <p className="status-title">No jobs in this view yet.</p>
          <p className="hint">Create your first render to start filling this library.</p>
          <Link href="/create" className="btn btn-accent">
            Start Creating
          </Link>
        </div>
      ) : (
        <div className="generated-grid">
          {filteredJobs.map((job) => {
            const manifest = manifests[job.id] ?? null;
            const completion =
              manifest && manifest.total_segments > 0
                ? Math.round((manifest.ready_segments / manifest.total_segments) * 100)
                : 0;

            const readyVideo =
              manifest?.timeline.find((segment) => segment.ready && Boolean(segment.output_video_url)) ??
              null;
            const readyFrame =
              manifest?.timeline.find((segment) => Boolean(segment.output_last_frame_url)) ?? null;

            return (
              <article key={job.id} className="generated-card">
                <div className="generated-card-head">
                  <p className="status-title">{job.id}</p>
                  <span className={`status-pill ${manifest?.status === "ready" ? "is-ok" : "is-pending"}`}>
                    {manifest?.status ?? "queued"}
                  </span>
                </div>

                <p className="hint">
                  Mode: {job.mode} | Created: {formatLocalDate(job.created_at)}
                </p>
                <p className="hint">
                  Job status: {job.status}
                  {manifest
                    ? ` | Segments: ${manifest.ready_segments}/${manifest.total_segments}`
                    : " | Manifest pending"}
                </p>

                <div className="generated-progress-track" aria-hidden>
                  <div className="generated-progress-fill" style={{ width: `${completion}%` }} />
                </div>

                {readyVideo?.output_video_url ? (
                  <video
                    className="generated-preview"
                    src={readyVideo.output_video_url}
                    poster={readyVideo.output_last_frame_url ?? undefined}
                    controls
                    playsInline
                    preload="metadata"
                  />
                ) : readyFrame?.output_last_frame_url ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    className="generated-preview"
                    src={readyFrame.output_last_frame_url}
                    alt={`Preview for ${job.id}`}
                    loading="lazy"
                  />
                ) : (
                  <div className="generated-preview generated-placeholder">Preview pending</div>
                )}

                <div className="cta-row compact-actions">
                  <Link href={`/jobs/${job.id}`} className="btn btn-primary">
                    Open Tracker
                  </Link>
                  {readyVideo?.output_video_url ? (
                    <Link href={readyVideo.output_video_url} target="_blank" className="btn btn-secondary">
                      Open Output
                    </Link>
                  ) : null}
                </div>
              </article>
            );
          })}
        </div>
      )}
    </div>
  );
}

