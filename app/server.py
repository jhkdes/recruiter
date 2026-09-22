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
from app.persistence.sqlite_repository import SqliteRecruiterRepository
from app.services import CampaignService, NotFoundError, evidence_from_payload


database_path = Path(os.environ.get("RECRUITER_DB_PATH", ".data/recruiter.db"))
database_path.parent.mkdir(parents=True, exist_ok=True)
repository = SqliteRecruiterRepository(database_path)
service = CampaignService(repository)


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
        candidates = repository.list_candidates(campaign.id)
        candidate_rows = "".join(_candidate_row(candidate) for candidate in candidates) or "<li>No candidates yet.</li>"
        rows.append(f"<section><h2>{html.escape(campaign.name)}</h2><p>{html.escape(campaign.research_goal)}</p><p>Target: {campaign.target_completions} calls by {campaign.deadline.date()}</p><ul>{candidate_rows}</ul></section>")
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
    return f"<li><strong>{html.escape(candidate.name)}</strong> - {html.escape(str(candidate.status))}<br>{evidence_links}{review_form}</li>"


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
        return _json(start_response, "404 Not Found", {"error": "route not found"})
    except (ValueError, KeyError) as error:
        return _json(start_response, "400 Bad Request", {"error": str(error)})
    except NotFoundError as error:
        return _json(start_response, "404 Not Found", {"error": str(error)})


if __name__ == "__main__":
    with make_server("127.0.0.1", 8000, application) as server:
        print("Reviewer page available at http://127.0.0.1:8000")
        server.serve_forever()
