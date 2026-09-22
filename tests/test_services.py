from __future__ import annotations

from datetime import datetime, timezone
import unittest

from app.domain.models import CandidateStatus, ParticipantCriteria
from app.repository import InMemoryRecruiterRepository
from app.services import CampaignService, evidence_from_payload


class CampaignServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = InMemoryRecruiterRepository()
        self.service = CampaignService(self.repository)
        self.campaign = self.service.create_campaign(
            name="Shipping research", research_goal="Learn about carrier selection.", target_completions=5,
            deadline=datetime(2026, 10, 1, tzinfo=timezone.utc),
            criteria=ParticipantCriteria(titles=("Shipping Manager",), industries=("Distribution",), seniorities=("Manager",), regions=("Texas",)),
        )

    def test_imported_candidate_is_evaluated_and_saved(self) -> None:
        evidence = [
            evidence_from_payload({"criterion": "name", "observed_value": "Sam Rivera", "source_type": "linkedin", "source_url": "https://linkedin.com/in/sam"}),
            evidence_from_payload({"criterion": "title", "observed_value": "Shipping Manager", "source_type": "linkedin", "source_url": "https://linkedin.com/in/sam"}),
            evidence_from_payload({"criterion": "industry", "observed_value": "Distribution", "source_type": "linkedin", "source_url": "https://linkedin.com/in/sam"}),
            evidence_from_payload({"criterion": "seniority", "observed_value": "Manager", "source_type": "linkedin", "source_url": "https://linkedin.com/in/sam"}),
            evidence_from_payload({"criterion": "region", "observed_value": "Texas", "source_type": "linkedin", "source_url": "https://linkedin.com/in/sam"}),
        ]
        candidate = self.service.import_candidate(campaign_id=self.campaign.id, name="Sam Rivera", evidence=evidence)
        self.assertEqual(candidate.status, CandidateStatus.QUALIFIED)
        self.assertEqual(self.repository.get_candidate(candidate.id).name, "Sam Rivera")

    def test_reviewer_can_include_uncertain_candidate(self) -> None:
        candidate = self.service.import_candidate(
            campaign_id=self.campaign.id, name="Sam Rivera",
            evidence=[
                evidence_from_payload({"criterion": "name", "observed_value": "Sam Rivera", "source_type": "linkedin", "source_url": "https://linkedin.com/in/sam"}),
                evidence_from_payload({"criterion": "title", "observed_value": "Shipping Manager", "source_type": "linkedin", "source_url": "https://linkedin.com/in/sam"}),
            ],
        )
        self.assertEqual(candidate.status, CandidateStatus.REVIEW_REQUIRED)
        decided = self.service.decide_uncertain_candidate(candidate_id=candidate.id, include=True, note="Known fit from prior research")
        self.assertEqual(decided.status, CandidateStatus.QUALIFIED)
        self.assertEqual(decided.reviewer_note, "Known fit from prior research")
