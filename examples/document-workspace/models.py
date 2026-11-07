"""Domain models for the document workspace example."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DocumentSection:
    id: int
    name: str
    section_type: str
    status: str
    target: int
    limit: int
    reviewer: str


SECTION_TYPES = (
    "Technical",
    "Management",
    "Financial",
    "Compliance",
    "Design",
)

REVIEWERS = (
    "Avery Chen",
    "Morgan Patel",
    "Riley Jones",
    "Jordan Kim",
    "Casey Diaz",
)

STATUSES = ("In Progress", "Done")

SECTION_NAMES = (
    "Cover page",
    "Table of contents",
    "Executive summary",
    "Technical approach",
    "Design",
    "Capabilities",
    "Integration with existing systems",
    "Innovation and Advantages",
    "Overview of EMR's Innovative Solutions",
    "Advanced Algorithms and Machine Learning",
    "Security and compliance",
    "Deployment plan",
    "Risk management",
    "Quality assurance",
    "Project schedule",
    "Budget summary",
    "Staffing plan",
    "Communications plan",
    "Lessons learned",
    "Appendix A",
)
__all__ = ["REVIEWERS", "SECTION_NAMES", "SECTION_TYPES", "STATUSES", "DocumentSection"]
