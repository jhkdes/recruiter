from __future__ import annotations

from dataclasses import replace
from datetime import datetime

from app.domain.models import (
    Campaign,
    Candidate,
    CandidateEvidence,
    CandidateStatus,
    ContactResult,
    EmailSourceType,
    EmailVerificationStatus,
    ApprovalStatus,
    EmailApproval,
    EmailDraft,
    EmailInteraction,
    EvidenceSourceType,
    ParticipantCriteria,
    new_id,
)
from app.discovery import build_linkedin_query, rank_candidates
from app.domain.qualification import evaluate_candidate
from app.domain.qualification import has_verification_evidence
from app.domain.transitions import transition_candidate
from app.ports import CandidateSearchPort, EmailSendPort, EmailVerificationPort, ProfessionalEmailEnrichmentPort
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


class DiscoveryService:
    """Fixture-safe discovery and contact proposal flow. It never creates outreach work."""

    def __init__(
        self,
        repository: RecruiterRepository,
        search: CandidateSearchPort,
        hunter: ProfessionalEmailEnrichmentPort,
        apollo: ProfessionalEmailEnrichmentPort,
        verifier: EmailVerificationPort,
    ) -> None:
        self.repository = repository
        self.search = search
        self.hunter = hunter
        self.apollo = apollo
        self.verifier = verifier
        self.campaigns = CampaignService(repository)

    def discover(self, campaign_id: str):
        campaign = self.repository.get_campaign(campaign_id)
        if campaign is None:
            raise NotFoundError("Campaign was not found.")
        for lead in self.search.search(build_linkedin_query(campaign)):
            evidence = [
                CandidateEvidence("name", lead.name, EvidenceSourceType.LINKEDIN, lead.profile_url),
                CandidateEvidence("linkedin_profile", lead.profile_url, EvidenceSourceType.LINKEDIN, lead.profile_url),
            ]
            evidence.extend(CandidateEvidence(key, value, EvidenceSourceType.LINKEDIN, lead.profile_url) for key, value in lead.evidence)
            candidate = self.campaigns.import_candidate(campaign_id=campaign_id, name=lead.name, evidence=evidence)
            if candidate.status == CandidateStatus.QUALIFIED:
                self._propose_contact(candidate, lead.company, lead.profile_url)
        return rank_candidates(self.repository.list_candidates(campaign_id))

    def _propose_contact(self, candidate: Candidate, company: str, profile_url: str) -> None:
        result = self.hunter.find(name=candidate.name, company=company, profile_url=profile_url)
        source = EmailSourceType.HUNTER
        if not result.email:
            result = self.apollo.find(name=candidate.name, company=company, profile_url=profile_url)
            source = EmailSourceType.APOLLO
        if not result.email:
            candidate.contact = ContactResult(None, None, result.confidence, EmailVerificationStatus.UNAVAILABLE, result.provider_reference)
        else:
            verification = self.verifier.verify(result.email)
            candidate.contact = ContactResult(
                result.email, source, result.confidence,
                EmailVerificationStatus.VERIFIED if verification.verified else EmailVerificationStatus.UNVERIFIED,
                verification.provider_reference,
            )
        self.repository.save_candidate(candidate)


class OutreachService:
    def __init__(self, repository: RecruiterRepository, sender: EmailSendPort, *, identity_url: str, scheduling_url: str) -> None:
        self.repository = repository
        self.sender = sender
        self.identity_url = identity_url
        self.scheduling_url = scheduling_url

    def propose_initial_email(self, candidate_id: str) -> tuple[EmailDraft, EmailApproval]:
        candidate = self._candidate(candidate_id)
        campaign = self.repository.get_campaign(candidate.campaign_id)
        if candidate.status != CandidateStatus.QUALIFIED or not candidate.contact or not candidate.contact.email or candidate.contact.verification_status != EmailVerificationStatus.VERIFIED:
            raise ValueError("Only qualified candidates with a verified professional email can receive an email proposal.")
        transition_candidate(candidate, CandidateStatus.CONTACTABLE)
        transition_candidate(candidate, CandidateStatus.PROPOSED_FOR_REVIEW)
        draft = EmailDraft(
            new_id(), campaign.id, candidate.id, candidate.contact.email,
            f"Invitation: {campaign.research_goal}",
            self._message_body(candidate.name, campaign.research_goal),
            f"initial-email:{candidate.id}",
        )
        approval = EmailApproval(new_id(), draft.id)
        self.repository.save_candidate(candidate)
        self.repository.save_draft(draft)
        self.repository.save_approval(approval)
        return draft, approval

    def approve(self, draft_id: str, reviewer: str) -> EmailApproval:
        draft = self.repository.get_draft(draft_id)
        approval = self.repository.get_approval_for_draft(draft_id)
        if draft is None or approval is None:
            raise NotFoundError("Email proposal was not found.")
        if approval.status != ApprovalStatus.PENDING:
            raise ValueError("Email proposal has already been decided.")
        approval.status, approval.approved_by, approval.approved_at = ApprovalStatus.APPROVED, reviewer.strip() or "reviewer", datetime.now().astimezone()
        candidate = self._candidate(draft.candidate_id)
        transition_candidate(candidate, CandidateStatus.APPROVED_FOR_OUTREACH)
        self.repository.save_approval(approval)
        self.repository.save_candidate(candidate)
        return approval

    def revise_draft(self, draft_id: str, *, subject: str, body: str) -> EmailDraft:
        draft = self.repository.get_draft(draft_id)
        approval = self.repository.get_approval_for_draft(draft_id)
        if draft is None or approval is None:
            raise NotFoundError("Email proposal was not found.")
        if approval.status != ApprovalStatus.PENDING:
            raise ValueError("Only a pending email proposal can be edited.")
        if not subject.strip() or not body.strip():
            raise ValueError("Email subject and body are required.")
        revised = replace(draft, subject=subject.strip(), body=body.strip())
        self.repository.save_draft(revised)
        return revised

    def send_approved(self, draft_id: str) -> EmailInteraction:
        draft = self.repository.get_draft(draft_id)
        approval = self.repository.get_approval_for_draft(draft_id)
        if draft is None or approval is None or approval.status != ApprovalStatus.APPROVED:
            raise ValueError("An individual approved email proposal is required before sending.")
        if self.repository.has_interaction(draft.id, "sent"):
            raise ValueError("This email has already been sent.")
        result = self.sender.send(recipient=draft.recipient, subject=draft.subject, body=draft.body, idempotency_key=draft.idempotency_key)
        interaction = EmailInteraction(new_id(), draft.candidate_id, draft.id, result.provider_message_id, "sent")
        self.repository.save_interaction(interaction)
        candidate = self._candidate(draft.candidate_id)
        transition_candidate(candidate, CandidateStatus.CONTACTED)
        self.repository.save_candidate(candidate)
        return interaction

    def process_delivery_webhook(self, *, event_id: str, provider_message_id: str, event_type: str) -> bool:
        if event_type not in {"delivered", "bounced"}:
            raise ValueError("Only delivered and bounced email webhook events are supported.")
        if not self.repository.record_webhook(event_id):
            return False
        interaction = self.repository.get_interaction_by_provider_message_id(provider_message_id)
        if interaction is None:
            raise NotFoundError("Email interaction was not found.")
        self.repository.save_interaction(EmailInteraction(new_id(), interaction.candidate_id, interaction.draft_id, provider_message_id, event_type))
        if event_type == "bounced":
            candidate = self._candidate(interaction.candidate_id)
            transition_candidate(candidate, CandidateStatus.BOUNCED)
            self.repository.save_candidate(candidate)
        return True

    def _candidate(self, candidate_id: str) -> Candidate:
        candidate = self.repository.get_candidate(candidate_id)
        if candidate is None:
            raise NotFoundError("Candidate was not found.")
        return candidate

    def _message_body(self, name: str, research_goal: str) -> str:
        return (f"Hi {name},\n\nWe are researching {research_goal}. Your public professional experience appears relevant. "
                f"This is a 30-minute conversation with a Discover First researcher, with no monetary incentive. "
                f"You can learn more about us at {self.identity_url} and choose a time at {self.scheduling_url}. "
                "If you would rather not hear from us, reply to decline or opt out.\n")

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
