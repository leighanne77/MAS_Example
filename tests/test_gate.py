"""The human step is a state, and these tests hold it to that.

The claim under test: an unreviewed record is a *distinguishable object* that downstream code
can refuse. Not a convention, not a note in a README — a thing the type system knows about.
"""
from __future__ import annotations

from datetime import date

import pytest

from provenance.gate import NotReviewed, approve, prepare_review, require_reviewed
from provenance.models import Assessment, Citation, Figure, Finding, Gap

TODAY = date(2026, 7, 29)
CIT = Citation(source="USGS NWIS site 03086000",
               url="https://waterdata.usgs.gov/monitoring-location/03086000/", accessed=TODAY)


def _record(**kw) -> Assessment:
    base = dict(
        site_name="Example Site", as_of=TODAY,
        findings=[Finding(finding_id="f1", statement="a statement",
                          figures=[Figure(label="basin area", value=19500.0, unit="sq mi",
                                          citations=[CIT])])],
        gaps=[Gap(gap_id="g1", question="unpriced consequence?",
                  fills_from="a published cost basis")],
    )
    base.update(kw)
    return Assessment(**base)


def test_unreviewed_records_cannot_leave_the_system():
    """The guarantee: evidence for a human decision does not get exported before a human
    has seen it."""
    with pytest.raises(NotReviewed):
        require_reviewed(_record())


def test_approval_requires_a_named_reviewer():
    """'Approved' with nobody attached is not accountability."""
    for bad in ("", "   "):
        with pytest.raises(ValueError, match="named reviewer"):
            approve(_record(), bad)


def test_approval_produces_a_new_version_rather_than_mutating():
    """The record is frozen, so approval is an explicit new artifact — the thing that was
    approved remains exactly as it was."""
    before = _record()
    after = approve(before, "A. Reviewer")
    assert before.reviewed_by is None          # unchanged
    assert after.reviewed_by == "A. Reviewer"
    assert require_reviewed(after) is after


def test_the_review_packet_surfaces_open_gaps():
    """An oversight step that hides its open questions is theatre."""
    packet = prepare_review(_record())
    assert len(packet.open_gaps) == 1
    assert "unpriced consequence?" in packet.open_gaps[0]
    assert "a published cost basis" in packet.open_gaps[0]   # and what would close it
    assert packet.sources == [f"{CIT.source} <{CIT.url}>"]


def test_the_gate_does_not_judge_quality():
    """Deliberate scope limit: the gate checks that a reviewer was equipped, not that the
    findings are good. Judging the reasoning is the human's job — automating it away would
    defeat the purpose of having the step."""
    packet = prepare_review(_record(findings=[]))
    assert packet.assessment.findings == []                  # empty is not rejected
    assert approve(packet.assessment, "A. Reviewer").reviewed_by == "A. Reviewer"
