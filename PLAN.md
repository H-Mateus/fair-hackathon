# FAIR Hackathon — Destructive FAIR-Score Walkthrough

## Goal
Build a git-tracked timeline where each commit makes a dataset *less* FAIR, with F-UJI scores recorded per commit. Participants then traverse the history in reverse to learn how to improve FAIR-ness.

- **Source dataset**: TIHM (Technology Integrated Health Management) — https://zenodo.org/records/7622128 (DOI 10.5281/zenodo.7622128, CC-BY-4.0).
- **Scoring tool**: F-UJI (https://github.com/pangaea-data-publisher/fuji), self-hosted in Docker.
- **Hosting for our mutated dataset**: local Python HTTP server, reachable from F-UJI container via `host.docker.internal`.

## Repository layout
```
fair_hackathon/
├── PLAN.md
├── README.md                 # Participant-facing hackathon brief
├── docker-compose.yml        # F-UJI server
├── dataset/                  # Self-hosted "landing page + data" — this is what we mutate
│   ├── index.html            # HTML landing page w/ embedded schema.org JSON-LD
│   ├── metadata.json         # DCAT / schema.org metadata
│   ├── LICENSE
│   ├── README.md
│   └── data/                 # Data files (CSV from TIHM)
├── server/serve.py           # Static HTTP server w/ content-negotiation + Signposting
├── scripts/
│   ├── measure.sh            # POST to F-UJI, save JSON + score summary
│   └── summarise.py          # Roll up assessments/ into a CSV/markdown table
└── assessments/              # One JSON per commit: NN_step-name.json
```

## Phase 0 — Setup
- [x] Confirm Docker + Python available
- [ ] Pull `fairsoftware/fuji` image
- [ ] Smoke-test F-UJI API
- [ ] Init git repo

## Phase 1 — Baseline (Zenodo, untouched)
- [ ] Run F-UJI against `https://doi.org/10.5281/zenodo.7622128`
- [ ] Save as `assessments/00_baseline_zenodo.json`
- [ ] Commit: "phase 1: baseline F-UJI score for Zenodo TIHM"

## Phase 2 — Self-hosted golden copy (high FAIR)
- [ ] Download TIHM zip from Zenodo, unpack into `dataset/data/`
- [ ] Write rich `index.html` with embedded JSON-LD (schema.org Dataset), DataCite metadata, dcterms, Signposting `<link>` headers via HTTP server
- [ ] Add LICENSE (CC-BY-4.0), README, dataset/metadata.json (DCAT-AP-style)
- [ ] Start local server, expose via `host.docker.internal:8000`
- [ ] Run F-UJI → `assessments/01_self_hosted_golden.json`
- [ ] Commit

## Phase 3 — Destructive iterations (one commit per regression)
Each row = one git commit + one F-UJI run. Order is intentional — earlier removals tank specific FAIR principles.

| # | Step                                  | Targets (principle) |
|---|----------------------------------------|---------------------|
| 02 | Remove Signposting link headers       | F1, F2, A1 |
| 03 | Strip JSON-LD `schema.org` block      | F2, I1 |
| 04 | Remove DataCite / persistent ID block | F1, F3 |
| 05 | Remove `LICENSE` file + license meta  | R1.1 |
| 06 | Drop content-type negotiation         | I1, A1.1 |
| 07 | Rename CSVs → opaque `.dat`           | I1, R1.3 |
| 08 | Strip README + provenance fields      | R1.2 |
| 09 | Remove keywords/subject metadata      | F2 |
| 10 | Replace stable URLs with random paths | F1, A1 |

Stretch / optional further regressions:
- Block HEAD requests
- Return 200 with HTML on missing pages (no 404)
- Strip charset declarations

## Phase 4 — Wrap-up
- [ ] Run `scripts/summarise.py` → `RESULTS.md` (table of scores per commit)
- [ ] Write participant-facing `README.md` (rules, how to run F-UJI, how to score, suggested moves)
- [ ] Final commit

## Notes for participants
- Reverse the journey: starting at the last commit, make commits that *raise* the F-UJI score.
- Every PR must include the F-UJI JSON for the new commit.
- Scoring categories: Findable, Accessible, Interoperable, Reusable.
