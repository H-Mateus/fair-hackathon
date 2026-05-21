#!/usr/bin/env bash
# Run F-UJI against an identifier and save the full result JSON + a one-line summary.
#
# Usage:  scripts/measure.sh <slug> <object_identifier>
#   <slug>             — filename slug, e.g. "00_baseline_zenodo"
#   <object_identifier> — DOI URL or http(s) URL F-UJI should evaluate
#
# Reads F-UJI host/creds from env (defaults: marvel:wonderwoman @ localhost:1071):
#   FUJI_URL  FUJI_USER  FUJI_PASS

set -euo pipefail

slug="${1:?missing slug}"
ident="${2:?missing identifier}"
out_dir="$(cd "$(dirname "$0")/.." && pwd)/assessments"
mkdir -p "$out_dir"
out_json="$out_dir/${slug}.json"

FUJI_URL="${FUJI_URL:-http://localhost:1071/fuji/api/v1/evaluate}"
FUJI_USER="${FUJI_USER:-marvel}"
FUJI_PASS="${FUJI_PASS:-wonderwoman}"

payload=$(mktemp -t fuji_payload.XXXXXX.json)
trap 'rm -f "$payload"' EXIT
IDENT="$ident" python3 - "$payload" <<'PY'
import json, os, sys
json.dump({"object_identifier": os.environ["IDENT"], "test_debug": False, "use_datacite": True},
          open(sys.argv[1], "w"))
PY

echo "→ Assessing: $ident"
echo "  endpoint:  $FUJI_URL"
echo "  output:    $out_json"

curl -sS -u "${FUJI_USER}:${FUJI_PASS}" -X POST "$FUJI_URL" \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json' \
  --data-binary "@${payload}" \
  -o "$out_json"

python3 - "$out_json" <<'PY'
import json, sys, pathlib
p = pathlib.Path(sys.argv[1])
data = json.loads(p.read_text())
summary  = data.get('summary', {})
earned   = summary.get('score_earned', {})
total    = summary.get('score_total', {})
sc       = summary.get('score_percent', {})
maturity = summary.get('maturity', {})
print(f"\n=== {p.stem} ===")
print(f"  Earned/Total : {earned.get('FAIR')}/{total.get('FAIR')}  "
      f"(F {earned.get('F')}/{total.get('F')}  A {earned.get('A')}/{total.get('A')}  "
      f"I {earned.get('I')}/{total.get('I')}  R {earned.get('R')}/{total.get('R')})")
print(f"  Overall FAIR : {sc.get('FAIR')}%  "
      f"(F {sc.get('F')}%  A {sc.get('A')}%  I {sc.get('I')}%  R {sc.get('R')}%)")
print(f"  Maturity     : F {maturity.get('F')} · A {maturity.get('A')} · "
      f"I {maturity.get('I')} · R {maturity.get('R')} (overall {maturity.get('FAIR')})")
PY
