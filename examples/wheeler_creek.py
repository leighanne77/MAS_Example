#!/usr/bin/env python3
"""Worked example: Wheeler Creek Municipal Campus (fictional).

The facility is invented. The cited source is real: USGS National Water Information System
site 03086000, Ohio River at Sewickley, Pennsylvania, whose published expanded site record
gives a contributing drainage area of 19,500 square miles. Keeping the source real and the
site fictional means the provenance chain in the output is genuinely followable — you can
click the link and check the number — without the example implying an assessment of any real
place.

Run:  PYTHONPATH=src python examples/wheeler_creek.py
Writes examples/wheeler_creek_output.html

What to watch, in the output:
  * Three proposals go in. One is well sourced. One is a confident, plausible dollar figure
    with no source at all. One cites "a federal flood map" with a link a reader cannot follow.
  * Only the first becomes a figure. The other two appear as OPEN GAPS — visible, with what
    would close them — rather than vanishing.
  * The export refuses to render at all until a named reviewer has approved the record.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

from provenance.factory import assemble, derive
from provenance.gate import NotReviewed, approve, prepare_review
from provenance.models import Figure
from provenance.proposer import demo_proposer
from provenance.render import to_html

AS_OF = date(2026, 7, 29)
OUT = Path(__file__).resolve().parent / "wheeler_creek_output.html"


def main() -> None:
    # 1. The stochastic layer proposes. Nothing here is trusted yet.
    proposers = [demo_proposer()]

    # 2. The deterministic core is the only writer. It admits what it can source and turns
    #    everything it cannot into a visible gap.
    assessment, rejections = assemble(
        "Wheeler Creek Municipal Campus", proposers, as_of=AS_OF, synthetic=True)

    print(f"proposals admitted : {len(assessment.findings)}")
    print(f"proposals rejected : {len(rejections)}")
    for r in rejections:
        print(f"   REJECTED  {r.proposal.statement[:58]!r}\n             -> {r.reason}")

    # 3. A derived figure: lineage resolves through the computation to the cited input.
    basin = next(f for f in assessment.all_figures() if "sq mi" in f.unit)
    indicative = derive(
        label="indicative mean discharge (illustrative unit rate)",
        formula="basin_area * unit_rate",
        inputs={
            "basin_area": basin,
            # The unit rate is itself a figure and so needs its own source; using the same
            # public record keeps the example honest about where every input came from.
            "unit_rate": Figure(label="illustrative unit rate", value=2.0, unit="cfs/sq mi",
                                citations=basin.citations),
        },
        value=basin.value * 2.0, unit="cfs")
    print(f"\nderived figure lineage: {indicative.lineage()}")

    # 4. The human gate. Export is refused until someone is accountable.
    packet = prepare_review(assessment)
    print(f"\nreview packet: {packet.summary}")
    for g in packet.open_gaps:
        print(f"   OPEN  {g[:96]}")

    try:
        to_html(assessment)
    except NotReviewed as e:
        print(f"\nexport correctly refused before review:\n   {e}")

    approved = approve(assessment, "A. Reviewer")
    OUT.write_text(to_html(approved), encoding="utf-8")
    print(f"\nwrote {OUT.name} after approval by {approved.reviewed_by}")


if __name__ == "__main__":
    main()
