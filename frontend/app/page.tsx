import Link from "next/link";
import Image from "next/image";

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
        <div className="hero-video-container">
          <video 
            className="hero-video-bg" 
            autoPlay 
            loop 
            muted 
            playsInline 
            poster="/hero-poster.jpg"
          >
            <source src="/hero-bg.webm" type="video/webm" />
          </video>
          <div className="hero-overlay" aria-hidden="true" />
        </div>

        {/* Floating SaaS Widgets */}
        <div className="hero-widget widget-1">
          <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--mint)', boxShadow: '0 0 10px var(--mint)' }} />
          <span>Processing 4K Narrative...</span>
        </div>
        <div className="hero-widget widget-2">
          <div style={{ color: 'var(--accent)', fontSize: '1.2rem' }}>✦</div>
          <span>Performance Score: 98/100</span>
        </div>

        <div className="hero-inner">
          <div className="hero-main reveal active">
            <p className="eyebrow" style={{ color: 'var(--accent)', fontWeight: 800 }}>AI Video Ad Studio</p>
            <h1>Creative<br/>Automation.</h1>
            <p>
              Pic2Ads transforms a single product shot into a high-performance video campaign. 
              UGC, Narrative, and TV Commercials—rendered in minutes.
            </p>
            <div className="cta-row">
              <Link className="btn btn-accent" href="/create">
                Start Building
              </Link>
              <Link className="btn btn-secondary" href="/pricing">
                View Pricing
              </Link>
            </div>
          </div>
        </div>
      </section>

      <section className="section reveal active" style={{ padding: '4rem 0' }}>
        <p className="eyebrow">Creative Gallery</p>
        <h2 style={{ fontSize: 'clamp(2.5rem, 5vw, 4rem)' }}>The content engine in action.</h2>
        
        <div className="bento-gallery">
          {/* Featured Output */}
          <div className="bento-item item-1">
            <video className="bento-video" autoPlay loop muted playsInline style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover' }}>
              <source src="/hero-bg-2.webm" type="video/webm" />
            </video>
            <div className="bento-content">
              <h4>Cinematic Master</h4>
              <p>Generated via Mode C (TV Commercial)</p>
            </div>
          </div>

          {/* Input -> Output Showcase */}
          <div className="bento-item item-2">
            <div className="io-pair">
              <div className="io-box">
                <div className="io-label">Input</div>
                <Image src="/logo.png" alt="Input Product" fill style={{ objectFit: 'contain', padding: '1rem', opacity: 0.8 }} />
              </div>
              <div className="io-connector">
                <div className="io-line" />
                <div style={{ color: 'var(--accent)', fontWeight: 900 }}>→</div>
              </div>
              <div className="io-box" style={{ flex: 1.5 }}>
                <div className="io-label" style={{ color: 'var(--mint)' }}>Output</div>
                <video autoPlay loop muted playsInline style={{ width: '100%', height: '100%', objectFit: 'cover' }}>
                  <source src="/UGC TV/ship-recycling.mp4" type="video/mp4" />
                </video>
              </div>
            </div>
          </div>

          {/* Scene Continuity Mesh */}
          <div className="bento-item item-3">
             <div className="mesh-bg mesh-1" style={{ position: 'absolute', inset: 0 }} />
             <div className="bento-content">
              <h4>Continuity Mapping</h4>
              <p>Ensuring brand consistency across shots.</p>
            </div>
          </div>

          {/* Another Input -> Output */}
          <div className="bento-item item-4" style={{ background: 'var(--bg-mid)' }}>
             <div className="io-pair" style={{ padding: '1rem' }}>
                <div className="io-box">
                  <Image src="/logo.png" alt="Input" fill style={{ objectFit: 'contain', padding: '0.5rem' }} />
                </div>
                <div className="io-connector">
                  <div style={{ color: 'var(--accent)', fontSize: '0.8rem' }}>AI</div>
                </div>
                <div className="io-box">
                  <video autoPlay loop muted playsInline style={{ width: '100%', height: '100%', objectFit: 'cover' }}>
                    <source src="/TV AD/tv-ad.mp4" type="video/mp4" />
                  </video>
                </div>
             </div>
          </div>

          {/* Professional Arc */}
          <div className="bento-item item-5">
            <video className="bento-video" autoPlay loop muted playsInline style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover' }}>
              <source src="/UGC TV/Ugc landscape.mp4" type="video/mp4" />
            </video>
            <div className="bento-content">
              <h4>Creator Narrative</h4>
              <p>Mode B: Professional UGC Arc</p>
            </div>
          </div>

          {/* Small Mesh Gradient */}
          <div className="bento-item item-6">
            <div className="mesh-bg mesh-3" style={{ position: 'absolute', inset: 0 }} />
          </div>
        </div>
      </section>

      <section className="split-feature reveal active">
        <article className="soft-panel atmospheric">
          <p className="eyebrow">Production Hub</p>
          <h2 style={{ marginTop: 0 }}>Seedance 2.0 Engine.</h2>
          <ul className="line-list">
            <li>Multi-agent orchestration</li>
            <li>Extend-native Shot Continuity</li>
            <li>Automated Scripting & Casting</li>
          </ul>
        </article>
        <article className="soft-panel atmospheric">
          <p className="eyebrow">Enterprise Ready</p>
          <h2 style={{ marginTop: 0 }}>Scale your creative.</h2>
          <p className="caption">
            Deploy thousands of high-converting variants from a single asset. 
            Optimized for TikTok, Meta, and YouTube.
          </p>
          <div className="cta-row">
            <Link href="/create" className="btn btn-accent">
              Get Started Free
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
