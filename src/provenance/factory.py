"""The deterministic core: the only thing that writes to the record.

Everything upstream of this module proposes. Only this module assembles. That asymmetry is the
design — not an implementation detail — and it is what makes the guarantee hold without anyone
supervising the proposer.

The factory does three things, in order:
  1. ADMIT or REJECT each proposal, with a stated reason. A rejection is never silent.
  2. Build typed `Figure`s from admitted proposals — which can only succeed if the provenance
     is real, since `Figure` enforces that itself.
  3. Turn every rejection into a `Gap`, so a proposal that failed leaves a visible question
     behind instead of a hole. "We could not source this" is a finding; omitting it is not.

Point 3 is the part people skip. A pipeline that just drops bad inputs produces a clean-looking
record whose cleanliness is a lie: the reader cannot tell the difference between "nothing was
wrong here" and "something was wrong and we discarded it".
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from provenance.models import Assessment, Citation, Figure, Finding, Gap
from provenance.proposer import Proposal, Proposer


@dataclass(frozen=True)
class Rejection:
    """A proposal that did not become evidence, and precisely why."""

    proposal: Proposal
    reason: str


def _admit(p: Proposal, accessed: date) -> tuple[Figure | None, str | None]:
    """Try to build a Figure. Returns (figure, None) or (None, reason-it-failed).

    Note that this function is short and boring. That is the point: the hard constraint lives
    in the type, so the gatekeeping code does not have to be clever or exhaustive — it just
    attempts construction and reports what the model refused.
    """
    if not p.carries_a_quantity:
        return None, None                                   # prose-only: nothing to admit
    if not p.claimed_source or not p.claimed_url:
        return None, ("quantity proposed with no source — a number that looks decision-grade "
                      "and rests on nothing is worse than no number")
    if not p.claimed_unit:
        return None, "quantity proposed with no unit — a bare magnitude is not a measurement"
    try:
        fig = Figure(
            label=p.statement[:80],
            value=float(p.claimed_value),                   # type: ignore[arg-type]
            unit=p.claimed_unit,
            citations=[Citation(source=p.claimed_source, url=p.claimed_url, accessed=accessed)],
        )
    except ValueError as e:
        # The type system refused it. Report the model's own reason rather than paraphrasing.
        return None, f"failed the provenance contract: {e}"
    return fig, None


def assemble(
    site_name: str,
    proposers: list[Proposer],
    *,
    as_of: date,
    synthetic: bool = False,
) -> tuple[Assessment, list[Rejection]]:
    """Build an Assessment from proposals. The ONLY constructor of a record in this codebase.

    Returns the assessment and the rejections. Callers are expected to surface the rejections;
    the assessment itself already carries the corresponding `Gap`s.
    """
    findings: list[Finding] = []
    gaps: list[Gap] = []
    rejections: list[Rejection] = []

    for proposer in proposers:
        for i, p in enumerate(proposer.propose(), 1):
            fig, reason = _admit(p, as_of)
            if reason is not None:
                rejections.append(Rejection(p, reason))
                gaps.append(Gap(
                    gap_id=f"{proposer.name}-{i}",
                    question=p.statement,
                    fills_from=("a followable published source for this quantity — "
                                f"rejected because: {reason}"),
                ))
                continue
            findings.append(Finding(
                finding_id=f"{proposer.name}-{i}",
                statement=p.statement,
                figures=[fig] if fig else [],
            ))

    return Assessment(site_name=site_name, as_of=as_of, findings=findings, gaps=gaps,
                      synthetic=synthetic), rejections


def derive(label: str, formula: str, inputs: dict[str, Figure], value: float,
           unit: str) -> Figure:
    """Build a computed Figure. Requires the inputs it was derived from, so the lineage of a
    derived number resolves all the way down to observed, cited values."""
    from provenance.models import CalcTrace
    return Figure(label=label, value=value, unit=unit, computed=True,
                  calc_trace=CalcTrace(formula=formula, inputs=inputs),
                  # A derived figure inherits its inputs' citations — it is not independently
                  # sourced, and pretending otherwise would overstate its standing.
                  citations=[c for f in inputs.values() for c in f.citations])
