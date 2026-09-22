from __future__ import annotations

import unittest

from app.domain.models import Candidate, CandidateEvidence, CandidateStatus, EvidenceSourceType, ParticipantCriteria
from app.domain.qualification import evaluate_candidate


class QualificationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.criteria = ParticipantCriteria(
            titles=("Logistics Manager",), industries=("Industrial Distribution",),
            seniorities=("Manager",), regions=("California",),
        )

    def evidence(self, criterion: str, value: str) -> CandidateEvidence:
        return CandidateEvidence(criterion, value, EvidenceSourceType.LINKEDIN, "https://linkedin.com/in/alex")

    def test_qualifies_candidate_with_all_required_evidence(self) -> None:
        candidate = Candidate("candidate-1", "campaign-1", "Alex Lee", [
            self.evidence("name", "Alex Lee"),
            self.evidence("title", "Logistics Manager"), self.evidence("industry", "Industrial Distribution"),
            self.evidence("seniority", "Manager"), self.evidence("region", "California"),
        ])
        result = evaluate_candidate(candidate, self.criteria)
        self.assertEqual(result.status, CandidateStatus.QUALIFIED)
        self.assertEqual(result.matched_criteria, ("title", "industry", "seniority", "region"))

    def test_requires_review_when_verification_evidence_is_missing(self) -> None:
        candidate = Candidate("candidate-1", "campaign-1", "Alex Lee", [
            CandidateEvidence("title", "Logistics Manager", EvidenceSourceType.UPLOADED_LIST, "https://example.com/list"),
        ])
        result = evaluate_candidate(candidate, self.criteria)
        self.assertEqual(result.status, CandidateStatus.REVIEW_REQUIRED)
        self.assertIn("identity verification source", result.missing_or_conflicting_criteria)

    def test_requires_review_when_source_name_does_not_match_candidate(self) -> None:
        candidate = Candidate("candidate-1", "campaign-1", "Alex Lee", [
            self.evidence("name", "Taylor Chen"), self.evidence("title", "Logistics Manager"),
        ])
        result = evaluate_candidate(candidate, self.criteria)
        self.assertEqual(result.status, CandidateStatus.REVIEW_REQUIRED)
        self.assertIn("identity verification source", result.missing_or_conflicting_criteria)

    def test_requires_review_when_a_criterion_is_not_present(self) -> None:
        candidate = Candidate("candidate-1", "campaign-1", "Alex Lee", [
            self.evidence("name", "Alex Lee"),
            self.evidence("title", "Logistics Manager"), self.evidence("industry", "Industrial Distribution"),
            self.evidence("seniority", "Manager"),
        ])
        result = evaluate_candidate(candidate, self.criteria)
        self.assertEqual(result.status, CandidateStatus.REVIEW_REQUIRED)
        self.assertIn("missing region", result.missing_or_conflicting_criteria)

    def test_rejects_candidate_when_evidence_conflicts(self) -> None:
        candidate = Candidate("candidate-1", "campaign-1", "Alex Lee", [
            self.evidence("name", "Alex Lee"),
            self.evidence("title", "Logistics Manager"), self.evidence("industry", "Industrial Distribution"),
            self.evidence("seniority", "Manager"), self.evidence("region", "Nevada"),
        ])
        result = evaluate_candidate(candidate, self.criteria)
        self.assertEqual(result.status, CandidateStatus.NOT_QUALIFIED)
        self.assertIn("conflicting region", result.missing_or_conflicting_criteria)
