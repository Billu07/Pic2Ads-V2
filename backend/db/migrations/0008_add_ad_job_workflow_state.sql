-- Persist workflow gating/approval state (TV concept + storyboard approvals).

alter table public.ad_job
  add column if not exists workflow_state jsonb not null default '{}'::jsonb;

update public.ad_job
set workflow_state = coalesce(workflow_state, '{}'::jsonb)
where workflow_state is null;

create index if not exists ad_job_workflow_state_gin_idx
  on public.ad_job
  using gin (workflow_state);

