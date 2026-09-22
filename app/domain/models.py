from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from uuid import uuid4


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class CandidateStatus(StrEnum):
    DISCOVERED = "discovered"
    VERIFIED = "verified"
    QUALIFIED = "qualified"
    NOT_QUALIFIED = "not_qualified"
    REVIEW_REQUIRED = "review_required"


class EvidenceSourceType(StrEnum):
    LINKEDIN = "linkedin"
    PUBLICATION = "publication"
    WEBINAR = "webinar"
    UPLOADED_LIST = "uploaded_list"
    OTHER_APPROVED_SOURCE = "other_approved_source"


REQUIRED_CRITERIA = ("title", "industry", "seniority", "region")


@dataclass(frozen=True)
class ParticipantCriteria:
    titles: tuple[str, ...] = ()
    industries: tuple[str, ...] = ()
    seniorities: tuple[str, ...] = ()
    regions: tuple[str, ...] = ()

    def requested_values(self, criterion: str) -> tuple[str, ...]:
        return {
            "title": self.titles,
            "industry": self.industries,
            "seniority": self.seniorities,
            "region": self.regions,
        }[criterion]


@dataclass(frozen=True)
class Campaign:
    id: str
    name: str
    research_goal: str
    target_completions: int
    deadline: datetime
    criteria: ParticipantCriteria
    created_at: datetime = field(default_factory=utc_now)


@dataclass(frozen=True)
class CandidateEvidence:
    criterion: str
    observed_value: str
    source_type: EvidenceSourceType
    source_url: str
    captured_at: datetime = field(default_factory=utc_now)


@dataclass
class Candidate:
    id: str
    campaign_id: str
    name: str
    evidence: list[CandidateEvidence] = field(default_factory=list)
    status: CandidateStatus = CandidateStatus.DISCOVERED
    reviewer_note: str | None = None
    created_at: datetime = field(default_factory=utc_now)


@dataclass(frozen=True)
class QualificationResult:
    status: CandidateStatus
    matched_criteria: tuple[str, ...]
    missing_or_conflicting_criteria: tuple[str, ...]
    explanation: str


def new_id() -> str:
    return str(uuid4())
