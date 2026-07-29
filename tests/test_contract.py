"""These tests are the argument.

Everything this repository claims reduces to one sentence: *an unsourced number cannot be
constructed*. That is a strong claim, and a README asserting it proves nothing. What follows is
the demonstration — mostly tests that assert something **fails**, because the guarantee is
about what the system refuses to do.

If you read one file here, read this one, then try to write a test that defeats it.
"""
from __future__ import annotations

from datetime import date

import pytest
from pydantic import ValidationError

from provenance.factory import assemble, derive
from provenance.models import Assessment, Citation, Figure, Finding
from provenance.proposer import Proposal, Proposer

TODAY = date(2026, 7, 29)
REAL = Citation(
    source="USGS National Water Information System — site 03086000",
    url="https://waterdata.usgs.gov/monitoring-location/03086000/",
    accessed=TODAY,
)


# ─────────────────────────── the central guarantee ───────────────────────────
def test_a_naked_figure_is_unconstructible():
    """THE headline. There is no argument list that produces a Figure without provenance."""
    with pytest.raises(ValidationError):
        Figure(label="annual damage", value=2_400_000.0, unit="USD/yr")          # no citations


def test_an_empty_citation_list_is_not_a_loophole():
    """Passing `citations=[]` satisfies the signature but not the contract."""
    with pytest.raises(ValidationError):
        Figure(label="annual damage", value=2_400_000.0, unit="USD/yr", citations=[])


def test_a_citation_a_reader_cannot_follow_is_rejected():
    """A source string without a resolvable URL is a claim, not a citation."""
    with pytest.raises(ValidationError):
        Citation(source="a federal flood map", url="see the agency website", accessed=TODAY)


def test_a_computed_figure_must_publish_its_derivation():
    """A derived number that will not say how it was derived is unreproducible."""
    with pytest.raises(ValidationError):
        Figure(label="scaled value", value=5.0, unit="ft", citations=[REAL], computed=True)


def test_a_figure_cannot_be_mutated_after_construction():
    """Evidence that can be edited in place is not evidence."""
    fig = Figure(label="basin area", value=19500.0, unit="sq mi", citations=[REAL])
    with pytest.raises(ValidationError):
        fig.value = 1.0                                                          # type: ignore[misc]


def test_a_typo_is_an_error_not_a_silent_ignore():
    """extra='forbid': a misspelled field fails loudly rather than vanishing."""
    with pytest.raises(ValidationError):
        Figure(label="basin area", value=19500.0, unit="sq mi",
               citations=[REAL], citaton="oops")                                 # type: ignore[call-arg]


# ─────────────────────────── lineage is followable ───────────────────────────
def test_derived_figures_resolve_to_observed_sources():
    """Following a computed value terminates only at cited, observed values."""
    a = Figure(label="basin area", value=19500.0, unit="sq mi", citations=[REAL])
    b = Figure(label="unit rate", value=2.0, unit="cfs/sq mi", citations=[REAL])
    out = derive("indicative discharge", "basin_area * unit_rate",
                 {"basin_area": a, "unit_rate": b}, value=39000.0, unit="cfs")
    assert out.computed and out.calc_trace is not None
    assert out.calc_trace.formula == "basin_area * unit_rate"
    assert out.lineage() == [f"{REAL.source} <{REAL.url}>"] * 2                   # both inputs


# ─────────────────── the boundary: proposals are not evidence ───────────────────
def test_an_unsourced_proposal_never_becomes_a_figure():
    """A confident, plausible, entirely unsourced number — the exact failure mode this repo
    exists to make impossible — is rejected, and leaves a visible gap behind."""
    bad = Proposal(statement="Annual flood damage is approximately $2.4M.",
                   claimed_value=2_400_000.0, claimed_unit="USD/yr")
    assessment, rejections = assemble("Example Site", [Proposer("p", [bad])], as_of=TODAY)
    assert assessment.all_figures() == []                       # nothing entered the record
    assert len(rejections) == 1
    assert "no source" in rejections[0].reason
    assert len(assessment.gaps) == 1                            # and the question survives


def test_a_rejected_proposal_is_never_silently_dropped():
    """A pipeline that discards bad input produces a clean-looking record whose cleanliness is
    a lie. Every rejection must leave a gap the reader can see."""
    props = [Proposal(statement="unsourced claim", claimed_value=1.0, claimed_unit="ft"),
             Proposal(statement="another one", claimed_value=2.0, claimed_unit="ft")]
    assessment, rejections = assemble("Example Site", [Proposer("p", props)], as_of=TODAY)
    assert len(rejections) == 2
    assert len(assessment.gaps) == 2
    for gap in assessment.gaps:
        assert gap.fills_from, "a gap must say what would close it"


def test_a_well_sourced_proposal_is_admitted():
    """The contract is strict, not obstructive: real provenance passes."""
    good = Proposal(statement="The basin is large.", claimed_value=19500.0,
                    claimed_unit="sq mi", claimed_source=REAL.source, claimed_url=REAL.url)
    assessment, rejections = assemble("Example Site", [Proposer("p", [good])], as_of=TODAY)
    assert not rejections
    assert len(assessment.all_figures()) == 1
    assert assessment.bibliography() == [f"{REAL.source} <{REAL.url}>"]


def test_prose_without_a_quantity_is_allowed_through():
    """The constraint is on NUMBERS. Narrative is free — it just cannot smuggle a figure."""
    prose = Proposal(statement="Upstream conditions dominate local stage.")
    assessment, rejections = assemble("Example Site", [Proposer("p", [prose])], as_of=TODAY)
    assert not rejections and len(assessment.findings) == 1
    assert assessment.all_figures() == []


# ─────────────────────────── the record itself ───────────────────────────
def test_bibliography_is_deduplicated_and_complete():
    other = Citation(source="USGS site 03086000 expanded record",
                     url="https://waterservices.usgs.gov/nwis/site/", accessed=TODAY)
    a = Figure(label="a", value=1.0, unit="ft", citations=[REAL])
    b = Figure(label="b", value=2.0, unit="ft", citations=[REAL, other])
    rec = Assessment(site_name="Example", as_of=TODAY,
                     findings=[Finding(finding_id="f1", statement="s", figures=[a, b])])
    assert len(rec.bibliography()) == 2                        # REAL appears twice, listed once
