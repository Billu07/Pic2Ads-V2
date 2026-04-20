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
      <section className="section story-shell reveal">
        <p className="eyebrow">Pricing</p>
        <h1 style={{ margin: 0, fontSize: "clamp(2rem, 3vw, 3rem)" }}>
          Credits mapped to production complexity
        </h1>
        <p className="section-intro">
          Credits map to render complexity. Keep cost low with Seedance-first generation and only
          use premium cinematic routes where the shot requires it.
        </p>
      </section>
      <section className="pricing-grid reveal delay-1">
        {tiers.map((tier, index) => (
          <article key={tier.name} className={`pricing-column ${index === 1 ? "featured" : ""}`}>
            <p className="eyebrow">{tier.name}</p>
            <h2>{tier.price}</h2>
            <p className="caption">{tier.credits} credits</p>
            <p>{tier.fit}</p>
          </article>
        ))}
      </section>
    </main>
  );
}
