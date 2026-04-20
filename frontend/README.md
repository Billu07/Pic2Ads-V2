# Pic2Ads Frontend (Next.js)

SEO-first frontend scaffold for Pic2Ads using Next.js App Router.

## Includes
- Next.js App Router + TypeScript baseline
- Metadata architecture with canonical URLs
- Open Graph + Twitter metadata
- `sitemap.xml` and `robots.txt` routes
- Core indexable pages aligned to product modes:
  - `/`
  - `/create`
  - `/ugc-video-ads`
  - `/professional-video-ads`
  - `/tv-commercial-ai`
  - `/pricing`
- Same-origin API proxy routes for backend orchestration:
  - `POST /api/jobs` -> backend `POST /v1/jobs`
  - `POST /api/jobs/[jobId]/run-local` -> backend `POST /v1/jobs/{jobId}/pipeline/run-local`
  - `POST /api/media/upload` -> Supabase Storage object upload (server-side)
- Job manifest page connected to backend:
  - `/jobs/[jobId]` -> `GET /v1/jobs/{job_id}/export/manifest`

## Environment
Copy `.env.example` to `.env.local` and set values:

```bash
NEXT_PUBLIC_SITE_URL=https://pic2ads.io
NEXT_PUBLIC_API_BASE_URL=https://api.pic2ads.io/v1
SUPABASE_URL=https://YOUR-PROJECT.supabase.co
SUPABASE_SERVICE_ROLE_KEY=YOUR_SERVICE_ROLE_KEY
SUPABASE_STORAGE_BUCKET=product-images
# optional custom public base, otherwise defaults to ${SUPABASE_URL}/storage/v1/object/public
SUPABASE_STORAGE_PUBLIC_URL=
```

Notes:
- `SUPABASE_SERVICE_ROLE_KEY` is server-only in Next route handlers; do not expose it to the browser.
- Create the storage bucket before uploading.

## Local run
```bash
npm install
npm run dev
```

## SEO policy
This codebase is set up for standards-compliant SEO: indexable architecture, intent-based page targeting, structured metadata, and technical crawl hygiene.
Avoid manipulative tactics such as cloaking, hidden text, doorway pages, or automated link spam.
