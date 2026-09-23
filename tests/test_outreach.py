from __future__ import annotations

import unittest
from datetime import datetime, timezone

from app.domain.models import Candidate, CandidateStatus, ContactResult, EmailSourceType, EmailVerificationStatus, ParticipantCriteria
from app.ports import FakeEmailSender
from app.repository import InMemoryRecruiterRepository
from app.services import CampaignService, OutreachService


class OutreachTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = InMemoryRecruiterRepository()
        self.campaign = CampaignService(self.repository).create_campaign(
            name="Shipping research", research_goal="carrier selection", target_completions=3,
            deadline=datetime(2026, 10, 1, tzinfo=timezone.utc), criteria=ParticipantCriteria(),
        )
        self.candidate = Candidate("candidate-1", self.campaign.id, "Sam Rivera", status=CandidateStatus.QUALIFIED,
            contact=ContactResult("sam@example.com", EmailSourceType.HUNTER, .9, EmailVerificationStatus.VERIFIED, "hunter:1"))
        self.repository.save_candidate(self.candidate)
        self.sender = FakeEmailSender()
        self.service = OutreachService(self.repository, self.sender, identity_url="https://discoverfirst.co", scheduling_url="https://cal.example/riley")

    def test_unapproved_draft_cannot_send_and_message_has_required_content(self) -> None:
        draft, _ = self.service.propose_initial_email(self.candidate.id)
        for expected in ("carrier selection", "30-minute", "https://discoverfirst.co", "https://cal.example/riley", "opt out"):
            self.assertIn(expected, draft.body)
        with self.assertRaisesRegex(ValueError, "approved"):
            self.service.send_approved(draft.id)
        self.assertEqual(self.sender.requests, [])

    def test_approval_sends_once_and_duplicate_approval_is_rejected(self) -> None:
        draft, _ = self.service.propose_initial_email(self.candidate.id)
        self.service.approve(draft.id, "Riley")
        with self.assertRaisesRegex(ValueError, "already been decided"):
            self.service.approve(draft.id, "Riley")
        sent = self.service.send_approved(draft.id)
        self.assertEqual(sent.provider_message_id, "sandbox:1")
        with self.assertRaisesRegex(ValueError, "already been sent"):
            self.service.send_approved(draft.id)
        self.assertEqual(len(self.sender.requests), 1)

    def test_pending_draft_can_be_revised_but_approved_draft_is_locked(self) -> None:
        draft, _ = self.service.propose_initial_email(self.candidate.id)
        revised = self.service.revise_draft(draft.id, subject="A better subject", body="A revised invitation with an opt out.")
        self.assertEqual(revised.subject, "A better subject")
        self.service.approve(draft.id, "Riley")
        with self.assertRaisesRegex(ValueError, "pending"):
            self.service.revise_draft(draft.id, subject="Changed", body="Changed")

    def test_duplicate_bounce_webhook_is_ignored(self) -> None:
        draft, _ = self.service.propose_initial_email(self.candidate.id)
        self.service.approve(draft.id, "Riley")
        sent = self.service.send_approved(draft.id)
        self.assertTrue(self.service.process_delivery_webhook(event_id="evt-1", provider_message_id=sent.provider_message_id, event_type="bounced"))
        self.assertFalse(self.service.process_delivery_webhook(event_id="evt-1", provider_message_id=sent.provider_message_id, event_type="bounced"))
        self.assertEqual(self.repository.get_candidate(self.candidate.id).status, CandidateStatus.BOUNCED)
