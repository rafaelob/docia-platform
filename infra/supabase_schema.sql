-- MedflowAI Supabase schema
-- Tables: cases, consultations

create table if not exists cases (
  id uuid primary key default gen_random_uuid(),
  patient_id uuid not null,
  specialty text not null,
  description text,
  created_at timestamptz default now()
);

create table if not exists consultations (
  id uuid primary key default gen_random_uuid(),
  case_id uuid references cases(id) on delete cascade,
  request jsonb not null,
  response jsonb,
  created_at timestamptz default now()
);
