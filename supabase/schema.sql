-- DinkIQ reference corpus + feature vector storage.
-- Region: ca-central-1 (Canadian data residency is a positioning asset).
--
-- Per the build plan's PIPEDA mitigation: raw clips are deleted after
-- feature extraction. Only vectors + metadata persist here -- never
-- store the source video.

create extension if not exists vector;

-- One row per reference-corpus shot. Only coach-approved, reference-grade
-- clips land here (see Phase 1a: a coach labels every clip before it
-- enters the corpus).
create table if not exists reference_shots (
    id uuid primary key default gen_random_uuid(),
    player_level text not null,               -- e.g. '4.5', '5.0'
    shot_type text not null,                   -- launch scope: 'third_shot_drop' only
    paddle_side text not null check (paddle_side in ('left', 'right')),
    embedding vector(8) not null,               -- see pipeline/datatypes.py FEATURE_NAMES for order
    filmed_at date not null,
    release_signed boolean not null default false,
    created_at timestamptz not null default now()
);

create index if not exists reference_shots_embedding_idx
    on reference_shots using ivfflat (embedding vector_l2_ops)
    with (lists = 100);

create index if not exists reference_shots_shot_type_idx
    on reference_shots (shot_type);

-- One row per user-submitted clip analysis. No video_url column on
-- purpose -- clips are processed and discarded, not retained.
create table if not exists clip_analyses (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users (id),
    shot_type text not null,
    paddle_side text not null check (paddle_side in ('left', 'right')),
    embedding vector(8) not null,
    nearest_neighbour_ids uuid[] not null,
    deltas jsonb not null,                      -- FeatureDelta[] as JSON
    coaching_summary text,
    coaching_faults jsonb,
    drill text,
    created_at timestamptz not null default now()
);

create index if not exists clip_analyses_user_id_idx
    on clip_analyses (user_id);

alter table clip_analyses enable row level security;

create policy "users read their own analyses"
    on clip_analyses for select
    using (auth.uid() = user_id);

create policy "users insert their own analyses"
    on clip_analyses for insert
    with check (auth.uid() = user_id);
