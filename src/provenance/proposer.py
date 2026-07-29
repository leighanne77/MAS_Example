"""The stochastic boundary: where a language model is allowed to act, and where it is not.

A proposer stands in for whatever generates candidate content — a language model, a search
tool, a human analyst. It emits `Proposal` objects: prose, a claimed quantity, and a claimed
source. **A proposal is not evidence.** It is untyped by design, and nothing downstream is
obliged to believe it.

The interesting property is what a proposer *cannot* do. It cannot construct a `Figure`,
because a `Figure` requires a real `Citation`, and it cannot write to an `Assessment`, because
only the factory assembles one. So the worst a bad proposal can do is fail validation. A
hallucinated number does not become a quiet error in the record; it becomes a rejection with a
reason.

No model is called here. This module is deliberately a stub: the point is the *shape* of the
boundary, and a demonstration should not need an API key to run.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Proposal:
    """Untyped candidate content. Note what is missing: nothing here is trusted, and every
    field is a *claim* until the factory checks it."""

    statement: str
    claimed_value: float | None = None
    claimed_unit: str | None = None
    claimed_source: str | None = None
    claimed_url: str | None = None
    reasoning: str = ""

    @property
    def carries_a_quantity(self) -> bool:
        return self.claimed_value is not None

    @property
    def is_admissible(self) -> bool:
        """A quantity is admissible only if the proposer supplied a followable source with it.
        Checked again — and enforced — by the factory; this is a courtesy pre-check so a
        proposer can self-filter rather than submit work that will certainly be rejected."""
        if not self.carries_a_quantity:
            return True                       # prose-only proposals are fine
        return bool(self.claimed_source and self.claimed_url
                    and self.claimed_url.startswith(("http://", "https://"))
                    and self.claimed_unit)


@dataclass
class Proposer:
    """A named source of proposals. In a real system this wraps a model call and a search
    tool; here it replays a scripted list so the example is deterministic and offline."""

    name: str
    scripted: list[Proposal] = field(default_factory=list)

    def propose(self) -> list[Proposal]:
        return list(self.scripted)


def demo_proposer() -> Proposer:
    """A proposer that emits three proposals — one good, two bad in different ways.

    This is the honest part of the demonstration: it includes the failure modes on purpose, so
    the reader can watch the boundary reject them rather than take on trust that it would.
    """
    return Proposer(
        name="demo-proposer",
        scripted=[
            # 1. GOOD — a quantity with a real, followable public source.
            Proposal(
                statement="The gauge upstream of the campus drains a large basin, so upstream "
                          "conditions dominate local stage.",
                claimed_value=19500.0,
                claimed_unit="sq mi",
                claimed_source="USGS National Water Information System — site 03086000",
                claimed_url="https://waterdata.usgs.gov/monitoring-location/03086000/",
                reasoning="Basin area is published in the USGS expanded site record.",
            ),
            # 2. BAD — a confident number with no source. The classic failure this repo is
            #    built to make impossible: it looks decision-grade and rests on nothing.
            Proposal(
                statement="Annual flood damage to the campus is approximately $2.4M.",
                claimed_value=2_400_000.0,
                claimed_unit="USD/yr",
                claimed_source=None,
                claimed_url=None,
                reasoning="Sounds plausible for a facility of this size.",
            ),
            # 3. BAD — a source that is not followable (a title, not a link).
            Proposal(
                statement="The site sits within a mapped regulatory floodplain.",
                claimed_value=1.0,
                claimed_unit="boolean",
                claimed_source="a federal flood map",
                claimed_url="see the agency website",
                reasoning="Recalled from general knowledge.",
            ),
        ],
    )
