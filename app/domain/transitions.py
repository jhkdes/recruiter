from __future__ import annotations

from app.domain.models import Candidate, CandidateStatus


ALLOWED_TRANSITIONS: dict[CandidateStatus, frozenset[CandidateStatus]] = {
    CandidateStatus.DISCOVERED: frozenset({CandidateStatus.VERIFIED, CandidateStatus.REVIEW_REQUIRED}),
    CandidateStatus.VERIFIED: frozenset({CandidateStatus.QUALIFIED, CandidateStatus.NOT_QUALIFIED, CandidateStatus.REVIEW_REQUIRED}),
    CandidateStatus.REVIEW_REQUIRED: frozenset({CandidateStatus.QUALIFIED, CandidateStatus.NOT_QUALIFIED}),
    CandidateStatus.QUALIFIED: frozenset(),
    CandidateStatus.NOT_QUALIFIED: frozenset(),
}


class InvalidCandidateTransition(ValueError):
    pass


def transition_candidate(candidate: Candidate, target: CandidateStatus) -> Candidate:
    """Apply an explicit lifecycle transition or reject it without mutation."""
    if candidate.status == target:
        return candidate
    if target not in ALLOWED_TRANSITIONS[candidate.status]:
        raise InvalidCandidateTransition(f"Cannot transition candidate from {candidate.status} to {target}.")
    candidate.status = target
    return candidate
