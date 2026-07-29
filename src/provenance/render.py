"""Export view. The record is the deliverable; this is one projection of it.

Two properties worth noticing, because they are the reason rendering is its own module:

  1. The renderer reads the record and writes HTML. It cannot add a number, because it has no
     way to build one — it never sees a proposer and never calls the factory. A presentation
     layer that can invent content is a hole in every guarantee upstream of it.
  2. Every figure is rendered *with* its provenance, and every gap is rendered too. An export
     that quietly omits the open questions would misrepresent the record it came from.

The record is format-agnostic: HTML here, but JSON, CSV or a structured feed are the same
projection over the same typed object.
"""
from __future__ import annotations

import html

from provenance.gate import require_reviewed
from provenance.models import Assessment

_CSS = """
body{font:15px/1.55 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;
     max-width:820px;margin:2rem auto;padding:0 1.2rem;color:#1a1a1a}
h1{font-size:1.5rem;margin-bottom:.2rem} .sub{color:#666;font-size:.9rem;margin-bottom:1.6rem}
.banner{background:#fff4e5;border-left:4px solid #d9822b;padding:.7rem 1rem;margin:1rem 0;font-size:.9rem}
.finding{border:1px solid #e3e3e3;border-radius:8px;padding:.9rem 1.1rem;margin:.8rem 0}
.fig{background:#f6f8fa;border-left:3px solid #0969da;padding:.5rem .8rem;margin:.6rem 0;font-size:.92rem}
.fig .val{font-weight:600} .src{color:#57606a;font-size:.82rem;margin-top:.25rem}
.src a{color:#0969da} .gap{border-left:3px solid #bf8700;background:#fff8e5;padding:.5rem .8rem;
     margin:.5rem 0;font-size:.9rem}
h2{font-size:1.05rem;margin-top:1.8rem;border-bottom:1px solid #e3e3e3;padding-bottom:.3rem}
.rev{color:#1a7f37;font-size:.85rem} ol.bib{font-size:.85rem;color:#57606a}
"""


def _e(s: str) -> str:
    return html.escape(str(s))


def to_html(assessment: Assessment, *, require_review: bool = True) -> str:
    """Render the record. By default refuses to export an unreviewed assessment — the human
    gate is not advisory."""
    if require_review:
        assessment = require_reviewed(assessment)

    parts: list[str] = [
        "<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>",
        f"<title>{_e(assessment.site_name)} — assessment</title><style>{_CSS}</style></head><body>",
        f"<h1>{_e(assessment.site_name)}</h1>",
        f"<div class='sub'>as of {assessment.as_of.isoformat()}"
        + (f" · reviewed by <span class='rev'>{_e(assessment.reviewed_by)}</span>"
           if assessment.reviewed_by else "")
        + "</div>",
    ]

    if assessment.synthetic:
        parts.append(
            "<div class='banner'><b>Synthetic example.</b> This site is fictional and exists "
            "only to demonstrate the mechanism. The cited source is real and public; the "
            "facility is not.</div>")

    parts.append("<h2>Findings</h2>")
    if not assessment.findings:
        parts.append("<p><i>No findings were admitted.</i></p>")
    for f in assessment.findings:
        parts.append(f"<div class='finding'><div>{_e(f.statement)}</div>")
        for fig in f.figures:
            parts.append(
                f"<div class='fig'><span class='val'>{fig.value:,.2f} {_e(fig.unit)}</span>"
                f" — {_e(fig.label)}")
            if fig.calc_trace:
                parts.append(f"<div class='src'>computed: <code>"
                             f"{_e(fig.calc_trace.formula)}</code></div>")
            for c in fig.citations:
                parts.append(f"<div class='src'>{_e(c.source)} · "
                             f"<a href='{_e(c.url)}'>{_e(c.url)}</a> "
                             f"(accessed {c.accessed.isoformat()})</div>")
            parts.append("</div>")
        parts.append("</div>")

    # Gaps are part of the export, always. Omitting them would misrepresent the record.
    parts.append("<h2>Open gaps</h2>")
    if not assessment.gaps:
        parts.append("<p><i>None recorded.</i></p>")
    for g in assessment.gaps:
        parts.append(f"<div class='gap'><b>{_e(g.gap_id)}</b> — {_e(g.question)}"
                     f"<div class='src'>closes with: {_e(g.fills_from)}</div></div>")

    parts.append("<h2>Sources</h2><ol class='bib'>")
    for s in assessment.bibliography():
        parts.append(f"<li>{_e(s)}</li>")
    parts.append("</ol></body></html>")
    return "\n".join(parts)
