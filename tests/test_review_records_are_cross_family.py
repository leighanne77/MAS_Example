"""Cross-family review gate.

Code in this repository is written with model assistance, and a reviewer from the same
model family as the author shares the author's training, idioms, and blind spots. So the
review that counts comes from a different family — and like every other rule here, that
is enforced as a contract, not remembered as a convention:

  1. A change-set touching code carries a review record in `reviews/`, added in the same
     change-set — checked against the working tree (fires pre-commit) AND against the
     HEAD commit (fires in a clean CI checkout), so a clean checkout is not a bypass.
     Commits predating the ledger are exempt (no `reviews/` in their tree).
  2. Every record in the ledger names the authoring model family and a red-team reviewer
     family, the two DIFFER, and the verdict APPROVES. A recorded REJECT keeps the gate
     red: the fixes it forced are new code and need their own review round.

The gate enforces that the review is recorded, cross-family, and approving. Whether the
review was any good is human judgment — the same honest boundary as the named-reviewer
gate in the pipeline itself.

Hardened after its own first cross-family review round, which is the mechanism working:
the reviewer found the clean-checkout bypass, a rename-parsing gap, and a quoted-value
bypass in this very file.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATED = ("src/", "examples/", "tests/")
REVIEWS = ROOT / "reviews"
_FIELD = re.compile(
    r"^(author_model|author_family|red_team_model|red_team_family|verdict):\s*(.+?)\s*$",
    re.M)


def _git(*args: str) -> str | None:
    try:
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True,
                              text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return None  # not a git checkout (e.g. an assembled tree): ledger checks still run


def _paths(lines: list[str]) -> list[str]:
    out = []
    for line in lines:
        p = line.strip().strip('"')
        if " -> " in p:  # rename entries name both sides; the NEW path is the landed one
            p = p.split(" -> ", 1)[1].strip().strip('"')
        if p:
            out.append(p)
    return out


def _worktree_changeset() -> list[str]:
    status = _git("status", "--porcelain", "-uall") or ""
    return _paths([line[3:] for line in status.splitlines() if line.strip()])


def _head_changeset() -> list[str]:
    if not (_git("ls-tree", "HEAD", "reviews/") or "").strip():
        return []  # pre-ledger commit, or no git: nothing checkable here
    diff = _git("diff", "--name-only", "HEAD~1..HEAD")
    return _paths(diff.splitlines()) if diff else []


def _fields(p: Path) -> dict[str, str]:
    return {k: v.strip().strip('"').strip("'")
            for k, v in _FIELD.findall(p.read_text(encoding="utf-8"))}


def test_code_change_sets_carry_a_review_record():
    for label, changed in (("working tree", _worktree_changeset()),
                           ("HEAD commit", _head_changeset())):
        code = [p for p in changed if p.startswith(GATED)]
        if not code:
            continue
        records = [p for p in changed
                   if p.startswith("reviews/") and p.endswith(".md")
                   and not p.endswith("0_TEMPLATE.md")]
        assert records, (
            f"{label} change-set touches code ({len(code)} file(s), e.g. {code[:3]}) but "
            "carries no review record — copy reviews/0_TEMPLATE.md to "
            "reviews/<date>_<slug>.md and have the change red-teamed by a different "
            "model family than its author")


def test_no_record_in_the_ledger_is_unreviewed_or_same_family():
    for p in sorted(REVIEWS.glob("*.md")):
        if p.name == "0_TEMPLATE.md":
            continue
        f = _fields(p)
        for k in ("author_model", "author_family", "red_team_model", "red_team_family"):
            v = f.get(k, "")
            assert v and v.upper() != "UNREVIEWED", (
                f"{p.name}: {k} is missing or UNREVIEWED — the red-team happens before "
                "the change lands; fill the record after the review runs, not before")
        assert f["author_family"].lower() != f["red_team_family"].lower(), (
            f"{p.name}: red_team_family must differ from author_family — a same-family "
            "reviewer shares the author's blind spots")
        v = f.get("verdict", "")
        assert v.upper().startswith("APPROVE"), (
            f"{p.name}: verdict is {v or 'missing'!r} — the ledger accepts only an "
            "approving verdict (APPROVE / APPROVE WITH FIXES); a REJECT stays red until "
            "a follow-up review approves the fixes")
