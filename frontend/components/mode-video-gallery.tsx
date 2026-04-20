import { OptimizedVideo } from "@/components/optimized-video";
import type { GalleryVideoItem } from "@/lib/video-library";

type ModeVideoGalleryProps = {
  eyebrow: string;
  title: string;
  intro: string;
  items: GalleryVideoItem[];
};

export function ModeVideoGallery({ eyebrow, title, intro, items }: ModeVideoGalleryProps) {
  return (
    <section className="section mode-gallery reveal delay-1">
      <p className="eyebrow">{eyebrow}</p>
      <h2>{title}</h2>
      <p className="section-intro">{intro}</p>
      <div className="mode-gallery-grid">
        {items.map((item) => (
          <article key={item.id} className="mode-gallery-card">
            <OptimizedVideo
              className="mode-gallery-video"
              src={item.src}
              poster={item.poster ?? "/hero-poster.jpg"}
            />
            <div className="mode-gallery-meta">
              <p>{item.tag}</p>
              <h3>{item.title}</h3>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

