from __future__ import annotations

import html
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Callable
from urllib.parse import parse_qs
from wsgiref.simple_server import make_server

from app.domain.models import ParticipantCriteria
from app.discovery import rank_candidate
from app.persistence.sqlite_repository import SqliteRecruiterRepository
from app.ports import FakeEmailSender
from app.services import CampaignService, NotFoundError, OutreachService, evidence_from_payload


database_path = Path(os.environ.get("RECRUITER_DB_PATH", ".data/recruiter.db"))
database_path.parent.mkdir(parents=True, exist_ok=True)
repository = SqliteRecruiterRepository(database_path)
service = CampaignService(repository)
outreach_service = OutreachService(
    repository, FakeEmailSender(),
    identity_url=os.environ.get("DISCOVER_FIRST_IDENTITY_URL", "https://discoverfirst.co"),
    scheduling_url=os.environ.get("CALENDLY_SCHEDULING_URL", "https://calendly.com/discover-first"),
)


def _json(start_response: Callable, status: str, value: object) -> list[bytes]:
    start_response(status, [("Content-Type", "application/json; charset=utf-8")])
    return [json.dumps(value, default=str).encode("utf-8")]


def _read_json(environ: dict) -> dict:
    length = int(environ.get("CONTENT_LENGTH") or 0)
    return json.loads(environ["wsgi.input"].read(length) or b"{}")


def _campaign_json(campaign: object) -> dict:
    return {
        "id": campaign.id,
        "name": campaign.name,
        "research_goal": campaign.research_goal,
        "target_completions": campaign.target_completions,
        "deadline": campaign.deadline.isoformat(),
        "criteria": {
            "titles": campaign.criteria.titles,
            "industries": campaign.criteria.industries,
            "seniorities": campaign.criteria.seniorities,
            "regions": campaign.criteria.regions,
        },
    }


def _candidate_json(candidate: object) -> dict:
    return {
        "id": candidate.id,
        "campaign_id": candidate.campaign_id,
        "name": candidate.name,
        "status": str(candidate.status),
        "reviewer_note": candidate.reviewer_note,
        "contact": None if candidate.contact is None else {
            "email": candidate.contact.email,
            "email_source": str(candidate.contact.email_source) if candidate.contact.email_source else None,
            "confidence": candidate.contact.confidence,
            "verification_status": str(candidate.contact.verification_status),
            "provider_reference": candidate.contact.provider_reference,
        },
        "evidence": [
            {
                "criterion": item.criterion,
                "observed_value": item.observed_value,
                "source_type": str(item.source_type),
                "source_url": item.source_url,
            }
            for item in candidate.evidence
        ],
    }


def _page() -> str:
    rows: list[str] = []
    for campaign in repository.list_campaigns():
        candidates = sorted(repository.list_candidates(campaign.id), key=lambda candidate: (-rank_candidate(candidate).score, candidate.name))
        candidate_rows = "".join(_candidate_row(candidate) for candidate in candidates) or "<li>No candidates yet.</li>"
        drafts = "".join(_draft_row(draft) for draft in repository.list_drafts(campaign.id)) or "<li>No pending email proposals.</li>"
        rows.append(f"<section><h2>{html.escape(campaign.name)}</h2><p>{html.escape(campaign.research_goal)}</p><p>Target: {campaign.target_completions} calls by {campaign.deadline.date()}</p><h3>Candidates</h3><ul>{candidate_rows}</ul><h3>Email proposals</h3><ul>{drafts}</ul></section>")
    content = "".join(rows) or "<p>No campaigns yet. Create one through the API.</p>"
    return f"""<!doctype html><html><head><title>Riley reviewer</title><style>body{{font-family:system-ui;max-width:900px;margin:2rem auto;padding:0 1rem}}section{{border:1px solid #ddd;padding:1rem;margin:1rem 0}}li{{margin:.8rem 0}}</style></head><body><h1>Riley reviewer</h1><p>Milestone 1 candidate evidence review.</p>{content}</body></html>"""


def _candidate_row(candidate: object) -> str:
    evidence_links = " ".join(
        f'<a href="{html.escape(item.source_url, quote=True)}">{html.escape(item.criterion)}: {html.escape(item.observed_value)}</a>'
        for item in candidate.evidence
    )
    review_form = ""
    if str(candidate.status) == "review_required":
        review_form = (
            f'<form method="post" action="/ui/candidates/{html.escape(candidate.id, quote=True)}/review">'
            '<label>Reviewer note <input name="note"></label> '
            '<button name="include" value="true">Include</button> '
            '<button name="include" value="false">Exclude</button></form>'
        )
    contact = ""
    if candidate.contact:
        email = html.escape(candidate.contact.email or "No professional email found")
        source = html.escape(str(candidate.contact.email_source or ""))
        verification = html.escape(str(candidate.contact.verification_status))
        reference = html.escape(candidate.contact.provider_reference)
        confidence = "" if candidate.contact.confidence is None else f"; confidence {candidate.contact.confidence:g}"
        contact = f"<br>Email proposal: {email} ({source}; {verification}{confidence}; reference {reference})"
    email_form = ""
    if str(candidate.status) == "qualified" and candidate.contact and candidate.contact.email and str(candidate.contact.verification_status) == "verified":
        email_form = f'<form method="post" action="/ui/candidates/{html.escape(candidate.id, quote=True)}/email-proposal"><button>Prepare email for review</button></form>'
    proposal = rank_candidate(candidate)
    return f"<li><strong>{html.escape(candidate.name)}</strong> - {html.escape(str(candidate.status))} (priority {proposal.score})<br>{evidence_links}{contact}{email_form}{review_form}</li>"


def _draft_row(draft: object) -> str:
    approval = repository.get_approval_for_draft(draft.id)
    state = str(approval.status) if approval else "missing approval"
    controls = ""
    if state == "pending":
        controls = (
            f'<form method="post" action="/ui/email-drafts/{html.escape(draft.id, quote=True)}/edit">'
            f'<label>Subject <input name="subject" value="{html.escape(draft.subject, quote=True)}"></label><br>'
            f'<label>Message<br><textarea name="body" rows="8" cols="80">{html.escape(draft.body)}</textarea></label><br>'
            '<button>Save edits</button></form>'
            f'<form method="post" action="/ui/email-drafts/{html.escape(draft.id, quote=True)}/approve"><button>Approve this exact email</button></form>'
        )
    elif state == "approved":
        controls = f'<form method="post" action="/ui/email-drafts/{html.escape(draft.id, quote=True)}/send"><button>Send through sandbox</button></form>'
    return f"<li><strong>{html.escape(draft.recipient)}</strong> — {html.escape(draft.subject)} ({html.escape(state)})<pre>{html.escape(draft.body)}</pre>{controls}</li>"


def application(environ: dict, start_response: Callable) -> list[bytes]:
    method, path = environ["REQUEST_METHOD"], environ["PATH_INFO"]
    try:
        if method == "GET" and path == "/":
            start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
            return [_page().encode("utf-8")]
        if method == "GET" and path == "/api/campaigns":
            return _json(start_response, "200 OK", [_campaign_json(item) for item in repository.list_campaigns()])
        if method == "POST" and path == "/api/campaigns":
            data = _read_json(environ)
            criteria = ParticipantCriteria(
                titles=tuple(data.get("criteria", {}).get("titles", [])),
                industries=tuple(data.get("criteria", {}).get("industries", [])),
                seniorities=tuple(data.get("criteria", {}).get("seniorities", [])),
                regions=tuple(data.get("criteria", {}).get("regions", [])),
            )
            campaign = service.create_campaign(
                name=data.get("name", ""), research_goal=data.get("research_goal", ""),
                target_completions=int(data.get("target_completions", 0)),
                deadline=datetime.fromisoformat(data["deadline"]), criteria=criteria,
            )
            return _json(start_response, "201 Created", _campaign_json(campaign))
        if method == "POST" and path.startswith("/api/campaigns/") and path.endswith("/candidates"):
            campaign_id = path.split("/")[3]
            data = _read_json(environ)
            candidate = service.import_candidate(
                campaign_id=campaign_id, name=data.get("name", ""),
                evidence=[evidence_from_payload(item) for item in data.get("evidence", [])],
            )
            return _json(start_response, "201 Created", _candidate_json(candidate))
        if method == "POST" and path.startswith("/api/candidates/") and path.endswith("/review"):
            candidate_id = path.split("/")[3]
            data = _read_json(environ)
            candidate = service.decide_uncertain_candidate(candidate_id=candidate_id, include=bool(data.get("include")), note=data.get("note", ""))
            return _json(start_response, "200 OK", _candidate_json(candidate))
        if method == "POST" and path.startswith("/api/candidates/") and path.endswith("/email-proposal"):
            draft, approval = outreach_service.propose_initial_email(path.split("/")[3])
            return _json(start_response, "201 Created", {"draft_id": draft.id, "approval_id": approval.id, "recipient": draft.recipient, "subject": draft.subject, "body": draft.body})
        if method == "POST" and path.startswith("/api/email-drafts/") and path.endswith("/approve"):
            data = _read_json(environ)
            approval = outreach_service.approve(path.split("/")[3], data.get("reviewer", "reviewer"))
            return _json(start_response, "200 OK", {"draft_id": approval.draft_id, "status": str(approval.status)})
        if method == "POST" and path.startswith("/api/email-drafts/") and path.endswith("/edit"):
            data = _read_json(environ)
            draft = outreach_service.revise_draft(path.split("/")[3], subject=data.get("subject", ""), body=data.get("body", ""))
            return _json(start_response, "200 OK", {"draft_id": draft.id, "subject": draft.subject, "body": draft.body})
        if method == "POST" and path.startswith("/api/email-drafts/") and path.endswith("/send"):
            interaction = outreach_service.send_approved(path.split("/")[3])
            return _json(start_response, "200 OK", {"provider_message_id": interaction.provider_message_id, "event_type": interaction.event_type})
        if method == "POST" and path == "/api/email-webhooks":
            data = _read_json(environ)
            accepted = outreach_service.process_delivery_webhook(
                event_id=data["event_id"], provider_message_id=data["provider_message_id"], event_type=data["event_type"],
            )
            return _json(start_response, "200 OK", {"accepted": accepted})
        if method == "POST" and path.startswith("/ui/candidates/") and path.endswith("/review"):
            candidate_id = path.split("/")[3]
            length = int(environ.get("CONTENT_LENGTH") or 0)
            form = parse_qs(environ["wsgi.input"].read(length).decode("utf-8"))
            service.decide_uncertain_candidate(
                candidate_id=candidate_id,
                include=form.get("include", [""])[0] == "true",
                note=form.get("note", [""])[0],
            )
            start_response("303 See Other", [("Location", "/")])
            return [b""]
        if method == "POST" and path.startswith("/ui/candidates/") and path.endswith("/email-proposal"):
            outreach_service.propose_initial_email(path.split("/")[3])
            start_response("303 See Other", [("Location", "/")])
            return [b""]
        if method == "POST" and path.startswith("/ui/email-drafts/") and path.endswith("/approve"):
            outreach_service.approve(path.split("/")[3], "reviewer")
            start_response("303 See Other", [("Location", "/")])
            return [b""]
        if method == "POST" and path.startswith("/ui/email-drafts/") and path.endswith("/edit"):
            length = int(environ.get("CONTENT_LENGTH") or 0)
            form = parse_qs(environ["wsgi.input"].read(length).decode("utf-8"))
            outreach_service.revise_draft(path.split("/")[3], subject=form.get("subject", [""])[0], body=form.get("body", [""])[0])
            start_response("303 See Other", [("Location", "/")])
            return [b""]
        if method == "POST" and path.startswith("/ui/email-drafts/") and path.endswith("/send"):
            outreach_service.send_approved(path.split("/")[3])
            start_response("303 See Other", [("Location", "/")])
            return [b""]
        return _json(start_response, "404 Not Found", {"error": "route not found"})
    except (ValueError, KeyError) as error:
        return _json(start_response, "400 Bad Request", {"error": str(error)})
    except NotFoundError as error:
        return _json(start_response, "404 Not Found", {"error": str(error)})


if __name__ == "__main__":
    with make_server("127.0.0.1", 8000, application) as server:
        print("Reviewer page available at http://127.0.0.1:8000")
        server.serve_forever()
