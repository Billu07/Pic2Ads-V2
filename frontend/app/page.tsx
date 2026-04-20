import Link from "next/link";

import { homePageKeywords } from "@/lib/seo";
import { siteConfig } from "@/lib/site";

export default function HomePage() {
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    name: "Pic2Ads",
    applicationCategory: "BusinessApplication",
    operatingSystem: "Web",
    description: siteConfig.description,
    url: siteConfig.siteUrl,
    offers: {
      "@type": "Offer",
      priceCurrency: "USD",
      price: "39",
      category: "Starter",
    },
    keywords: homePageKeywords.join(", "),
  };

  return (
    <main>
      <section className="full-bleed-hero">
        <div className="hero-paint" aria-hidden="true" />
        <div className="hero-inner">
          <div className="hero-main reveal">
            <p className="eyebrow">AI Video Ad Studio</p>
            <h1>A dreamlike ad engine for brands that need performance and beauty.</h1>
            <p>
              Start with a single product image. Generate UGC, creator-narrative, and TV-style ads
              with one orchestration layer and Seedance 2.0 as the production spine.
            </p>
            <div className="cta-row">
              <Link className="btn btn-accent" href="/create">
                Launch Workspace
              </Link>
              <Link className="btn btn-secondary" href="/pricing">
                See Pricing
              </Link>
            </div>
          </div>
          <aside className="hero-rail reveal delay-1">
            <p className="hero-note">Mode-aware prompting from hook to final render manifest.</p>
            <p className="hero-note">Continuity-native workflows with extend where it matters.</p>
            <Link href="/create" className="btn btn-primary" style={{ width: "fit-content" }}>
              Start Now
            </Link>
          </aside>
        </div>
      </section>

      <section className="section reveal delay-1">
        <p className="eyebrow">Creative Modes</p>
        <h2>Three creative worlds. One coherent rendering system.</h2>
        <p className="section-intro">
          Each mode has its own narrative grammar, prompt pack, and execution logic.
        </p>
        <div className="mode-river">
          <article className="mode-river-item">
            <p className="eyebrow">Mode A</p>
            <h3>UGC Influencer</h3>
            <p>Fast single-shot outputs for paid social testing loops.</p>
            <Link href="/ugc-video-ads">Explore UGC</Link>
          </article>
          <article className="mode-river-item">
            <p className="eyebrow">Mode B</p>
            <h3>Professional UGC</h3>
            <p>Narrative creator arcs with continuity-aware extensions.</p>
            <Link href="/professional-video-ads">Explore Professional</Link>
          </article>
          <article className="mode-river-item">
            <p className="eyebrow">Mode C</p>
            <h3>TV Commercial AI</h3>
            <p>Multi-shot campaign cuts with storyboard and gate controls.</p>
            <Link href="/tv-commercial-ai">Explore TV</Link>
          </article>
        </div>
      </section>

      <section className="split-feature reveal delay-2">
        <article className="soft-panel atmospheric">
          <p className="eyebrow">Execution Logic</p>
          <h2 style={{ marginTop: 0 }}>Seedance-first economics with cinematic escalation.</h2>
          <ul className="line-list">
            <li>Seedance 2.0 default routing for cost-efficient throughput</li>
            <li>Extend chains for long continuous takes</li>
            <li>Cut-chain strategy for deliberate scene shifts</li>
            <li>Manifest-level output visibility for production QA</li>
          </ul>
        </article>
        <article className="soft-panel atmospheric">
          <p className="eyebrow">Operator Workspace</p>
          <h2 style={{ marginTop: 0 }}>Plan, generate, validate, and ship in one flow.</h2>
          <p className="caption">
            Job creation, creative decisions, gates, and render status are built into one calm
            interface designed for daily iteration.
          </p>
          <div className="cta-row">
            <Link href="/create" className="btn btn-primary">
              Open Workspace
            </Link>
          </div>
        </article>
      </section>

      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
    </main>
  );
}
