import type { Metadata } from "next";
import Link from "next/link";
import { Fraunces, Plus_Jakarta_Sans } from "next/font/google";

import "./globals.css";
import { buildMetadata } from "@/lib/seo";
import { siteConfig } from "@/lib/site";

const display = Fraunces({
  subsets: ["latin"],
  variable: "--font-display",
  weight: ["500", "600", "700"],
});

const body = Plus_Jakarta_Sans({
  subsets: ["latin"],
  variable: "--font-body",
  weight: ["400", "500", "600", "700"],
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
        <div className="ambient-layer" aria-hidden="true" />
        <div className="site-shell">
          <header className="top-nav">
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
          </header>
          {children}
          <footer className="footer">
            Pic2Ads at {siteConfig.domain} | AI video ad pipeline with Seedance 2.0 base and extend.
          </footer>
        </div>
      </body>
    </html>
  );
}
