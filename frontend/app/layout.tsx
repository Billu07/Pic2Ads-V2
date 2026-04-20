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

export const metadata: Metadata = buildMetadata({
  title: siteConfig.title,
  description: siteConfig.description,
  pathname: "/",
});

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
                <span className="brand-orb" />
                <span>Pic2Ads</span>
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
            Pic2Ads at {siteConfig.domain} | Built for cinematic performance creative with Seedance
            2.0.
          </footer>
        </div>
      </body>
    </html>
  );
}
