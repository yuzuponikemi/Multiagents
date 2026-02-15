from __future__ import annotations

from pydantic import BaseModel, Field


class CodeReviewResult(BaseModel):
    """Structured output for code review tasks."""

    summary: str = Field(description="Brief summary of the review findings")
    issues: list[str] = Field(default_factory=list, description="List of identified issues")
    suggestions: list[str] = Field(
        default_factory=list, description="Improvement suggestions"
    )
    severity: str = Field(
        default="info", description="Overall severity: info, warning, critical"
    )


class SafetyAssessment(BaseModel):
    """Structured output for safety-related assessments."""

    is_safe: bool = Field(description="Whether the proposed action is safe")
    risk_level: str = Field(description="Risk level: low, medium, high, critical")
    reasoning: str = Field(description="Explanation of the safety assessment")
    mitigations: list[str] = Field(
        default_factory=list, description="Recommended mitigations"
    )


class TaskReflection(BaseModel):
    """Structured output for agent self-reflection after task completion."""

    task_summary: str = Field(description="What was accomplished")
    lessons_learned: list[str] = Field(
        default_factory=list, description="Key takeaways for future tasks"
    )
    confidence: float = Field(
        ge=0.0, le=1.0, description="Self-assessed confidence in the result"
    )


class TriageResult(BaseModel):
    """Structured output for JIRA ticket triage."""

    ticket_id: str = Field(description="The JIRA ticket ID")
    priority: str = Field(description="Assessed priority: critical, high, medium, low")
    category: str = Field(description="Issue category: bug, feature, refactor, investigation")
    affected_subsystems: list[str] = Field(
        default_factory=list, description="Affected subsystems (e.g., laser, fluidics, optics)"
    )
    estimated_complexity: str = Field(
        description="Complexity estimate: trivial, moderate, complex"
    )
    reasoning: str = Field(description="Explanation of the triage assessment")


class ReviewVerdict(BaseModel):
    """Structured output for Ghost's review of a proposal."""

    approved: bool = Field(description="Whether the proposal is approved")
    feedback: str = Field(description="Review feedback and reasoning")
    adr_references: list[str] = Field(
        default_factory=list, description="Referenced ADR IDs or descriptions"
    )


class MeetingMinutes(BaseModel):
    """Structured output for a virtual meeting conclusion."""

    topic: str = Field(description="The meeting topic")
    decision: str = Field(description="Final decision reached")
    reasoning: str = Field(description="Reasoning behind the decision")
    dissents: list[str] = Field(
        default_factory=list, description="Dissenting opinions or unresolved concerns"
    )
    action_items: list[str] = Field(
        default_factory=list, description="Follow-up actions required"
    )
