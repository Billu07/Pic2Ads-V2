import type { MetadataRoute } from "next";

import { canonicalUrl } from "@/lib/site";

export default function sitemap(): MetadataRoute.Sitemap {
  const routes = ["/", "/create", "/ugc-video-ads", "/professional-video-ads", "/tv-commercial-ai", "/pricing"];
  const lastModified = new Date();

  return routes.map((route) => ({
    url: canonicalUrl(route),
    lastModified,
    changeFrequency: route === "/" ? "daily" : "weekly",
    priority: route === "/" ? 1 : 0.8,
  }));
}
