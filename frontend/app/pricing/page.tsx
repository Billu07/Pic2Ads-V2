import type { Metadata } from "next";

import { buildMetadata } from "@/lib/seo";

export const metadata: Metadata = buildMetadata({
  title: "Pic2Ads Pricing | Credits for AI Video Ads",
  description:
    "Choose a Pic2Ads plan and run AI-powered UGC, professional, and TV commercial ad generation with credit-based pricing.",
  pathname: "/pricing",
  keywords: [
    "ai video ad pricing",
    "ugc video ad credits",
    "ecommerce ad generator pricing",
    "performance creative automation pricing",
  ],
});

const tiers = [
  { name: "Starter", price: "$39", credits: 150, fit: "~5 UGC spots or 1 Mode B spot" },
  { name: "Growth", price: "$149", credits: 700, fit: "Weekly ad testing for growth brands" },
  { name: "Scale", price: "$399", credits: 2200, fit: "Agency teams and multi-brand workflows" },
];

export default function PricingPage() {
  return (
    <main>
      <section className="section">
        <p className="eyebrow">Pricing</p>
        <h1 style={{ margin: 0, fontSize: "clamp(2rem, 3vw, 3rem)" }}>
          Credits mapped to production complexity
        </h1>
        <p className="section-intro">
          Credits map to render complexity. Keep cost low with Seedance-first generation and only
          use premium cinematic routes where the shot requires it.
        </p>
      </section>
      <section className="mode-grid">
        {tiers.map((tier) => (
          <article key={tier.name} className="mode-panel">
            <h2>{tier.name}</h2>
            <p style={{ fontSize: "1.6rem", margin: "0.3rem 0", fontWeight: 800 }}>{tier.price}</p>
            <p>{tier.credits} credits</p>
            <p>{tier.fit}</p>
          </article>
        ))}
      </section>
    </main>
  );
}
