"""Run a local, fixture-backed Milestone 2 discovery demonstration.

This command creates a campaign in the configured local SQLite database and saves a
verified email proposal. It does not make network requests or create outreach work.
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.domain.models import ParticipantCriteria
from app.persistence.sqlite_repository import SqliteRecruiterRepository
from app.ports import EnrichmentMatch, FakeCandidateSearch, FakeEmailVerification, FakeProfessionalEmailEnrichment, SearchLead
from app.services import CampaignService, DiscoveryService


def main() -> None:
    repository = SqliteRecruiterRepository(".data/recruiter.db")
    campaign = CampaignService(repository).create_campaign(
        name="Fixture shipping research",
        research_goal="Learn how shipping managers choose carriers.",
        target_completions=3,
        deadline=datetime(2026, 10, 1, tzinfo=timezone.utc),
        criteria=ParticipantCriteria(
            titles=("Shipping Manager",), industries=("Distribution",),
            seniorities=("Manager",), regions=("Texas",),
        ),
    )
    search = FakeCandidateSearch([SearchLead(
        "Sam Rivera", "https://linkedin.com/in/sam-rivera", "https://search.example/sam-rivera", "Example Distribution",
        (("title", "Shipping Manager"), ("industry", "Distribution"), ("seniority", "Manager"), ("region", "Texas")),
    )])
    proposals = DiscoveryService(
        repository, search,
        FakeProfessionalEmailEnrichment(EnrichmentMatch("sam.rivera@example.com", "hunter:fixture-1", 0.92, True)),
        FakeProfessionalEmailEnrichment(),
        FakeEmailVerification(EnrichmentMatch("sam.rivera@example.com", "verification:fixture-1", 0.99, True)),
    ).discover(campaign.id)
    print(f"Created fixture campaign: {campaign.id}")
    print(f"Search query: {search.queries[0]}")
    for proposal in proposals:
        print(f"Candidate {proposal.candidate_id}: priority {proposal.score}; contactable={proposal.contactable}")
    repository.close()


if __name__ == "__main__":
    main()
