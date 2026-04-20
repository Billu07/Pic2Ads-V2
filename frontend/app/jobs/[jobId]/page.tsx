import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { getExportManifest } from "@/lib/api";
import { buildMetadata } from "@/lib/seo";

type PageProps = {
  params: Promise<{ jobId: string }>;
};

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { jobId } = await params;
  return {
    ...buildMetadata({
      title: `Job ${jobId} Export Manifest | Pic2Ads`,
      description: "Check segment render status and output URLs for a Pic2Ads production job.",
      pathname: `/jobs/${jobId}`,
      keywords: ["ad video export manifest", "render timeline", "segment output status"],
    }),
    robots: {
      index: false,
      follow: false,
    },
  };
}

export default async function JobManifestPage({ params }: PageProps) {
  const { jobId } = await params;
  const manifest = await getExportManifest(jobId);

  if (manifest === null) {
    notFound();
  }

  return (
    <main className="section">
      <div className="panel">
        <p className="eyebrow">Render Manifest</p>
        <h1 style={{ marginTop: 0 }}>Job {manifest.job_id}</h1>
        <p>
          <span className="status-pill">Status: {manifest.status}</span>
        </p>
        <p className="caption">
          Ready segments: {manifest.ready_segments}/{manifest.total_segments} | Ready duration:{" "}
          {manifest.ready_duration_s}s / {manifest.total_duration_s}s
        </p>
        <table className="manifest-table">
          <thead>
            <tr>
              <th>Unit</th>
              <th>Segment</th>
              <th>Status</th>
              <th>Duration</th>
              <th>Output</th>
            </tr>
          </thead>
          <tbody>
            {manifest.timeline.map((segment) => (
              <tr key={segment.segment_id}>
                <td>
                  #{segment.unit_sequence} ({segment.unit_pattern})
                </td>
                <td>#{segment.segment_order}</td>
                <td>{segment.status}</td>
                <td>{segment.duration_s}s</td>
                <td>
                  {segment.output_video_url ? (
                    <Link href={segment.output_video_url} target="_blank">
                      Video URL
                    </Link>
                  ) : (
                    "Pending"
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </main>
  );
}
