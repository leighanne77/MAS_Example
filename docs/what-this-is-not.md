# What this is not

Stating the limits plainly, because a demonstration that oversells itself undermines the very
discipline it is demonstrating.

## Not a system that knows anything

There is no domain model here. No data sources, no methodology, no scoring, no opinion about
what any quantity means or which source is authoritative for it. The pipeline will happily admit
a well-cited number that is completely wrong for the question being asked, because the contract
checks *provenance*, not *fitness for purpose*.

That gap is not an oversight — it is the honest boundary of what a type system can do. Deciding
that a particular published curve is the right one for a particular structure at a particular
location is domain judgement. It is also, in any real application, the overwhelming majority of
the work. Nothing here helps with it.

## Not a validator of correctness

The contract enforces that a number has a followable source and, if derived, a published
derivation. It cannot tell you:

- whether the source actually supports the claim attached to it (a real trap: a methodology
  manual is not the data the methodology consumes);
- whether two individually-correct figures were combined wrongly;
- whether the narrative around a figure is a fair reading of it;
- whether the right question was asked in the first place.

Every one of those is interpretive, and every one is why the human gate exists.

## Not production infrastructure

No persistence, no API, no authentication, no concurrency, no versioning of records over time,
no audit log, no access control. The example runs offline against a scripted proposer precisely
so the mechanism can be read without infrastructure noise around it.

## Not a model harness

No model is called anywhere in this repository. `proposer.py` is a stub that replays a scripted
list. Wiring an actual model in is straightforward and deliberately left undone: the point being
demonstrated is the *boundary*, and the boundary is more legible when nothing on the far side of
it is moving.

## Not an assessment of any real place

**Wheeler Creek Municipal Campus is fictional.** The USGS gauge it cites is real and public, so
that the provenance chain in the output can actually be followed — but no inference about any
real facility, watershed or community should be drawn from the example. The numbers exist to
demonstrate a mechanism.

## Not a claim of novelty

Typed records, required provenance, and human sign-off are old ideas, and better versions of
each exist in scientific-data management, provenance research (PROV-O and its relatives),
regulated-industry recordkeeping, and elsewhere. What is offered here is a small, readable
assembly of them aimed at a specific contemporary problem: language-model output entering
records that people then rely on.

If you need the full apparatus, use the standards. If you want to see the shape of the idea in
an afternoon, this is that.
