"""Render a Markdown PR comment from two F-UJI assessment JSONs.

Usage:
    python3 scripts/pr_comment.py <baseline.json> <pr.json>

Writes the rendered comment to stdout.  Stdlib only.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

DIMENSIONS = ("F", "A", "I", "R")


def _load(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text())


def _fmt_delta(value: float) -> str:
    if value > 0:
        return f"🟢 +{value:.2f}"
    if value < 0:
        return f"🔴 {value:.2f}"
    return "·  0.00"


def _row(dim: str, base: dict, head: dict) -> str:
    be, bt = base["score_earned"].get(dim, 0), base["score_total"].get(dim, 0)
    he, ht = head["score_earned"].get(dim, 0), head["score_total"].get(dim, 0)
    bp = base["score_percent"].get(dim, 0.0)
    hp = head["score_percent"].get(dim, 0.0)
    bm = base["maturity"].get(dim, 0)
    hm = head["maturity"].get(dim, 0)
    return (
        f"| **{dim}** "
        f"| {be:g}/{bt} ({bp:.2f}%) "
        f"| {he:g}/{ht} ({hp:.2f}%) "
        f"| {_fmt_delta(hp - bp)} "
        f"| {bm} → {hm} |"
    )


def _metric_flips(base: dict, head: dict) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    base_map = {r["metric_identifier"]: r for r in base.get("results", [])}
    head_map = {r["metric_identifier"]: r for r in head.get("results", [])}
    gained, lost = [], []
    for mid, hr in head_map.items():
        br = base_map.get(mid)
        if br is None:
            continue
        if br.get("test_status") == "fail" and hr.get("test_status") == "pass":
            gained.append((mid, hr.get("metric_name", "")))
        elif br.get("test_status") == "pass" and hr.get("test_status") == "fail":
            lost.append((mid, hr.get("metric_name", "")))
    return gained, lost


def render(baseline: dict, pr: dict) -> str:
    bs = baseline["summary"]
    hs = pr["summary"]
    fair_delta = hs["score_percent"].get("FAIR", 0.0) - bs["score_percent"].get("FAIR", 0.0)
    headline = (
        f"### 🧪 F-UJI FAIRness assessment\n\n"
        f"**FAIR: {hs['score_percent'].get('FAIR', 0.0):.2f}%** "
        f"(initial-commit baseline {bs['score_percent'].get('FAIR', 0.0):.2f}% — {_fmt_delta(fair_delta)})\n\n"
    )
    table = (
        "| Dimension | initial | PR | Δ % | Maturity |\n"
        "|-----------|-------:|---:|----:|---------:|\n"
        + "\n".join(_row(d, bs, hs) for d in DIMENSIONS)
        + "\n"
    )
    gained, lost = _metric_flips(baseline, pr)
    flips = ""
    if gained or lost:
        flips_lines = ["", "<details><summary>Per-metric changes</summary>", ""]
        if gained:
            flips_lines.append("**🟢 Newly passing**")
            flips_lines.append("")
            flips_lines += [f"- `{mid}` — {name}" for mid, name in gained]
            flips_lines.append("")
        if lost:
            flips_lines.append("**🔴 Newly failing**")
            flips_lines.append("")
            flips_lines += [f"- `{mid}` — {name}" for mid, name in lost]
            flips_lines.append("")
        flips_lines.append("</details>")
        flips = "\n".join(flips_lines) + "\n"
    footer = (
        "\n<sub>Scored by "
        f"F-UJI `{pr.get('software_version', '?')}` against "
        f"`{pr.get('request', {}).get('object_identifier', '?')}`. "
        "Full JSON in the workflow artifact.</sub>\n"
    )
    return headline + table + flips + footer


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    baseline = _load(argv[1])
    pr = _load(argv[2])
    sys.stdout.write(render(baseline, pr))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
