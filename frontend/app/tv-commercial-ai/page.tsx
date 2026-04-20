import type { Metadata } from "next";

import { ModeVideoGallery } from "@/components/mode-video-gallery";
import { buildMetadata } from "@/lib/seo";
import { tvModeVideos } from "@/lib/video-library";

export const metadata: Metadata = buildMetadata({
  title: "AI TV Commercial Generator | Pic2Ads",
  description:
    "Create multi-shot AI TV commercials with render-unit planning, segment QA, and export-ready timelines.",
  pathname: "/tv-commercial-ai",
  keywords: [
    "ai tv commercial generator",
    "multi shot video ad generation",
    "commercial storyboard to video ai",
    "campaign video production automation",
  ],
});

export default function TvCommercialAiPage() {
  return (
    <main>
      <section className="section story-shell reveal">
        <p className="eyebrow">Mode C - TV Commercial</p>
        <h1 style={{ margin: 0, fontSize: "clamp(2rem, 3vw, 3rem)" }}>
          Multi-shot commercial composition with operator control.
        </h1>
        <p className="section-intro">
          Built for campaign-grade storytelling where shot sequencing, continuity constraints, and
          export readiness need deterministic structure.
        </p>
      </section>
      <section className="split-feature reveal delay-1">
        <article className="soft-panel atmospheric">
          <p className="eyebrow">Team workflow fit</p>
          <ul className="line-list">
            <li>Render units map cleanly to production planning logic</li>
            <li>Segment timelines enable review before final cut assembly</li>
            <li>Structured output aligns with agency handoff processes</li>
          </ul>
        </article>
        <article className="soft-panel atmospheric">
          <p className="eyebrow">Technical baseline</p>
          <ul className="line-list">
            <li>Efficiency-first routing for lower blended generation cost</li>
            <li>Fallback-ready architecture for provider instability</li>
            <li>Manifest output gives transparent shot completion states</li>
          </ul>
        </article>
      </section>
      <ModeVideoGallery
        eyebrow="TV Gallery"
        title="TV commercial references in your workspace"
        intro="Your TV AD clips and cinematic alternatives are now directly available inside Mode C for visual guidance."
        items={tvModeVideos}
      />
    </main>
  );
}
