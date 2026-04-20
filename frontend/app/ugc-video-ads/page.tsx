import type { Metadata } from "next";

import { buildMetadata } from "@/lib/seo";

export const metadata: Metadata = buildMetadata({
  title: "UGC Video Ads Generator | Pic2Ads",
  description:
    "Generate 10-15 second UGC product video ads from a single image for TikTok, Instagram Reels, and YouTube Shorts.",
  pathname: "/ugc-video-ads",
  keywords: [
    "ugc video ad generator",
    "ai tiktok ads",
    "short form ecommerce ads",
    "product image to ugc video",
  ],
});

export default function UgcVideoAdsPage() {
  return (
    <main>
      <section className="section story-shell reveal">
        <p className="eyebrow">Mode A · UGC Influencer</p>
        <h1 style={{ margin: 0, fontSize: "clamp(2rem, 3vw, 3rem)" }}>
          UGC ads tuned for velocity, honesty, and fast testing.
        </h1>
        <p className="section-intro">
          Single-shot 10-15 second generation for rapid hook iteration, lightweight production,
          and always-on paid social refreshes.
        </p>
      </section>
      <section className="split-feature reveal delay-1">
        <article className="soft-panel atmospheric">
          <p className="eyebrow">Where it wins</p>
          <ul className="line-list">
            <li>TikTok top-of-funnel creative sprints</li>
            <li>Meta Reels variation packs for CAC control</li>
            <li>PDP short-form video proof clips</li>
          </ul>
        </article>
        <article className="soft-panel atmospheric">
          <p className="eyebrow">Pipeline behavior</p>
          <ul className="line-list">
            <li>One render unit, one segment, no continuity overhead</li>
            <li>Seedance default path for cost-efficient throughput</li>
            <li>Ideal mode for high-volume hook experimentation</li>
          </ul>
        </article>
      </section>
    </main>
  );
}
