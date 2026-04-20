export type GalleryVideoItem = {
  id: string;
  title: string;
  tag: string;
  src: string;
  poster?: string;
};

export const homeLibraryVideos: GalleryVideoItem[] = [
  {
    id: "home_ugc_mobile",
    title: "Mobile UGC Beat",
    tag: "Mode A - UGC Mobile",
    src: "/UGC%20Mobile/dreamy-cat.mp4",
    poster: "/hero-poster.jpg",
  },
  {
    id: "home_ugc_tv",
    title: "UGC TV Hook",
    tag: "Mode A - UGC TV",
    src: "/UGC%20TV/ship-recycling.mp4",
    poster: "/hero-poster.jpg",
  },
  {
    id: "home_pro_arc",
    title: "Professional Arc",
    tag: "Mode B - Professional",
    src: "/UGC%20TV/Ugc%20landscape.mp4",
    poster: "/hero-poster.jpg",
  },
  {
    id: "home_tv_ad",
    title: "TV Commercial Cut",
    tag: "Mode C - TV",
    src: "/TV%20AD/tv-ad.mp4",
    poster: "/hero-poster.jpg",
  },
  {
    id: "home_cinematic_1",
    title: "Narrative Reel",
    tag: "Cinematic Stock",
    src: "/hero-bg-2-lite.webm",
    poster: "/hero-poster.jpg",
  },
  {
    id: "home_cinematic_2",
    title: "Loop Atmosphere",
    tag: "Hero Layer",
    src: "/hero-bg-lite.webm",
    poster: "/hero-poster.jpg",
  },
];

export const ugcModeVideos: GalleryVideoItem[] = [
  {
    id: "ugc_mobile",
    title: "Dreamy Mobile UGC",
    tag: "UGC Mobile",
    src: "/UGC%20Mobile/dreamy-cat.mp4",
    poster: "/hero-poster.jpg",
  },
  {
    id: "ugc_tv",
    title: "Ship Recycling UGC",
    tag: "UGC TV",
    src: "/UGC%20TV/ship-recycling.mp4",
    poster: "/hero-poster.jpg",
  },
  {
    id: "ugc_loop",
    title: "Short-Form Loop Cut",
    tag: "UGC Reference",
    src: "/hero-bg-lite.webm",
    poster: "/hero-poster.jpg",
  },
];

export const proModeVideos: GalleryVideoItem[] = [
  {
    id: "pro_landscape",
    title: "Landscape Narrative",
    tag: "Professional UGC",
    src: "/UGC%20TV/Ugc%20landscape.mp4",
    poster: "/hero-poster.jpg",
  },
  {
    id: "pro_cinematic",
    title: "Cinematic Continuity",
    tag: "Narrative",
    src: "/hero-bg-2-lite.webm",
    poster: "/hero-poster.jpg",
  },
  {
    id: "pro_secondary",
    title: "Secondary Arc Reference",
    tag: "Extend Chain",
    src: "/hero-bg-loop.webm",
    poster: "/hero-poster.jpg",
  },
];

export const tvModeVideos: GalleryVideoItem[] = [
  {
    id: "tv_primary",
    title: "TV Ad Cut",
    tag: "TV AD",
    src: "/TV%20AD/tv-ad.mp4",
    poster: "/hero-poster.jpg",
  },
  {
    id: "tv_scene",
    title: "Scene Assembly Reel",
    tag: "TV Sequence",
    src: "/hero-bg-2-lite.webm",
    poster: "/hero-poster.jpg",
  },
  {
    id: "tv_alt",
    title: "Campaign Alternate",
    tag: "Render Variant",
    src: "/hero-bg-loop.webm",
    poster: "/hero-poster.jpg",
  },
];

