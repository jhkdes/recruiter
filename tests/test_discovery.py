from __future__ import annotations

from datetime import datetime, timezone
import unittest

from app.adapters import translate_apollo_response, translate_hunter_response, translate_search_results
from app.discovery import build_linkedin_query
from app.domain.models import ParticipantCriteria
from app.ports import EnrichmentMatch, FakeCandidateSearch, FakeEmailVerification, FakeProfessionalEmailEnrichment, SearchLead
from app.repository import InMemoryRecruiterRepository
from app.services import CampaignService, DiscoveryService


class DiscoveryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = InMemoryRecruiterRepository()
        self.campaign = CampaignService(self.repository).create_campaign(
            name="Shipping research", research_goal="Learn about carrier selection", target_completions=3,
            deadline=datetime(2026, 10, 1, tzinfo=timezone.utc),
            criteria=ParticipantCriteria(("Shipping Manager",), ("Distribution",), ("Manager",), ("Texas",)),
        )

    def test_query_uses_explicit_campaign_criteria(self) -> None:
        query = build_linkedin_query(self.campaign)
        self.assertEqual(query, 'site:linkedin.com/in ("Shipping Manager") ("Distribution") ("Manager") ("Texas")')

    def test_apollo_is_used_only_after_hunter_has_no_email(self) -> None:
        search = FakeCandidateSearch([SearchLead("Sam Rivera", "https://linkedin.com/in/sam", "https://search.example/sam", "Example", (
            ("title", "Shipping Manager"), ("industry", "Distribution"), ("seniority", "Manager"), ("region", "Texas"),
        ))])
        hunter = FakeProfessionalEmailEnrichment(EnrichmentMatch(None, "hunter:none", None, False))
        apollo = FakeProfessionalEmailEnrichment(EnrichmentMatch("sam@example.com", "apollo:1", 0.9, True))
        verifier = FakeEmailVerification(EnrichmentMatch("sam@example.com", "verify:1", 0.99, True))
        proposals = DiscoveryService(self.repository, search, hunter, apollo, verifier).discover(self.campaign.id)
        candidate = self.repository.list_candidates(self.campaign.id)[0]
        self.assertEqual(len(hunter.requests), 1)
        self.assertEqual(len(apollo.requests), 1)
        self.assertEqual(candidate.contact.email_source.value, "apollo")
        self.assertTrue(proposals[0].contactable)
        self.assertFalse(hasattr(self.repository, "outreach_commands"))

    def test_captured_provider_payloads_translate_to_port_records(self) -> None:
        leads = translate_search_results([{"name": "Sam Rivera", "profile_url": "https://linkedin.com/in/sam", "source_url": "https://search.example/sam", "evidence": {"title": "Shipping Manager"}}])
        self.assertEqual(leads[0].evidence, (("title", "Shipping Manager"),))
        self.assertTrue(translate_hunter_response({"data": {"email": "sam@example.com", "id": "1", "verification": {"status": "valid"}}}).verified)
        self.assertFalse(translate_apollo_response({"person": {"email": "sam@example.com", "id": "1", "email_status": "guessed"}}).verified)
