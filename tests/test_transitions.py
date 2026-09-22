from __future__ import annotations

import unittest

from app.domain.models import Candidate, CandidateStatus
from app.domain.transitions import InvalidCandidateTransition, transition_candidate


class CandidateTransitionTests(unittest.TestCase):
    def test_allows_discovered_to_verified_then_qualified(self) -> None:
        candidate = Candidate("candidate-1", "campaign-1", "Alex Lee")
        transition_candidate(candidate, CandidateStatus.VERIFIED)
        transition_candidate(candidate, CandidateStatus.QUALIFIED)
        self.assertEqual(candidate.status, CandidateStatus.QUALIFIED)

    def test_rejects_skipping_verification(self) -> None:
        candidate = Candidate("candidate-1", "campaign-1", "Alex Lee")
        with self.assertRaises(InvalidCandidateTransition):
            transition_candidate(candidate, CandidateStatus.QUALIFIED)

    def test_allows_reviewer_to_resolve_review_required_candidate(self) -> None:
        candidate = Candidate("candidate-1", "campaign-1", "Alex Lee", status=CandidateStatus.REVIEW_REQUIRED)
        transition_candidate(candidate, CandidateStatus.NOT_QUALIFIED)
        self.assertEqual(candidate.status, CandidateStatus.NOT_QUALIFIED)
