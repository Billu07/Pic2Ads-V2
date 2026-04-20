"use client";

import { useEffect, useMemo, useRef, useState } from "react";

type OptimizedVideoProps = {
  src: string;
  poster?: string;
  className?: string;
  autoPlayInView?: boolean;
  loop?: boolean;
  priority?: boolean;
};

function sourceType(src: string): string {
  if (src.endsWith(".webm")) return "video/webm";
  if (src.endsWith(".mp4")) return "video/mp4";
  return "video/webm";
}

export function OptimizedVideo({
  src,
  poster,
  className,
  autoPlayInView = true,
  loop = true,
  priority = false,
}: OptimizedVideoProps) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const [inView, setInView] = useState(priority);
  const [shouldLoad, setShouldLoad] = useState(priority);

  const type = useMemo(() => sourceType(src), [src]);

  useEffect(() => {
    const node = videoRef.current;
    if (!node || priority) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setInView(true);
          setShouldLoad(true);
        } else {
          setInView(false);
        }
      },
      { rootMargin: "280px 0px" },
    );

    observer.observe(node);
    return () => observer.disconnect();
  }, [priority]);

  useEffect(() => {
    if (!autoPlayInView) return;
    const node = videoRef.current;
    if (!node || !shouldLoad) return;

    if (inView) {
      void node.play().catch(() => {});
    } else {
      node.pause();
    }
  }, [autoPlayInView, inView, shouldLoad]);

  return (
    <video
      ref={videoRef}
      className={className}
      muted
      playsInline
      loop={loop}
      preload={priority ? "metadata" : "none"}
      poster={poster}
      aria-hidden="true"
    >
      {shouldLoad && <source src={src} type={type} />}
    </video>
  );
}

