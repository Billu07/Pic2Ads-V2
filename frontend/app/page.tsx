import Link from "next/link";

import { OptimizedVideo } from "@/components/optimized-video";
import { homePageKeywords } from "@/lib/seo";
import { siteConfig } from "@/lib/site";

export default function HomePage() {
  const referenceLibrary = [
    {
      id: "clip_ugc",
      title: "UGC Pulse Cut",
      mode: "Mode A - UGC",
      src: "/hero-bg.webm",
      poster: "/hero-poster.jpg",
    },
    {
      id: "clip_narrative",
      title: "Narrative Arc Reel",
      mode: "Mode B - Professional",
      src: "/hero-bg-2.webm",
      poster: "/hero-poster.jpg",
    },
    {
      id: "clip_tv",
      title: "TV Scene Sequence",
      mode: "Mode C - TV",
      src: "/hero-bg.webm",
      poster: "/hero-poster.jpg",
    },
    {
      id: "clip_variation",
      title: "Variant Playground",
      mode: "Mode Lab",
      src: "/hero-bg-2.webm",
      poster: "/hero-poster.jpg",
    },
  ];

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
    <main className="home-main">
      <section className="full-bleed-hero home-hero">
        <OptimizedVideo
          className="hero-video-bg"
          src="/hero-bg.webm"
          poster="/hero-poster.jpg"
          priority
        />
        <div className="hero-overlay" aria-hidden="true" />
        <div className="hero-grid-overlay" aria-hidden="true" />
        <div className="hero-inner">
          <div className="hero-main home-hero-main reveal">
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
            <div className="hero-anchors">
              <span>Seedance 2.0 Routing</span>
              <span>Extend-native continuity</span>
              <span>Segment-level operator control</span>
            </div>
          </div>
          <aside className="hero-rail hero-orbit reveal delay-1">
            <p className="hero-orbit-label">Production Pulse</p>
            <p className="hero-note">
              Three creative modes, one production graph, one render timeline you can actually
              manage.
            </p>
            <p className="hero-note">
              Build hooks first, then scale winning variants with segment-level retries and QA.
            </p>
            <div className="hero-orbit-grid">
              <span className="orbit-chip">Concept Engine</span>
              <span className="orbit-chip">Prompt Guardrails</span>
              <span className="orbit-chip">Render Manifest</span>
              <span className="orbit-chip">TV Gates</span>
            </div>
            <Link href="/jobs/sample-job-id" className="btn btn-primary" style={{ width: "fit-content" }}>
              Open Manifest Demo
            </Link>
          </aside>
        </div>
      </section>

      <section className="section reveal delay-1 home-section">
        <p className="eyebrow">Creative Modes</p>
        <h2>Purpose-built paths for each ad intent</h2>
        <p className="section-intro">
          Not one generic prompt box. Each mode has its own planning and render behavior aligned to
          your campaign objective.
        </p>
        <div className="mode-river">
          <article className="mode-river-item">
            <p className="eyebrow">Mode A</p>
            <h3>UGC Influencer</h3>
            <p>10-15 second single-shot ads for rapid paid social testing loops.</p>
            <Link href="/ugc-video-ads">Explore UGC</Link>
          </article>
          <article className="mode-river-item">
            <p className="eyebrow">Mode B</p>
            <h3>Professional UGC</h3>
            <p>20-30 second creator narratives with extend-chain continuity and stronger retention.</p>
            <Link href="/professional-video-ads">Explore Professional</Link>
          </article>
          <article className="mode-river-item">
            <p className="eyebrow">Mode C</p>
            <h3>TV Commercial AI</h3>
            <p>Multi-shot ad assembly with segment control and export-ready timelines.</p>
            <Link href="/tv-commercial-ai">Explore TV Mode</Link>
          </article>
        </div>
      </section>

      <section className="section media-library reveal delay-1">
        <div className="library-head">
          <p className="eyebrow">Visual Library</p>
          <h2>Reference reels that shape atmosphere and continuity</h2>
          <p className="section-intro">
            Drop your own footage into the library rail to tune pacing, lens language, and
            emotional temperature before scaling variants.
          </p>
        </div>
        <div className="library-track">
          {referenceLibrary.map((clip) => (
            <article key={clip.id} className="library-item">
              <OptimizedVideo src={clip.src} poster={clip.poster} />
              <div className="library-meta">
                <p>{clip.mode}</p>
                <h3>{clip.title}</h3>
              </div>
            </article>
          ))}
        </div>
        <p className="library-note">
          Add more reels by placing files in `frontend/public` and duplicating one item in this
          list.
        </p>
      </section>

      <section className="bento-section reveal delay-2">
        <p className="eyebrow">Creative Gallery</p>
        <h2>Cinematic content at scale</h2>
        <div className="bento-gallery">
          <div className="bento-item bento-large">
            <OptimizedVideo className="bento-video" src="/hero-bg-2.webm" poster="/hero-poster.jpg" />
            <div className="bento-content">
              <h4>High-Fidelity Render</h4>
              <p>Generated in Mode C</p>
            </div>
          </div>
          <div className="bento-item bento-tall">
            <div className="mesh-bg mesh-1" />
            <div className="bento-content">
              <h4>Scene Extraction</h4>
              <p>Continuity mapped</p>
            </div>
          </div>
          <div className="bento-item bento-wide">
            <div className="mesh-bg mesh-2" />
            <div className="bento-content">
              <h4>Render Timeline</h4>
              <p>Multi-shot assembly active</p>
            </div>
          </div>
          <div className="bento-item">
            <div className="mesh-bg mesh-3" />
            <div className="bento-content">
              <h4>Variant A</h4>
              <p>UGC optimized</p>
            </div>
          </div>
          <div className="bento-item">
            <div className="mesh-bg mesh-1" style={{ animationDelay: '-5s' }} />
            <div className="bento-content">
              <h4>Variant B</h4>
              <p>Narrative cut</p>
            </div>
          </div>
        </div>
      </section>

      <section className="split-feature reveal delay-2">
        <article className="soft-panel atmospheric">
          <p className="eyebrow">Execution Logic</p>
          <h2 style={{ marginTop: 0 }}>Seedance-first economics, premium when needed.</h2>
          <ul className="line-list">
            <li>Seedance 2.0 default routing for cost-efficient throughput</li>
            <li>Extend chains for continuous shots beyond 15 seconds</li>
            <li>Cut-chain strategy for deliberate scene shifts</li>
            <li>Manifest-level output visibility for production QA</li>
          </ul>
        </article>
        <article className="soft-panel atmospheric">
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

      <section className="section final-cta reveal delay-2">
        <p className="eyebrow">Ready To Launch</p>
        <h2>Move from concept to ad-ready cuts in one workspace.</h2>
        <p className="section-intro">
          Build your first run, approve TV gates when required, and ship creative variants faster
          without losing visual control.
        </p>
        <div className="cta-row">
          <Link className="btn btn-accent" href="/create">
            Start Building
          </Link>
          <Link className="btn btn-secondary" href="/pricing">
            See Credit Plans
          </Link>
        </div>
      </section>

      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
    </main>
  );
}
