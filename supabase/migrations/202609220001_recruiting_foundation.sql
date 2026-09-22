-- Supabase/Postgres source of truth for Milestone 0 and Milestone 1 facts.
CREATE TABLE campaigns (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL CHECK (length(trim(name)) > 0),
    research_goal TEXT NOT NULL CHECK (length(trim(research_goal)) > 0),
    target_completions INTEGER NOT NULL CHECK (target_completions > 0),
    deadline TIMESTAMPTZ NOT NULL,
    criteria JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE candidates (
    id UUID PRIMARY KEY,
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE RESTRICT,
    name TEXT NOT NULL CHECK (length(trim(name)) > 0),
    status TEXT NOT NULL CHECK (status IN ('discovered', 'verified', 'qualified', 'not_qualified', 'review_required')),
    reviewer_note TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX candidates_campaign_id_idx ON candidates (campaign_id);
CREATE INDEX candidates_campaign_status_idx ON candidates (campaign_id, status);

CREATE TABLE candidate_evidence (
    id UUID PRIMARY KEY,
    candidate_id UUID NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    criterion TEXT NOT NULL,
    observed_value TEXT NOT NULL,
    source_type TEXT NOT NULL CHECK (source_type IN ('linkedin', 'publication', 'webinar', 'uploaded_list', 'other_approved_source')),
    source_url TEXT NOT NULL CHECK (source_url ~ '^https?://'),
    captured_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (candidate_id, criterion, source_url, observed_value)
);

CREATE INDEX candidate_evidence_candidate_id_idx ON candidate_evidence (candidate_id);
