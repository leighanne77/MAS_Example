"""The typed contract: a number that cannot exist without its provenance.

This is the whole idea of this repository in about a hundred lines.

The usual approach to "make sure figures are sourced" is a review step — a checklist, a linter,
a prompt instructing a model to always cite. All of those are *behavioural*: they work when
everyone remembers, and they fail quietly when someone does not. Accuracy is a probability.

The approach here is *structural*. `Figure` requires at least one `Citation` to construct, and
a computed `Figure` additionally requires a `CalcTrace` naming its inputs and formula. There is
no code path that produces an unsourced number, because the object cannot be instantiated
without one. Impossibility is a guarantee.

The consequence worth noticing: a language model in this design can draft, search, summarise
and propose — but it can never *emit a number into the record*, because the record only accepts
`Figure`, and building one means supplying a real source. The constraint does the work that a
well-behaved model would otherwise have to be trusted to do.
"""
from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field, model_validator

# Frozen and closed: values cannot be mutated after validation, and an unexpected field is an
# error rather than a silently ignored typo. Both matter when the object is evidence.
_STRICT = ConfigDict(frozen=True, extra="forbid")


class Citation(BaseModel):
    """Where a value came from. A URL is required — a citation a reader cannot follow is a
    claim, not a citation."""

    model_config = _STRICT

    source: str = Field(min_length=1, description="publisher and dataset, as a reader would cite it")
    url: str = Field(min_length=1, description="resolvable link to the source")
    accessed: date
    note: str | None = None

    @model_validator(mode="after")
    def _url_is_resolvable_shaped(self) -> "Citation":
        if not self.url.startswith(("http://", "https://")):
            raise ValueError(
                f"citation url must be resolvable, got {self.url!r}. A reference a reader "
                "cannot follow does not count as provenance.")
        return self


class CalcTrace(BaseModel):
    """How a computed value was derived. Inputs are themselves `Figure`s, so the trace is
    recursive: following it terminates only at observed values with citations."""

    model_config = _STRICT

    formula: str = Field(min_length=1, description="human-readable derivation, e.g. 'a * b'")
    inputs: dict[str, "Figure"] = Field(min_length=1)

    def lineage(self) -> list[str]:
        """Flatten the derivation to a list of source strings — the audit answer to
        'what does this number rest on?'"""
        out: list[str] = []
        for fig in self.inputs.values():
            out.extend(fig.lineage())
        return out


class Figure(BaseModel):
    """A number with its provenance attached, by construction.

    Two rules, both enforced at instantiation:
      1. at least one citation, always;
      2. if `computed` is true, a `CalcTrace` is mandatory — a derived number must say how it
         was derived, not merely where its ingredients came from.
    """

    model_config = _STRICT

    label: str = Field(min_length=1)
    value: float
    unit: str = Field(min_length=1)
    citations: list[Citation] = Field(min_length=1)      # <- the load-bearing constraint
    computed: bool = False
    calc_trace: CalcTrace | None = None
    note: str | None = None

    @model_validator(mode="after")
    def _computed_requires_a_trace(self) -> "Figure":
        if self.computed and self.calc_trace is None:
            raise ValueError(
                f"{self.label!r} is marked computed but carries no calc_trace. A derived figure "
                "must publish its derivation, or it is unreproducible.")
        if self.calc_trace is not None and not self.computed:
            raise ValueError(
                f"{self.label!r} carries a calc_trace but is not marked computed — say which "
                "it is.")
        return self

    def lineage(self) -> list[str]:
        """Every source this figure ultimately rests on, following computation through."""
        if self.calc_trace is not None:
            return self.calc_trace.lineage()
        return [f"{c.source} <{c.url}>" for c in self.citations]


class Finding(BaseModel):
    """One assessed statement about a site. Prose and numbers are kept in separate fields on
    purpose: the narrative may be edited freely, while every quantity in `figures` carries its
    own provenance and cannot be rewritten into an unsourced claim by accident."""

    model_config = _STRICT

    finding_id: str = Field(min_length=1)
    statement: str = Field(min_length=1)
    figures: list[Figure] = Field(default_factory=list)
    open_question: str | None = None


class Gap(BaseModel):
    """A question that was asked and NOT answered.

    An honest record needs a way to say "we looked and could not close this", because the
    alternative — omitting it — is indistinguishable from never having looked. `fills_from`
    names what would close the gap, so an absence is actionable rather than merely admitted.
    """

    model_config = _STRICT

    gap_id: str = Field(min_length=1)
    question: str = Field(min_length=1)
    fills_from: str = Field(min_length=1, description="what evidence would close this")


class Assessment(BaseModel):
    """The assembled record — the deliverable. Built only by the factory (see factory.py)."""

    model_config = _STRICT

    site_name: str = Field(min_length=1)
    as_of: date
    findings: list[Finding] = Field(default_factory=list)
    gaps: list[Gap] = Field(default_factory=list)
    reviewed_by: str | None = None       # set only by the human gate; see gate.py
    synthetic: bool = False              # worked examples say so, loudly

    def all_figures(self) -> list[Figure]:
        return [f for finding in self.findings for f in finding.figures]

    def bibliography(self) -> list[str]:
        """Every distinct source the record rests on, resolvable and de-duplicated."""
        seen: dict[str, None] = {}
        for fig in self.all_figures():
            for src in fig.lineage():
                seen.setdefault(src, None)
        return sorted(seen)


CalcTrace.model_rebuild()   # resolve the forward reference to Figure
