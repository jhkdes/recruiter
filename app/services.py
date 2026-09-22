from __future__ import annotations

from datetime import datetime

from app.domain.models import (
    Campaign,
    Candidate,
    CandidateEvidence,
    CandidateStatus,
    EvidenceSourceType,
    ParticipantCriteria,
    new_id,
)
from app.domain.qualification import evaluate_candidate
from app.domain.qualification import has_verification_evidence
from app.domain.transitions import transition_candidate
from app.repository import RecruiterRepository


class NotFoundError(ValueError):
    pass


class CampaignService:
    def __init__(self, repository: RecruiterRepository) -> None:
        self.repository = repository

    def create_campaign(
        self,
        *,
        name: str,
        research_goal: str,
        target_completions: int,
        deadline: datetime,
        criteria: ParticipantCriteria,
    ) -> Campaign:
        if not name.strip() or not research_goal.strip():
            raise ValueError("Campaign name and research goal are required.")
        if target_completions < 1:
            raise ValueError("Target completions must be at least one.")
        campaign = Campaign(new_id(), name.strip(), research_goal.strip(), target_completions, deadline, criteria)
        self.repository.save_campaign(campaign)
        return campaign

    def import_candidate(self, *, campaign_id: str, name: str, evidence: list[CandidateEvidence]) -> Candidate:
        campaign = self.repository.get_campaign(campaign_id)
        if campaign is None:
            raise NotFoundError("Campaign was not found.")
        if not name.strip():
            raise ValueError("Candidate name is required.")
        candidate = Candidate(id=new_id(), campaign_id=campaign.id, name=name.strip(), evidence=evidence)
        if has_verification_evidence(candidate):
            transition_candidate(candidate, CandidateStatus.VERIFIED)
        result = evaluate_candidate(candidate, campaign.criteria)
        transition_candidate(candidate, result.status)
        self.repository.save_candidate(candidate)
        return candidate

    def decide_uncertain_candidate(self, *, candidate_id: str, include: bool, note: str) -> Candidate:
        candidate = self.repository.get_candidate(candidate_id)
        if candidate is None:
            raise NotFoundError("Candidate was not found.")
        candidate.status = CandidateStatus.QUALIFIED if include else CandidateStatus.NOT_QUALIFIED
        candidate.reviewer_note = note.strip() or None
        self.repository.save_candidate(candidate)
        return candidate


def evidence_from_payload(payload: dict[str, str]) -> CandidateEvidence:
    try:
        source_type = EvidenceSourceType(payload["source_type"])
    except (KeyError, ValueError) as error:
        raise ValueError("Evidence source_type must be linkedin, publication, webinar, uploaded_list, or other_approved_source.") from error
    criterion = payload.get("criterion", "").strip().casefold()
    value = payload.get("observed_value", "").strip()
    url = payload.get("source_url", "").strip()
    if not criterion or not value or not url.startswith(("https://", "http://")):
        raise ValueError("Evidence requires criterion, observed_value, and an http(s) source_url.")
    return CandidateEvidence(criterion=criterion, observed_value=value, source_type=source_type, source_url=url)
