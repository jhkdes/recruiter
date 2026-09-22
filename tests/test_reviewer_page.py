from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO
import json
import unittest

from app import server
from app.repository import InMemoryRecruiterRepository
from app.services import CampaignService


class ReviewerPageTests(unittest.TestCase):
    def setUp(self) -> None:
        server.repository = InMemoryRecruiterRepository()
        server.service = CampaignService(server.repository)

    def request(self, method: str, path: str, payload: dict | None = None) -> tuple[str, dict, bytes]:
        body = json.dumps(payload or {}).encode("utf-8")
        captured: dict[str, object] = {}

        def start_response(status: str, headers: list[tuple[str, str]]) -> None:
            captured["status"] = status
            captured["headers"] = dict(headers)

        response = server.application({
            "REQUEST_METHOD": method,
            "PATH_INFO": path,
            "CONTENT_LENGTH": str(len(body)),
            "wsgi.input": BytesIO(body),
        }, start_response)
        return captured["status"], captured["headers"], b"".join(response)

    def test_reviewer_page_shows_candidate_evidence(self) -> None:
        campaign_payload = {
            "name": "Shipping research", "research_goal": "Learn about shipping.", "target_completions": 3,
            "deadline": datetime(2026, 10, 1, tzinfo=timezone.utc).isoformat(),
            "criteria": {"titles": ["Shipping Manager"], "industries": ["Distribution"], "seniorities": ["Manager"], "regions": ["Texas"]},
        }
        status, _, body = self.request("POST", "/api/campaigns", campaign_payload)
        self.assertEqual(status, "201 Created")
        campaign_id = json.loads(body)["id"]
        candidate_payload = {
            "name": "Sam Rivera",
            "evidence": [{"criterion": criterion, "observed_value": value, "source_type": "linkedin", "source_url": "https://linkedin.com/in/sam"} for criterion, value in [
                ("name", "Sam Rivera"), ("title", "Shipping Manager"), ("industry", "Distribution"), ("seniority", "Manager"), ("region", "Texas"),
            ]],
        }
        status, _, _ = self.request("POST", f"/api/campaigns/{campaign_id}/candidates", candidate_payload)
        self.assertEqual(status, "201 Created")
        status, headers, page = self.request("GET", "/")
        self.assertEqual(status, "200 OK")
        self.assertEqual(headers["Content-Type"], "text/html; charset=utf-8")
        self.assertIn(b"Sam Rivera", page)
        self.assertIn(b"Shipping Manager", page)
