from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from app.domain.models import (
    Campaign, Candidate, CandidateEvidence, CandidateStatus, ContactResult, EmailSourceType,
    EmailVerificationStatus, EvidenceSourceType, ParticipantCriteria,
    ApprovalStatus, EmailApproval, EmailDraft, EmailInteraction,
)


class SqliteRecruiterRepository:
    """Durable local repository used for development and repository contract tests.

    Production uses the matching Supabase/Postgres migration in ``supabase/migrations``.
    """

    def __init__(self, database_path: str | Path) -> None:
        self.connection = sqlite3.connect(database_path)
        self.connection.row_factory = sqlite3.Row
        self._migrate()

    def close(self) -> None:
        self.connection.close()

    def _migrate(self) -> None:
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS campaigns (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                research_goal TEXT NOT NULL,
                target_completions INTEGER NOT NULL,
                deadline TEXT NOT NULL,
                criteria_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS candidates (
                id TEXT PRIMARY KEY,
                campaign_id TEXT NOT NULL REFERENCES campaigns(id),
                name TEXT NOT NULL,
                status TEXT NOT NULL,
                reviewer_note TEXT,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS candidate_evidence (
                candidate_id TEXT NOT NULL REFERENCES candidates(id),
                criterion TEXT NOT NULL,
                observed_value TEXT NOT NULL,
                source_type TEXT NOT NULL,
                source_url TEXT NOT NULL,
                captured_at TEXT NOT NULL,
                PRIMARY KEY (candidate_id, criterion, source_url, observed_value)
            );
            CREATE TABLE IF NOT EXISTS candidate_contacts (
                candidate_id TEXT PRIMARY KEY REFERENCES candidates(id) ON DELETE CASCADE,
                email TEXT,
                email_source TEXT,
                confidence REAL,
                verification_status TEXT NOT NULL,
                provider_reference TEXT NOT NULL,
                checked_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS email_drafts (id TEXT PRIMARY KEY, campaign_id TEXT NOT NULL, candidate_id TEXT NOT NULL, recipient TEXT NOT NULL, subject TEXT NOT NULL, body TEXT NOT NULL, idempotency_key TEXT NOT NULL UNIQUE, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS email_approvals (id TEXT PRIMARY KEY, draft_id TEXT NOT NULL UNIQUE, status TEXT NOT NULL, approved_by TEXT, approved_at TEXT);
            CREATE TABLE IF NOT EXISTS email_interactions (id TEXT PRIMARY KEY, candidate_id TEXT NOT NULL, draft_id TEXT NOT NULL, provider_message_id TEXT NOT NULL, event_type TEXT NOT NULL, occurred_at TEXT NOT NULL, UNIQUE(draft_id, event_type));
            CREATE TABLE IF NOT EXISTS email_webhooks (event_id TEXT PRIMARY KEY);
            """
        )
        self.connection.commit()

    def save_campaign(self, campaign: Campaign) -> None:
        criteria = {
            "titles": campaign.criteria.titles,
            "industries": campaign.criteria.industries,
            "seniorities": campaign.criteria.seniorities,
            "regions": campaign.criteria.regions,
        }
        self.connection.execute(
            """INSERT INTO campaigns (id, name, research_goal, target_completions, deadline, criteria_json, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET name=excluded.name, research_goal=excluded.research_goal,
               target_completions=excluded.target_completions, deadline=excluded.deadline, criteria_json=excluded.criteria_json""",
            (campaign.id, campaign.name, campaign.research_goal, campaign.target_completions, campaign.deadline.isoformat(), json.dumps(criteria), campaign.created_at.isoformat()),
        )
        self.connection.commit()

    def get_campaign(self, campaign_id: str) -> Campaign | None:
        row = self.connection.execute("SELECT * FROM campaigns WHERE id = ?", (campaign_id,)).fetchone()
        return self._campaign_from_row(row) if row else None

    def list_campaigns(self) -> list[Campaign]:
        return [self._campaign_from_row(row) for row in self.connection.execute("SELECT * FROM campaigns ORDER BY created_at DESC")]

    def save_candidate(self, candidate: Candidate) -> None:
        self.connection.execute(
            """INSERT INTO candidates (id, campaign_id, name, status, reviewer_note, created_at)
               VALUES (?, ?, ?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET status=excluded.status, reviewer_note=excluded.reviewer_note, name=excluded.name""",
            (candidate.id, candidate.campaign_id, candidate.name, candidate.status.value, candidate.reviewer_note, candidate.created_at.isoformat()),
        )
        self.connection.execute("DELETE FROM candidate_evidence WHERE candidate_id = ?", (candidate.id,))
        self.connection.executemany(
            """INSERT INTO candidate_evidence (candidate_id, criterion, observed_value, source_type, source_url, captured_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            [(candidate.id, item.criterion, item.observed_value, item.source_type.value, item.source_url, item.captured_at.isoformat()) for item in candidate.evidence],
        )
        self.connection.execute("DELETE FROM candidate_contacts WHERE candidate_id = ?", (candidate.id,))
        if candidate.contact:
            contact = candidate.contact
            self.connection.execute(
                """INSERT INTO candidate_contacts (candidate_id, email, email_source, confidence, verification_status, provider_reference, checked_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (candidate.id, contact.email, contact.email_source.value if contact.email_source else None, contact.confidence,
                 contact.verification_status.value, contact.provider_reference, contact.checked_at.isoformat()),
            )
        self.connection.commit()

    def get_candidate(self, candidate_id: str) -> Candidate | None:
        row = self.connection.execute("SELECT * FROM candidates WHERE id = ?", (candidate_id,)).fetchone()
        return self._candidate_from_row(row) if row else None

    def list_candidates(self, campaign_id: str) -> list[Candidate]:
        rows = self.connection.execute("SELECT * FROM candidates WHERE campaign_id = ? ORDER BY created_at", (campaign_id,))
        return [self._candidate_from_row(row) for row in rows]

    def save_draft(self, draft: EmailDraft) -> None:
        self.connection.execute("INSERT OR REPLACE INTO email_drafts VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (draft.id, draft.campaign_id, draft.candidate_id, draft.recipient, draft.subject, draft.body, draft.idempotency_key, draft.created_at.isoformat()))
        self.connection.commit()

    def get_draft(self, draft_id: str) -> EmailDraft | None:
        row = self.connection.execute("SELECT * FROM email_drafts WHERE id = ?", (draft_id,)).fetchone()
        return EmailDraft(row["id"], row["campaign_id"], row["candidate_id"], row["recipient"], row["subject"], row["body"], row["idempotency_key"], _parse_datetime(row["created_at"])) if row else None

    def list_drafts(self, campaign_id: str) -> list[EmailDraft]:
        return [self.get_draft(row["id"]) for row in self.connection.execute("SELECT id FROM email_drafts WHERE campaign_id = ?", (campaign_id,))]

    def save_approval(self, approval: EmailApproval) -> None:
        self.connection.execute("INSERT OR REPLACE INTO email_approvals VALUES (?, ?, ?, ?, ?)", (approval.id, approval.draft_id, approval.status.value, approval.approved_by, approval.approved_at.isoformat() if approval.approved_at else None))
        self.connection.commit()

    def get_approval_for_draft(self, draft_id: str) -> EmailApproval | None:
        row = self.connection.execute("SELECT * FROM email_approvals WHERE draft_id = ?", (draft_id,)).fetchone()
        return EmailApproval(row["id"], row["draft_id"], ApprovalStatus(row["status"]), row["approved_by"], _parse_datetime(row["approved_at"]) if row["approved_at"] else None) if row else None

    def save_interaction(self, interaction: EmailInteraction) -> bool:
        try:
            self.connection.execute("INSERT INTO email_interactions VALUES (?, ?, ?, ?, ?, ?)", (interaction.id, interaction.candidate_id, interaction.draft_id, interaction.provider_message_id, interaction.event_type, interaction.occurred_at.isoformat()))
            self.connection.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def has_interaction(self, draft_id: str, event_type: str) -> bool:
        return self.connection.execute("SELECT 1 FROM email_interactions WHERE draft_id = ? AND event_type = ?", (draft_id, event_type)).fetchone() is not None

    def get_interaction_by_provider_message_id(self, provider_message_id: str) -> EmailInteraction | None:
        row = self.connection.execute("SELECT * FROM email_interactions WHERE provider_message_id = ? ORDER BY occurred_at LIMIT 1", (provider_message_id,)).fetchone()
        return EmailInteraction(row["id"], row["candidate_id"], row["draft_id"], row["provider_message_id"], row["event_type"], _parse_datetime(row["occurred_at"])) if row else None

    def record_webhook(self, event_id: str) -> bool:
        try:
            self.connection.execute("INSERT INTO email_webhooks VALUES (?)", (event_id,))
            self.connection.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def _campaign_from_row(self, row: sqlite3.Row) -> Campaign:
        criteria = json.loads(row["criteria_json"])
        return Campaign(
            id=row["id"], name=row["name"], research_goal=row["research_goal"], target_completions=row["target_completions"],
            deadline=_parse_datetime(row["deadline"]),
            criteria=ParticipantCriteria(tuple(criteria["titles"]), tuple(criteria["industries"]), tuple(criteria["seniorities"]), tuple(criteria["regions"])),
            created_at=_parse_datetime(row["created_at"]),
        )

    def _candidate_from_row(self, row: sqlite3.Row) -> Candidate:
        evidence_rows = self.connection.execute("SELECT * FROM candidate_evidence WHERE candidate_id = ?", (row["id"],))
        evidence = [
            CandidateEvidence(
                criterion=item["criterion"], observed_value=item["observed_value"], source_type=EvidenceSourceType(item["source_type"]),
                source_url=item["source_url"], captured_at=_parse_datetime(item["captured_at"]),
            )
            for item in evidence_rows
        ]
        contact_row = self.connection.execute("SELECT * FROM candidate_contacts WHERE candidate_id = ?", (row["id"],)).fetchone()
        contact = ContactResult(
            email=contact_row["email"], email_source=EmailSourceType(contact_row["email_source"]) if contact_row["email_source"] else None,
            confidence=contact_row["confidence"], verification_status=EmailVerificationStatus(contact_row["verification_status"]),
            provider_reference=contact_row["provider_reference"], checked_at=_parse_datetime(contact_row["checked_at"]),
        ) if contact_row else None
        return Candidate(
            id=row["id"], campaign_id=row["campaign_id"], name=row["name"], evidence=evidence,
            status=CandidateStatus(row["status"]), reviewer_note=row["reviewer_note"], contact=contact, created_at=_parse_datetime(row["created_at"]),
        )


def _parse_datetime(value: str):
    from datetime import datetime
    return datetime.fromisoformat(value)
