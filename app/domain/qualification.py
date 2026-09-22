from __future__ import annotations

from app.domain.models import (
    Candidate,
    CandidateStatus,
    EvidenceSourceType,
    ParticipantCriteria,
    QualificationResult,
    REQUIRED_CRITERIA,
)


VERIFICATION_SOURCES = {
    EvidenceSourceType.LINKEDIN,
    EvidenceSourceType.PUBLICATION,
    EvidenceSourceType.WEBINAR,
}


def _normalise(value: str) -> str:
    return " ".join(value.casefold().split())


def has_verification_evidence(candidate: Candidate) -> bool:
    return any(
        item.source_type in VERIFICATION_SOURCES
        and item.criterion == "name"
        and _normalise(item.observed_value) == _normalise(candidate.name)
        for item in candidate.evidence
    )


def evaluate_candidate(candidate: Candidate, criteria: ParticipantCriteria) -> QualificationResult:
    """Evaluate only supplied professional evidence; never infer a missing criterion."""
    if not has_verification_evidence(candidate):
        return QualificationResult(
            status=CandidateStatus.REVIEW_REQUIRED,
            matched_criteria=(),
            missing_or_conflicting_criteria=("identity verification source",),
            explanation="A LinkedIn profile, publication, or webinar credential is required to verify the candidate.",
        )

    evidence_by_criterion: dict[str, set[str]] = {}
    for item in candidate.evidence:
        evidence_by_criterion.setdefault(item.criterion, set()).add(_normalise(item.observed_value))

    matched: list[str] = []
    missing_or_conflicting: list[str] = []
    for criterion in REQUIRED_CRITERIA:
        expected = {_normalise(item) for item in criteria.requested_values(criterion)}
        observed = evidence_by_criterion.get(criterion, set())
        if not expected:
            continue
        if not observed:
            missing_or_conflicting.append(f"missing {criterion}")
        elif expected.intersection(observed):
            matched.append(criterion)
        else:
            missing_or_conflicting.append(f"conflicting {criterion}")

    if missing_or_conflicting:
        status = CandidateStatus.REVIEW_REQUIRED if any(item.startswith("missing") for item in missing_or_conflicting) else CandidateStatus.NOT_QUALIFIED
        return QualificationResult(
            status=status,
            matched_criteria=tuple(matched),
            missing_or_conflicting_criteria=tuple(missing_or_conflicting),
            explanation="Candidate needs reviewer attention because qualification evidence is incomplete or does not match the campaign.",
        )

    return QualificationResult(
        status=CandidateStatus.QUALIFIED,
        matched_criteria=tuple(matched),
        missing_or_conflicting_criteria=(),
        explanation="Candidate has verified evidence for every configured target criterion.",
    )
