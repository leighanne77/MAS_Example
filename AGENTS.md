# AGENTS.md — how agents work in this repository

The vendor-neutral entry point for any coding agent (Claude Code reaches it via the
one-line `@AGENTS.md` import in `CLAUDE.md`). This file is short because the real rules
are contracts: they live in the type system and the tests, where an agent cannot drift
past them. What follows is the part that has to be said in prose.

1. **Test gate.** `pytest` before any commit; commit only on green. The negative tests
   are the point of the repository — a change that weakens what the system *refuses* is
   wrong even if everything still passes.
2. **The factory is the only writer.** Never construct a `Figure` or `Assessment` outside
   `factory.assemble()` / `derive()`, never add a convenience path that does, and never
   add an escape hatch to the contract. A contract with an override is a convention
   wearing a costume (`docs/philosophy.md`).
3. **Generated output is never edited.** `examples/wheeler_creek_output.html` is
   regenerated (`PYTHONPATH=src python examples/wheeler_creek.py`), never touched by
   hand. A drift test enforces byte-identity.
4. **Cross-family review.** Every code change-set carries a review record in `reviews/`
   naming the authoring model family and a red-team reviewer from a **different** model
   family, filled after the review runs. Enforced by
   `tests/test_review_records_are_cross_family.py`.
5. **The example stays fictional.** Wheeler Creek is not a real place and no real
   facility is ever added. Cited *sources* are real so provenance is followable; the
   *subject* never is.
6. **No new dependencies, no network.** One runtime dependency (`pydantic`) on purpose;
   the renderer cannot fetch or compute. Additions that need either are out of scope
   here (`docs/what-this-is-not.md`).
7. **Promote conventions.** If a rule in this file can be hardened by a test, write the
   test and shorten this file — that is the direction everything here moves.
