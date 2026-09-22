from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from app.domain.models import Campaign, Candidate, CandidateEvidence, CandidateStatus, EvidenceSourceType, ParticipantCriteria
from app.persistence.sqlite_repository import SqliteRecruiterRepository


class SqliteRepositoryTests(unittest.TestCase):
    def test_persists_campaign_candidate_and_evidence_across_reopen(self) -> None:
        with TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "recruiter.db"
            campaign = Campaign(
                "campaign-1", "Shipping research", "Learn about shipping", 3,
                datetime(2026, 10, 1, tzinfo=timezone.utc),
                ParticipantCriteria(("Shipping Manager",), ("Distribution",), ("Manager",), ("Texas",)),
            )
            candidate = Candidate(
                "candidate-1", campaign.id, "Sam Rivera",
                [CandidateEvidence("name", "Sam Rivera", EvidenceSourceType.LINKEDIN, "https://linkedin.com/in/sam")],
                CandidateStatus.REVIEW_REQUIRED,
            )
            repository = SqliteRecruiterRepository(database_path)
            repository.save_campaign(campaign)
            repository.save_candidate(candidate)
            repository.close()

            reopened = SqliteRecruiterRepository(database_path)
            stored_campaign = reopened.get_campaign(campaign.id)
            stored_candidate = reopened.get_candidate(candidate.id)
            self.assertEqual(stored_campaign.criteria.regions, ("Texas",))
            self.assertEqual(stored_candidate.status, CandidateStatus.REVIEW_REQUIRED)
            self.assertEqual(stored_candidate.evidence[0].source_url, "https://linkedin.com/in/sam")
            reopened.close()
