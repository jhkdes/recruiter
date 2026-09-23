from __future__ import annotations

from app.ports import EnrichmentMatch, SearchLead


def translate_search_results(payload: list[dict]) -> list[SearchLead]:
    """Translate captured provider data; making HTTP requests is intentionally out of scope."""
    return [SearchLead(
        name=item["name"], profile_url=item["profile_url"], source_url=item["source_url"],
        company=item.get("company", ""), evidence=tuple(item.get("evidence", {}).items()),
    ) for item in payload]


def translate_hunter_response(payload: dict) -> EnrichmentMatch:
    data = payload.get("data") or {}
    return EnrichmentMatch(
        data.get("email"), str(data.get("id", "hunter:no-match")), data.get("score"),
        (data.get("verification") or {}).get("status") == "valid",
    )


def translate_apollo_response(payload: dict) -> EnrichmentMatch:
    person = payload.get("person") or (payload.get("people") or [{}])[0] or {}
    return EnrichmentMatch(
        person.get("email"), str(person.get("id", "apollo:no-match")), person.get("confidence"),
        person.get("email_status") == "verified",
    )
