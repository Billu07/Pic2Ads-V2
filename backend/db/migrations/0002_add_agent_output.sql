-- Store structured outputs from individual agents for replayability.

create table if not exists public.agent_output (
  id bigserial primary key,
  job_id text not null references public.ad_job(id) on delete cascade,
  agent_name text not null,
  prompt_version text not null,
  input_hash text not null,
  output jsonb not null,
  tokens_in integer not null default 0,
  tokens_out integer not null default 0,
  cost_usd numeric(12, 6) not null default 0,
  latency_ms integer not null default 0,
  created_at timestamptz not null default timezone('utc', now())
);

create index if not exists agent_output_job_created_idx
  on public.agent_output (job_id, created_at desc);

create index if not exists agent_output_agent_created_idx
  on public.agent_output (agent_name, created_at desc);

create unique index if not exists agent_output_job_agent_input_hash_uidx
  on public.agent_output (job_id, agent_name, input_hash);

