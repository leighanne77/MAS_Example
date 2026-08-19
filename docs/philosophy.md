# Why structural, not behavioural

## The problem is not model accuracy

It is tempting to frame unsourced output as a model-quality problem: better prompts, better
retrieval, a bigger model, and the fabrications go away. They mostly do — which is the trap.
"Mostly" is a probability, and a system whose guarantee is probabilistic has no guarantee at
all; it has a failure rate, discovered by whoever is reading the output at the time.

The reframe that makes the problem tractable: **stop trying to make the model reliable, and make
the unwanted state unrepresentable.** If a number without provenance cannot be constructed, then
no amount of model misbehaviour produces one. The constraint holds on code paths nobody tested,
in situations nobody anticipated, and when nobody is watching.

## Three categories of structure

Not all structure is equal, and the differences matter more than they look:

| | What it is | A violation is | Holds when nobody looks? |
|---|---|---|---|
| **Contract** | machine-enforced interface — the typed record, the validation gate | a **failure** | yes |
| **Convention** | documentation, naming, prompt-level guidance | **drift** | no |
| **Orchestration** | control flow — who runs, when, in what order | — | n/a |

The move this repository argues for: **maximize Contract, keep Orchestration thin, and migrate
Convention into Contract wherever a test can harden it.** A rule that lives in a README depends
on being read and remembered. The same rule expressed as a type depends on nothing.

Some rules genuinely cannot migrate. Whether a narrative is well reasoned, whether a source
actually supports the claim it is attached to, whether the right method was chosen — those are
interpretive, and no type system checks them. That residue is exactly what the human gate is
for, and being honest about the boundary is part of the design rather than an embarrassment.

## Containment, not elimination

Nondeterminism is not the enemy and is not eliminated here. Language models are good at things
that are genuinely hard otherwise: interpreting a vague request, finding candidate sources,
drafting explanation. This design keeps all of that.

What it changes is *where the nondeterminism can reach*. Model output lands in an untyped
`Proposal`, which is explicitly untrusted, and must pass through a boundary that can only admit
it by constructing a typed object — which requires real provenance. The stochastic layer has no
write path to the record. So the uncertainty is contained inside contract-bounded steps rather
than propagating into the output.

This is why the claim is careful. Not "the system is deterministic" — the agents inside it are
not. The claim is that **determinism holds at the boundaries**, and the boundaries are where the
record is written.

## Rejections must be visible

The quietest failure in any evidence pipeline is the silent drop. Input arrives, fails
validation, gets discarded, and the resulting record looks immaculate. The reader cannot tell
the difference between "nothing was wrong here" and "something was wrong and we threw it away."

So every rejection becomes a **gap**: the question survives, along with a statement of what
would close it. An honest record needs a way to say *we looked and could not answer this*,
because omission and absence-of-evidence are indistinguishable to whoever reads it next.

## The human is a step, not a hope

Plenty of systems describe human oversight in a README and implement it nowhere: the pipeline
runs end to end and "someone reviews the output" is a hope about a calendar.

Here review is a state transition. An unreviewed record is a distinguishable object; the
exporter refuses it; approval requires a named reviewer, because "approved" with nobody attached
is not accountability. The gate deliberately does **not** judge quality — that is the judgement
the human is there to supply, and automating it away would defeat the point of having the step.
What it enforces is that the reviewer was *equipped*: gaps surfaced, unsourced material already
excluded, sources listed.

## Review from outside the author's blind spots

The same logic applies one level up, to the code of this repository itself. Much of it is
written with model assistance, and a reviewer from the same model family as the author was
trained on much the same distribution — it tends to miss what the author missed. So changes
here carry a review record (`reviews/`) naming the authoring model family and a red-team
reviewer from a **different** family, and a test fails any change-set that lands without its
record — or any record where the two families match. As with the human gate above, the
contract does not judge whether the review was good; that remains judgment. It makes skipping
the review a visible, deliberate act instead of a quiet one.

## What this costs

Honesty about the tradeoff: this design is more work up front, and it will refuse things you
wanted. A quantity you know is right will be rejected because you have not yet found the source
that says so. That friction is the mechanism functioning — but it is real friction, and a team
that is not prepared for it will be tempted to add an escape hatch.

Do not add the escape hatch. A contract with an override is a convention wearing a costume.
