import type { Metadata } from "next";

import { CreateJobWorkbench } from "@/components/create-job-workbench";
import { buildMetadata } from "@/lib/seo";

export const metadata: Metadata = buildMetadata({
  title: "Create AI Video Ad Job | Pic2Ads Workspace",
  description:
    "Configure and launch a Pic2Ads job: mode, product image, duration, deliverable ratio, and pipeline execution.",
  pathname: "/create",
  keywords: [
    "ai video ad workspace",
    "create ugc ad job",
    "seedance job builder",
    "product to video workflow",
  ],
});

export default function CreatePage() {
  return (
    <main>
      <section className="section story-shell reveal">
        <p className="eyebrow">Build Flow</p>
        <h1 className="create-title">
          Craft your next ad run with cinematic calm.
        </h1>
        <p className="section-intro">
          Start from a product image URL, pick your mode, and execute the render pipeline. This
          workspace is wired directly to the backend endpoints you already configured.
        </p>
      </section>
      <CreateJobWorkbench />
    </main>
  );
}
