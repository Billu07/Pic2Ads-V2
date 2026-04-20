import type { Metadata } from "next";

import { canonicalUrl, siteConfig } from "@/lib/site";

const primaryKeywords = [
  "ai video ad generator",
  "product photo to video ad",
  "ugc ad creator ai",
  "professional ugc video ads",
  "ai tv commercial maker",
  "pic2ads video ads",
  "short form ad video generator",
  "performance marketing video ads",
  "ecommerce ad creative automation",
];

type BuildMetadataInput = {
  title: string;
  description: string;
  pathname: string;
  keywords?: string[];
};

export function buildMetadata(input: BuildMetadataInput): Metadata {
  const url = canonicalUrl(input.pathname);
  const keywords = input.keywords ?? primaryKeywords;

  return {
    title: input.title,
    description: input.description,
    keywords,
    alternates: {
      canonical: url,
    },
    openGraph: {
      type: "website",
      title: input.title,
      description: input.description,
      url,
      siteName: siteConfig.name,
    },
    twitter: {
      card: "summary_large_image",
      title: input.title,
      description: input.description,
    },
  };
}

export const homePageKeywords = [
  ...primaryKeywords,
  "ai ad generator for shopify brands",
  "tiktok ad creative generator",
  "meta ads video generator",
  "youtube shorts ad generator",
  "video ad variations for ab testing",
];
