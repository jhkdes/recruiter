from __future__ import annotations

from app.domain.models import Campaign, Candidate, CandidateProposal, CandidateStatus


def build_linkedin_query(campaign: Campaign) -> str:
    """Build a deterministic public-profile query using only explicit campaign criteria."""
    terms = ["site:linkedin.com/in"]
    for values in (
        campaign.criteria.titles,
        campaign.criteria.industries,
        campaign.criteria.seniorities,
        campaign.criteria.regions,
    ):
        if values:
            terms.append("(" + " OR ".join(f'\"{value}\"' for value in values) + ")")
    return " ".join(terms)


def rank_candidate(candidate: Candidate) -> CandidateProposal:
    score = 0
    reasons: list[str] = []
    if candidate.status == CandidateStatus.QUALIFIED:
        score += 100
        reasons.append("Matches every configured campaign criterion.")
    elif candidate.status == CandidateStatus.REVIEW_REQUIRED:
        score += 25
        reasons.append("Needs reviewer attention before qualification.")
    contactable = bool(candidate.contact and candidate.contact.email and candidate.contact.verification_status.value == "verified")
    if contactable:
        score += 25
        reasons.append("Professional email is verified.")
    elif candidate.contact:
        reasons.append("Professional email requires verification.")
    return CandidateProposal(candidate.id, score, tuple(reasons), contactable)


def rank_candidates(candidates: list[Candidate]) -> list[CandidateProposal]:
    return sorted((rank_candidate(candidate) for candidate in candidates), key=lambda item: (-item.score, item.candidate_id))
