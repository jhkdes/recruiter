-- Milestone 3: individual approval and idempotent outbound-email audit trail.
CREATE TABLE email_drafts (
    id UUID PRIMARY KEY, campaign_id UUID NOT NULL REFERENCES campaigns(id), candidate_id UUID NOT NULL REFERENCES candidates(id),
    recipient TEXT NOT NULL, subject TEXT NOT NULL, body TEXT NOT NULL, idempotency_key TEXT NOT NULL UNIQUE, created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE email_approvals (
    id UUID PRIMARY KEY, draft_id UUID NOT NULL UNIQUE REFERENCES email_drafts(id), status TEXT NOT NULL CHECK (status IN ('pending', 'approved', 'rejected')),
    approved_by TEXT, approved_at TIMESTAMPTZ
);
CREATE TABLE email_interactions (
    id UUID PRIMARY KEY, candidate_id UUID NOT NULL REFERENCES candidates(id), draft_id UUID NOT NULL REFERENCES email_drafts(id),
    provider_message_id TEXT NOT NULL, event_type TEXT NOT NULL CHECK (event_type IN ('sent', 'delivered', 'bounced')), occurred_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (draft_id, event_type)
);
CREATE TABLE email_webhooks (event_id TEXT PRIMARY KEY, received_at TIMESTAMPTZ NOT NULL DEFAULT now());
