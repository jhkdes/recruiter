-- Milestone 2: provenance for professional-email discovery and verification.
CREATE TABLE candidate_contacts (
    candidate_id UUID PRIMARY KEY REFERENCES candidates(id) ON DELETE CASCADE,
    email TEXT,
    email_source TEXT CHECK (email_source IN ('hunter', 'apollo', 'uploaded_list')),
    confidence DOUBLE PRECISION,
    verification_status TEXT NOT NULL CHECK (verification_status IN ('verified', 'unverified', 'unavailable')),
    provider_reference TEXT NOT NULL,
    checked_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK ((email IS NULL AND email_source IS NULL) OR (email IS NOT NULL AND email_source IS NOT NULL))
);

CREATE INDEX candidate_contacts_verification_status_idx ON candidate_contacts (verification_status);
