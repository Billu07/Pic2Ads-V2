export const siteConfig = {
  name: "Pic2Ads",
  domain: "https://pic2ads.io",
  title: "Pic2Ads | AI Video Ad Generator for UGC, Pro Ads, and TV Spots",
  description:
    "Turn one product photo into finished video ads with AI. Generate UGC ads, professional creator-style ads, and TV-ready commercial cuts.",
  apiBaseUrl: process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/v1",
  siteUrl: process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000",
};

export function canonicalUrl(pathname: string): string {
  const base = siteConfig.siteUrl.replace(/\/+$/, "");
  const path = pathname.startsWith("/") ? pathname : `/${pathname}`;
  return `${base}${path}`;
}
