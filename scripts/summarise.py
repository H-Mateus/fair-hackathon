"""Roll up every JSON in `assessments/` into a Markdown scoreboard.

Output:
  - prints a Markdown table to stdout
  - writes `RESULTS.md` at repo root (overwriting)
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger("summarise")

REPO_ROOT      = Path(__file__).resolve().parent.parent
ASSESSMENT_DIR = REPO_ROOT / "assessments"
RESULTS_PATH   = REPO_ROOT / "RESULTS.md"

HEADER = (
    "| # | Step (commit slug) | FAIR % | F | A | I | R | Maturity | Notes |\n"
    "|---|--------------------|-------:|--:|--:|--:|--:|---------:|-------|\n"
)


def _row(path: Path) -> Optional[str]:
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("Skipping %s: %s", path.name, exc)
        return None
    summary  = data.get("summary", {})
    sc       = summary.get("score_percent", {})
    earned   = summary.get("score_earned", {})
    total    = summary.get("score_total", {})
    maturity = summary.get("maturity", {})
    ident    = data.get("request", {}).get("object_identifier", "")
    slug     = path.stem
    idx, *rest = slug.split("_", 1)
    name = rest[0] if rest else slug
    notes = ident.replace("http://host.docker.internal:8000/", "(self-hosted)") \
                 .replace("https://doi.org/", "doi:")
    def fmt(x: object) -> str:
        return f"{x:.2f}" if isinstance(x, (int, float)) else str(x)
    return (
        f"| {idx} | `{name}` | **{fmt(sc.get('FAIR'))}** "
        f"| {fmt(sc.get('F'))} ({earned.get('F')}/{total.get('F')}) "
        f"| {fmt(sc.get('A'))} ({earned.get('A')}/{total.get('A')}) "
        f"| {fmt(sc.get('I'))} ({earned.get('I')}/{total.get('I')}) "
        f"| {fmt(sc.get('R'))} ({earned.get('R')}/{total.get('R')}) "
        f"| {maturity.get('FAIR')} | {notes} |"
    )


def main() -> int:
    rows: list[str] = []
    for path in sorted(ASSESSMENT_DIR.glob("*.json")):
        row = _row(path)
        if row:
            rows.append(row)
    table = HEADER + "\n".join(rows) + "\n"
    body = (
        "# F-UJI Score Timeline\n\n"
        f"Generated from `{ASSESSMENT_DIR.relative_to(REPO_ROOT)}/*.json`.  "
        "Each row corresponds to one commit on this branch.\n\n"
        "Columns are F-UJI subscores: F=Findable, A=Accessible, "
        "I=Interoperable, R=Reusable.  Earned/total in parens.\n\n"
        + table
        + "\n## How to read this\n\n"
        "- Row `00_baseline_zenodo` is the unmodified Zenodo DOI — our gold standard.\n"
        "- Row `01_self_hosted_golden` is our locally-hosted copy with rich metadata "
        "(JSON-LD + DCAT + Signposting + LICENSE + README).  Same overall % as Zenodo "
        "with a different breakdown.\n"
        "- Rows `02_…` through `10_…` are destructive commits — each removes one "
        "FAIR signal.  Each commit message names the removal and the score delta.\n"
        "- The score floor (~8%) is reached when every metadata signal is stripped "
        "and only the URL itself remains.\n"
    )
    RESULTS_PATH.write_text(body)
    print(body)
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    raise SystemExit(main())
