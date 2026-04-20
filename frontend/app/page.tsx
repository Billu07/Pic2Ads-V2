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
        <div className="hero-inner">
          <div className="hero-main reveal">
            <p className="eyebrow">AI Video Ad Platform</p>
            <h1>Image in. Story out. Ads ready for spend.</h1>
            <p>
              Pic2Ads turns one product photo into high-converting video ads across UGC, narrative
              creator formats, and TV-style campaign cuts. Seedance 2.0 powers the execution path
              with extend-native continuity where it matters.
            </p>
            <div className="cta-row">
              <Link className="btn btn-accent" href="/create">
                Launch a Job
              </Link>
              <Link className="btn btn-secondary" href="/pricing">
                View Credits
              </Link>
            </div>
          </div>
          <aside className="hero-rail reveal delay-1">
            <p className="hero-note">
              Three creative modes, one production graph, one render timeline you can actually
              manage.
            </p>
            <p className="hero-note">
              Build hooks first, then scale winning variants with segment-level retries and QA.
            </p>
            <Link href="/jobs/sample-job-id" className="btn btn-primary" style={{ width: "fit-content" }}>
              Open Manifest Demo
            </Link>
          </aside>
        </div>
      </section>

      <section className="section reveal delay-1">
        <p className="eyebrow">Creative Modes</p>
        <h2>Purpose-built paths for each ad intent</h2>
        <p className="section-intro">
          Not one generic prompt box. Each mode has its own planning and render behavior aligned to
          your campaign objective.
        </p>
        <div className="mode-grid">
          <article className="mode-panel">
            <p className="eyebrow">Mode A</p>
            <h3>UGC Influencer</h3>
            <p>10-15 second single-shot ads for rapid paid social testing loops.</p>
            <Link href="/ugc-video-ads">Explore UGC</Link>
          </article>
          <article className="mode-panel">
            <p className="eyebrow">Mode B</p>
            <h3>Professional UGC</h3>
            <p>20-30 second creator narratives with extend-chain continuity and stronger retention.</p>
            <Link href="/professional-video-ads">Explore Professional</Link>
          </article>
          <article className="mode-panel">
            <p className="eyebrow">Mode C</p>
            <h3>TV Commercial AI</h3>
            <p>Multi-shot ad assembly with segment control and export-ready timelines.</p>
            <Link href="/tv-commercial-ai">Explore TV Mode</Link>
          </article>
        </div>
      </section>

      <section className="split-feature reveal delay-2">
        <article className="soft-panel">
          <p className="eyebrow">Execution Logic</p>
          <h2 style={{ marginTop: 0 }}>Seedance-first economics, premium when needed.</h2>
          <ul className="line-list">
            <li>Seedance 2.0 default routing for cost-efficient throughput</li>
            <li>Extend chains for continuous shots beyond 15 seconds</li>
            <li>Cut-chain strategy for deliberate scene shifts</li>
            <li>Manifest-level output visibility for production QA</li>
          </ul>
        </article>
        <article className="soft-panel">
          <p className="eyebrow">Operator Ready</p>
          <h2 style={{ marginTop: 0 }}>One workspace from brief to rendered outputs.</h2>
          <p className="caption">
            Start with your product image and let the pipeline generate structured outputs. Follow
            segment progress and open output URLs directly for review and downstream editing.
          </p>
          <div className="cta-row">
            <Link href="/create" className="btn btn-primary">
              Build New Job
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
