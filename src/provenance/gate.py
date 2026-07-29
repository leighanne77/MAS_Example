"""The human step, as an explicit state — not an assumption.

Most systems describe human oversight in a README and implement it nowhere: the pipeline runs
end to end, and "a person reviews the output" is a hope about someone's calendar. Here review
is a state transition on the record. An unreviewed assessment is a distinguishable object, and
code downstream can refuse it.

The gate deliberately does NOT judge quality. It cannot tell whether a finding is well
reasoned — that is exactly the judgement a person is here to supply. What it enforces is that
the person was *given what they need*: open gaps surfaced, unsourced material already excluded
by the factory, and a named reviewer recorded on the artifact.
"""
from __future__ import annotations

from dataclasses import dataclass

from provenance.models import Assessment


class NotReviewed(Exception):
    """Raised when an unreviewed assessment is used where review is required."""


@dataclass(frozen=True)
class ReviewPacket:
    """What a reviewer is handed. Assembled so the gaps are impossible to miss — an oversight
    step that hides its open questions is theatre."""

    assessment: Assessment
    open_gaps: list[str]
    sources: list[str]

    @property
    def summary(self) -> str:
        return (f"{self.assessment.site_name}: {len(self.assessment.findings)} finding(s), "
                f"{len(self.open_gaps)} open gap(s), {len(self.sources)} distinct source(s)")


def prepare_review(assessment: Assessment) -> ReviewPacket:
    """Bundle an assessment for human review."""
    return ReviewPacket(
        assessment=assessment,
        open_gaps=[f"{g.gap_id}: {g.question} — needs {g.fills_from}" for g in assessment.gaps],
        sources=assessment.bibliography(),
    )


def approve(assessment: Assessment, reviewer: str) -> Assessment:
    """Record human approval. Returns a NEW assessment — the record is frozen, so approval is
    an explicit new version rather than a mutation of the thing being approved.

    A reviewer name is required. "Approved" with nobody attached is not accountability.
    """
    if not reviewer or not reviewer.strip():
        raise ValueError("approval requires a named reviewer — anonymous sign-off is not review")
    return assessment.model_copy(update={"reviewed_by": reviewer.strip()})


def require_reviewed(assessment: Assessment) -> Assessment:
    """Guard for anything that must not act on unreviewed material — exporting, publishing,
    handing to a decision-maker."""
    if not assessment.reviewed_by:
        raise NotReviewed(
            f"{assessment.site_name!r} has not been reviewed. The record is evidence for a "
            "human decision; it does not leave the system before a human has seen it.")
    return assessment
