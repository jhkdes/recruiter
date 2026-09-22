from __future__ import annotations

import unittest

from app.ports import EnrichmentMatch, FakeCandidateSearch, FakeProfessionalEmailEnrichment, SearchLead


class PortFakeTests(unittest.TestCase):
    def test_search_fake_records_query_and_returns_copy(self) -> None:
        fake = FakeCandidateSearch([SearchLead("Sam Rivera", "https://linkedin.com/in/sam", "https://google.com/result")])
        results = fake.search("shipping manager Texas")
        results.clear()
        self.assertEqual(fake.queries, ["shipping manager Texas"])
        self.assertEqual(len(fake.results), 1)

    def test_enrichment_fake_records_request(self) -> None:
        fake = FakeProfessionalEmailEnrichment(EnrichmentMatch("sam@example.com", "fake:1", 0.9, True))
        result = fake.find(name="Sam Rivera", company="Example", profile_url="https://linkedin.com/in/sam")
        self.assertEqual(result.email, "sam@example.com")
        self.assertEqual(fake.requests[0]["company"], "Example")
