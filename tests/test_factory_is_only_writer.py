"""The asymmetry under test: everything upstream proposes, only the factory assembles.

The contract tests (test_contract.py) show that a bad *object* cannot exist. These show the
complementary property about the *pipeline*: there is no route from a proposal into the record
except through `assemble()`, and what assemble refuses leaves a mark.
"""
from __future__ import annotations

from datetime import date

from provenance.factory import Rejection, assemble
from provenance.proposer import Proposal, Proposer, demo_proposer

TODAY = date(2026, 7, 29)


def test_proposals_carry_no_write_access():
    """A Proposal exposes claims and nothing else — no method on it produces a Figure, a
    Finding, or an Assessment. The absence is the API."""
    p = Proposal(statement="s", claimed_value=1.0, claimed_unit="ft")
    public_surface = {name for name in dir(p) if not name.startswith("_")}
    assert public_surface == {"statement", "claimed_value", "claimed_unit", "claimed_source",
                              "claimed_url", "reasoning", "carries_a_quantity", "is_admissible"}, \
        "Proposal grew surface area — check nothing on it can write to the record"


def test_the_demo_proposer_is_honest_about_failure_modes():
    """The shipped demo includes one good proposal and two bad ones ON PURPOSE — a
    demonstration that only shows successes demonstrates nothing."""
    proposals = demo_proposer().propose()
    assert len(proposals) == 3
    admissible = [p for p in proposals if p.is_admissible]
    assert len(admissible) == 1, "exactly one demo proposal should survive the pre-check"


def test_assemble_accounts_for_every_proposal():
    """Conservation law: proposals in == findings + rejections out, and every rejection has a
    matching gap. Nothing is silently dropped, nothing is double-counted."""
    assessment, rejections = assemble("Example Site", [demo_proposer()], as_of=TODAY)
    n_in = len(demo_proposer().propose())
    assert len(assessment.findings) + len(rejections) == n_in
    assert len(assessment.gaps) == len(rejections)
    for r in rejections:
        assert isinstance(r, Rejection) and r.reason, "a rejection must say why"


def test_multiple_proposers_stay_attributed():
    """Findings and gaps carry the proposer's name in their ids — provenance applies to the
    pipeline itself, not only to the numbers."""
    a = Proposer("alpha", [Proposal(statement="prose only")])
    b = Proposer("beta", [Proposal(statement="unsourced", claimed_value=1.0,
                                   claimed_unit="ft")])
    assessment, _ = assemble("Example Site", [a, b], as_of=TODAY)
    assert [f.finding_id for f in assessment.findings] == ["alpha-1"]
    assert [g.gap_id for g in assessment.gaps] == ["beta-1"]


def test_the_synthetic_flag_travels_with_the_record():
    """A fictional example must say so on the record itself, not merely in a README —
    downstream consumers see the object, not the repository it came from."""
    assessment, _ = assemble("Example Site", [demo_proposer()], as_of=TODAY, synthetic=True)
    assert assessment.synthetic is True
