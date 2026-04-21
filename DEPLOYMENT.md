# Pic2Ads Deployment Guide

This project is split into:
- `frontend` (Next.js) -> deploy on Vercel
- `backend` (FastAPI) -> deploy on a Python host (Render/Railway/Fly.io)

Recommended domain mapping:
- `pic2ads.io` -> frontend
- `api.pic2ads.io` -> backend

## 1. Push to GitHub

From repository root:

```bash
git init
git add .
git commit -m "chore: initial pic2ads platform setup"
git branch -M main
git remote add origin <YOUR_GITHUB_REPO_URL>
git push -u origin main
```

## 2. Deploy Frontend (Vercel)

In Vercel:
1. Import your GitHub repo.
2. Set **Root Directory** to `frontend`.
3. Framework: Next.js (auto-detected).
4. Add environment variables:
   - `NEXT_PUBLIC_SITE_URL=https://pic2ads.io`
   - `NEXT_PUBLIC_API_BASE_URL=https://api.pic2ads.io/v1`
   - `SUPABASE_URL=<your-supabase-url>`
   - `SUPABASE_SERVICE_ROLE_KEY=<your-service-role-key>`
   - `SUPABASE_STORAGE_BUCKET=product-images`
   - `SUPABASE_STORAGE_PUBLIC_URL=` (optional)
5. Deploy.

## 3. Deploy Backend (Render example)

### Option A: Docker (recommended)
Use `backend/Dockerfile`.

Settings:
- Root directory: `backend`
- Build method: Docker
- Start command: from Dockerfile `CMD`

### Option B: Native Python
- Root directory: `backend`
- Build command:
  - `pip install -r requirements.txt`
- Start command:
  - `python -m app.db.migrate && python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT`

Backend environment variables:
- `APP_ENV=prod`
- `APP_DEBUG=false`
- `API_PREFIX=/v1`
- `DATABASE_URL=<supabase-session-pooler-url>?sslmode=require`
- `OPENAI_API_KEY=<...>`
- `OPENAI_SCRIPT_MODEL=gpt-4.1-mini`
- `FAL_API_KEY=<...>`
- `FAL_CALLBACK_URL=https://api.pic2ads.io/v1/webhooks/fal`
- `FAL_WEBHOOK_SECRET=<optional>`
- `FAL_SEEDANCE_TEXT_ENDPOINT=bytedance/seedance-2.0/text-to-video`
- `FAL_SEEDANCE_IMAGE_ENDPOINT=bytedance/seedance-2.0/image-to-video`
- `FAL_SEEDANCE_REFERENCE_ENDPOINT=bytedance/seedance-2.0/reference-to-video`
- `FAL_RETRY_WORKER_ENABLED=true`
- `FAL_RETRY_WORKER_INTERVAL_SECONDS=20`
- `FAL_RETRY_WORKER_BATCH_SIZE=10`

## 4. Connect Domains

At your DNS provider:

1. Frontend:
   - Connect `pic2ads.io` and `www.pic2ads.io` in Vercel.
   - Add required A/CNAME records as shown by Vercel.

2. Backend:
   - Connect `api.pic2ads.io` in your backend host.
   - Add CNAME record for `api` to backend target host.

## 5. Post-Deploy Verification

1. Frontend:
   - Open `https://pic2ads.io/create`
   - Upload image
   - Create job
   - Run pipeline

2. Backend:
   - `https://api.pic2ads.io/v1/health` should return healthy response.

3. Fal callback:
   - Confirm webhook requests reach:
     - `https://api.pic2ads.io/v1/webhooks/fal`

4. Manifest:
   - Confirm `/jobs/<jobId>` page shows timeline and segment states.
