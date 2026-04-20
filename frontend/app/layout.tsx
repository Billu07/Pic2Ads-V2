import type { Metadata } from "next";
import Link from "next/link";
import { Cormorant_Garamond, Sora } from "next/font/google";

import "./globals.css";
import { buildMetadata } from "@/lib/seo";
import { siteConfig } from "@/lib/site";

const display = Cormorant_Garamond({
  subsets: ["latin"],
  variable: "--font-display",
  weight: ["500", "600", "700"],
});

const body = Sora({
  subsets: ["latin"],
  variable: "--font-body",
  weight: ["300", "400", "500", "600", "700"],
});

const baseMetadata = buildMetadata({
  title: siteConfig.title,
  description: siteConfig.description,
  pathname: "/",
});

export const metadata: Metadata = {
  ...baseMetadata,
  manifest: "/site.webmanifest",
  icons: {
    icon: [
      { url: "/favicon.ico", sizes: "any" },
      { url: "/favicon-16x16.png", type: "image/png", sizes: "16x16" },
      { url: "/favicon-32x32.png", type: "image/png", sizes: "32x32" },
    ],
    apple: [{ url: "/apple-touch-icon.png", sizes: "180x180", type: "image/png" }],
    other: [
      {
        rel: "icon",
        url: "/android-chrome-192x192.png",
        sizes: "192x192",
        type: "image/png",
      },
      {
        rel: "icon",
        url: "/android-chrome-512x512.png",
        sizes: "512x512",
        type: "image/png",
      },
    ],
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${display.variable} ${body.variable}`}>
        <div className="ambient-layer ambient-layer-a" aria-hidden="true" />
        <div className="ambient-layer ambient-layer-b" aria-hidden="true" />
        <div className="ambient-noise" aria-hidden="true" />
        <div className="site-shell">
          <header className="top-nav reveal">
            <div className="site-chrome">
              <Link href="/" className="brand brand-lockup">
                <span className="brand-wordmark" aria-label="Pic2Ads">
                  <span className="brand-wordmark-main">
                    Pic<span className="brand-wordmark-mid">2</span>Ads
                  </span>
                  <span className="brand-wordmark-sub">AI Video Ad Studio</span>
                </span>
              </Link>
              <nav className="nav-links">
                <Link href="/ugc-video-ads">UGC</Link>
                <Link href="/professional-video-ads">Professional</Link>
                <Link href="/tv-commercial-ai">TV</Link>
                <Link href="/pricing">Pricing</Link>
                <Link href="/create" className="nav-action">
                  Start Building
                </Link>
              </nav>
            </div>
          </header>
          {children}
          <footer className="footer">
            Pic2Ads at {siteConfig.domain} | A sister concern of{" "}
            <a href="https://autolinium.com" target="_blank" rel="noreferrer">
              Autolinium
            </a>
            .
          </footer>
        </div>
      </body>
    </html>
  );
}
