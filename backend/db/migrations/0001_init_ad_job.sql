-- Pic2Ads initial schema for job storage (Supabase/Postgres)

do $$
begin
  if not exists (
    select 1
    from pg_type t
    join pg_namespace n on n.oid = t.typnamespace
    where t.typname = 'job_mode'
      and n.nspname = 'public'
  ) then
    create type public.job_mode as enum ('ugc', 'pro_arc', 'tv');
  end if;
end $$;

do $$
begin
  if not exists (
    select 1
    from pg_type t
    join pg_namespace n on n.oid = t.typnamespace
    where t.typname = 'job_status'
      and n.nspname = 'public'
  ) then
    create type public.job_status as enum ('queued', 'running', 'completed', 'failed');
  end if;
end $$;

create table if not exists public.ad_job (
  id text primary key,
  brand_id text null,
  mode public.job_mode not null,
  status public.job_status not null default 'queued',
  duration_s integer not null check (duration_s between 10 and 60),
  product_name text not null,
  product_image_url text not null,
  brief text null,
  deliverables jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create index if not exists ad_job_status_created_at_idx
  on public.ad_job (status, created_at desc);

create index if not exists ad_job_brand_id_idx
  on public.ad_job (brand_id)
  where brand_id is not null;

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = timezone('utc', now());
  return new;
end;
$$;

drop trigger if exists trg_ad_job_set_updated_at on public.ad_job;
create trigger trg_ad_job_set_updated_at
before update on public.ad_job
for each row
execute function public.set_updated_at();

