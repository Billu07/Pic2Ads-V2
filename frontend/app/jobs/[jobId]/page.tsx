import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { JobLiveManifest } from "@/components/job-live-manifest";
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
      <JobLiveManifest jobId={jobId} initialManifest={manifest} />
    </main>
  );
}
