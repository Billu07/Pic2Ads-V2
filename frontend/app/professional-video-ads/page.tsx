import type { Metadata } from "next";

import { buildMetadata } from "@/lib/seo";

export const metadata: Metadata = buildMetadata({
  title: "Professional UGC Video Ads | Pic2Ads",
  description:
    "Produce 20-30 second professional creator-style ads with continuous takes and extend-chain rendering.",
  pathname: "/professional-video-ads",
  keywords: [
    "professional ugc ads",
    "ai narrative video ads",
    "seedance extend chain ads",
    "creator style commercial videos",
  ],
});

export default function ProfessionalVideoAdsPage() {
  return (
    <main>
      <section className="section story-shell reveal">
        <p className="eyebrow">Mode B · Professional UGC</p>
        <h1 style={{ margin: 0, fontSize: "clamp(2rem, 3vw, 3rem)" }}>
          Story-led creator ads with continuity intelligence.
        </h1>
        <p className="section-intro">
          Mode B bridges raw UGC trust and polished narrative structure. Use extend-chain for one
          seamless emotional arc, or cut-chain when scene contrast drives the story.
        </p>
      </section>
      <section className="split-feature reveal delay-1">
        <article className="soft-panel atmospheric">
          <p className="eyebrow">Narrative advantage</p>
          <ul className="line-list">
            <li>Higher retention from friction-to-resolution structure</li>
            <li>30-second arcs without abrupt visual drift</li>
            <li>Segment-level intervention for controlled regeneration</li>
          </ul>
        </article>
        <article className="soft-panel atmospheric">
          <p className="eyebrow">Execution patterns</p>
          <ul className="line-list">
            <li>Continuous take via base + extend for temporal consistency</li>
            <li>Cut-chain for scene jumps and episodic storytelling</li>
            <li>Manifest tracking for production-grade QA handoff</li>
          </ul>
        </article>
      </section>
    </main>
  );
}
