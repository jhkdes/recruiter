from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from app.domain.models import Campaign, Candidate, CandidateEvidence, CandidateStatus, EvidenceSourceType, ParticipantCriteria


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
        self.connection.commit()

    def get_candidate(self, candidate_id: str) -> Candidate | None:
        row = self.connection.execute("SELECT * FROM candidates WHERE id = ?", (candidate_id,)).fetchone()
        return self._candidate_from_row(row) if row else None

    def list_candidates(self, campaign_id: str) -> list[Candidate]:
        rows = self.connection.execute("SELECT * FROM candidates WHERE campaign_id = ? ORDER BY created_at", (campaign_id,))
        return [self._candidate_from_row(row) for row in rows]

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
        return Candidate(
            id=row["id"], campaign_id=row["campaign_id"], name=row["name"], evidence=evidence,
            status=CandidateStatus(row["status"]), reviewer_note=row["reviewer_note"], created_at=_parse_datetime(row["created_at"]),
        )


def _parse_datetime(value: str):
    from datetime import datetime
    return datetime.fromisoformat(value)
