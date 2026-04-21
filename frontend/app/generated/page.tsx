import type { Metadata } from "next";

import { GeneratedContentHub } from "@/components/generated-content-hub";
import { buildMetadata } from "@/lib/seo";

export const metadata: Metadata = buildMetadata({
  title: "Generated Content Library | Pic2Ads",
  description:
    "Track all generated Pic2Ads renders with previews, status progress, and direct links to each job tracker.",
  pathname: "/generated",
  keywords: ["generated video library", "render tracking dashboard", "ai ad output manager"],
});

export default function GeneratedContentPage() {
  return (
    <main className="section">
      <GeneratedContentHub />
    </main>
  );
}

