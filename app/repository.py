from __future__ import annotations

from typing import Protocol

from app.domain.models import Campaign, Candidate


class RecruiterRepository(Protocol):
    def save_campaign(self, campaign: Campaign) -> None: ...
    def get_campaign(self, campaign_id: str) -> Campaign | None: ...
    def list_campaigns(self) -> list[Campaign]: ...
    def save_candidate(self, candidate: Candidate) -> None: ...
    def get_candidate(self, candidate_id: str) -> Candidate | None: ...
    def list_candidates(self, campaign_id: str) -> list[Candidate]: ...


class InMemoryRecruiterRepository:
    def __init__(self) -> None:
        self.campaigns: dict[str, Campaign] = {}
        self.candidates: dict[str, Candidate] = {}

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
