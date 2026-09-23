from __future__ import annotations

from typing import Protocol

from app.domain.models import Campaign, Candidate, EmailApproval, EmailDraft, EmailInteraction


class RecruiterRepository(Protocol):
    def save_campaign(self, campaign: Campaign) -> None: ...
    def get_campaign(self, campaign_id: str) -> Campaign | None: ...
    def list_campaigns(self) -> list[Campaign]: ...
    def save_candidate(self, candidate: Candidate) -> None: ...
    def get_candidate(self, candidate_id: str) -> Candidate | None: ...
    def list_candidates(self, campaign_id: str) -> list[Candidate]: ...
    def save_draft(self, draft: EmailDraft) -> None: ...
    def get_draft(self, draft_id: str) -> EmailDraft | None: ...
    def list_drafts(self, campaign_id: str) -> list[EmailDraft]: ...
    def save_approval(self, approval: EmailApproval) -> None: ...
    def get_approval_for_draft(self, draft_id: str) -> EmailApproval | None: ...
    def save_interaction(self, interaction: EmailInteraction) -> bool: ...
    def has_interaction(self, draft_id: str, event_type: str) -> bool: ...
    def get_interaction_by_provider_message_id(self, provider_message_id: str) -> EmailInteraction | None: ...
    def record_webhook(self, event_id: str) -> bool: ...


class InMemoryRecruiterRepository:
    def __init__(self) -> None:
        self.campaigns: dict[str, Campaign] = {}
        self.candidates: dict[str, Candidate] = {}
        self.drafts: dict[str, EmailDraft] = {}
        self.approvals: dict[str, EmailApproval] = {}
        self.interactions: list[EmailInteraction] = []
        self.webhook_ids: set[str] = set()

    def save_campaign(self, campaign: Campaign) -> None:
        self.campaigns[campaign.id] = campaign

    def get_campaign(self, campaign_id: str) -> Campaign | None:
        return self.campaigns.get(campaign_id)

    def list_campaigns(self) -> list[Campaign]:
        return sorted(self.campaigns.values(), key=lambda campaign: campaign.created_at, reverse=True)

    def save_candidate(self, candidate: Candidate) -> None:
        self.candidates[candidate.id] = candidate

    def get_candidate(self, candidate_id: str) -> Candidate | None:
        return self.candidates.get(candidate_id)

    def list_candidates(self, campaign_id: str) -> list[Candidate]:
        return [candidate for candidate in self.candidates.values() if candidate.campaign_id == campaign_id]

    def save_draft(self, draft: EmailDraft) -> None:
        self.drafts[draft.id] = draft

    def get_draft(self, draft_id: str) -> EmailDraft | None:
        return self.drafts.get(draft_id)

    def list_drafts(self, campaign_id: str) -> list[EmailDraft]:
        return [item for item in self.drafts.values() if item.campaign_id == campaign_id]

    def save_approval(self, approval: EmailApproval) -> None:
        self.approvals[approval.draft_id] = approval

    def get_approval_for_draft(self, draft_id: str) -> EmailApproval | None:
        return self.approvals.get(draft_id)

    def save_interaction(self, interaction: EmailInteraction) -> bool:
        if self.has_interaction(interaction.draft_id, interaction.event_type):
            return False
        self.interactions.append(interaction)
        return True

    def has_interaction(self, draft_id: str, event_type: str) -> bool:
        return any(item.draft_id == draft_id and item.event_type == event_type for item in self.interactions)

    def get_interaction_by_provider_message_id(self, provider_message_id: str) -> EmailInteraction | None:
        return next((item for item in self.interactions if item.provider_message_id == provider_message_id), None)

    def record_webhook(self, event_id: str) -> bool:
        if event_id in self.webhook_ids:
            return False
        self.webhook_ids.add(event_id)
        return True
