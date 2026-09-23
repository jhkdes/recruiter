from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class SearchLead:
    name: str
    profile_url: str
    source_url: str
    company: str = ""
    evidence: tuple[tuple[str, str], ...] = ()


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


class EmailVerificationPort(Protocol):
    def verify(self, email: str) -> EnrichmentMatch: ...


@dataclass(frozen=True)
class EmailSendResult:
    provider_message_id: str


class EmailSendPort(Protocol):
    def send(self, *, recipient: str, subject: str, body: str, idempotency_key: str) -> EmailSendResult: ...


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


class FakeEmailVerification:
    def __init__(self, result: EnrichmentMatch | None = None) -> None:
        self.result = result or EnrichmentMatch(None, "fake:unavailable", None, False)
        self.emails: list[str] = []

    def verify(self, email: str) -> EnrichmentMatch:
        self.emails.append(email)
        return self.result


class FakeEmailSender:
    def __init__(self) -> None:
        self.requests: list[dict[str, str]] = []

    def send(self, *, recipient: str, subject: str, body: str, idempotency_key: str) -> EmailSendResult:
        self.requests.append({"recipient": recipient, "subject": subject, "body": body, "idempotency_key": idempotency_key})
        return EmailSendResult(f"sandbox:{len(self.requests)}")
