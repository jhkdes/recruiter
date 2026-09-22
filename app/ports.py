from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class SearchLead:
    name: str
    profile_url: str
    source_url: str


@dataclass(frozen=True)
class EnrichmentMatch:
    email: str | None
    provider_reference: str
    confidence: float | None
    verified: bool


class CandidateSearchPort(Protocol):
    def search(self, query: str) -> list[SearchLead]: ...


class ProfessionalEmailEnrichmentPort(Protocol):
    def find(self, *, name: str, company: str, profile_url: str) -> EnrichmentMatch: ...


class Clock(Protocol):
    def now_iso(self) -> str: ...


class FakeCandidateSearch:
    def __init__(self, results: list[SearchLead] | None = None) -> None:
        self.results = results or []
        self.queries: list[str] = []

    def search(self, query: str) -> list[SearchLead]:
        self.queries.append(query)
        return list(self.results)


class FakeProfessionalEmailEnrichment:
    def __init__(self, result: EnrichmentMatch | None = None) -> None:
        self.result = result or EnrichmentMatch(None, "fake:no-match", None, False)
        self.requests: list[dict[str, str]] = []

    def find(self, *, name: str, company: str, profile_url: str) -> EnrichmentMatch:
        self.requests.append({"name": name, "company": company, "profile_url": profile_url})
        return self.result
