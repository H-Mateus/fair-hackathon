# FAIR Hackathon — repair the broken dataset!

You've inherited a dataset hosting setup that is **as un-FAIR as possible**.
This repo contains a self-hostable copy of the
[TIHM remote-monitoring dataset](https://doi.org/10.5281/zenodo.7622128),
served by a tiny static HTTP server, with **deliberately stripped metadata**.

Your job: send PRs that **raise the [F-UJI](https://github.com/pangaea-data-publisher/fuji)
FAIRness score** of the served URL.  Each PR should be one focused fix
(license, identifier, JSON-LD, …), include the new F-UJI assessment JSON,
and explain which FAIR metric it targets.

## Current state at HEAD

The data files are still there under `dataset/data/` — but they have an
opaque `.dat` extension, no `LICENSE`, no `README`, no machine-readable
metadata, and almost no `<head>` metadata.  F-UJI scores it at roughly
**8% overall** — only the URL itself is recognised.

The git history is the teaching tool: `git log` walks you backwards
through how the dataset was destroyed, one FAIR principle at a time.

### The decline

| # | Commit slug | F % | A % | I % | R % | **FAIR %** | What was removed |
|--:|-------------|----:|----:|----:|----:|-----------:|------------------|
| 00 | `baseline_zenodo`        | 100.00 | 100.00 |  75.00 | 70.00 | **83.33** | — (unmodified Zenodo DOI) |
| 01 | `self_hosted_golden`     |  71.43 | 100.00 | 100.00 | 80.00 | **83.33** | — (rich JSON-LD + DCAT + Signposting + LICENSE + README) |
| 02 | `strip_signposting`      |  71.43 | 100.00 | 100.00 | 80.00 | **83.33** | FAIR Signposting `<link rel>` headers (no score impact — JSON-LD still scored) |
| 03 | `strip_qualified_refs`   |  71.43 | 100.00 |  75.00 | 70.00 | **75.00** | DOI alt-id, `citation`, `isBasedOn`, `wasDerivedFrom` |
| 04 | `strip_license`          |  71.43 | 100.00 |  75.00 | 50.00 | **66.67** | license URL / `dcterms:license` / `dcterms:rights` |
| 05 | `strip_provenance`       |  50.00 | 100.00 |  75.00 | 50.00 | **60.42** | `publisher`, `datePublished`, `dateModified` |
| 06 | `strip_content_metadata` |  35.71 |  66.67 |  75.00 | 30.00 | **43.75** | `distribution`, `variableMeasured`, `temporalCoverage`, `conformsTo` |
| 07 | `strip_descriptive`      |  35.71 |  66.67 |  75.00 | 20.00 | **39.58** | `creator`, `keywords`, structured description |
| 08 | `strip_rdf_metadata`     |  35.71 |  33.33 |  25.00 | 20.00 | **27.08** | `metadata.jsonld`, `metadata.xml`, inline `<script type="application/ld+json">` |
| 09 | `strip_head_metadata`    |  14.29 |  33.33 |   0.00 |  0.00 |  **8.33** | `DC.*` `<meta>` tags, descriptive `<title>` |
| 10 | `obfuscate_files`        |  14.29 |  33.33 |   0.00 |  0.00 |  **8.33** | `.csv` → `.dat`, delete LICENSE + README (floor) |

`RESULTS.md` is the auto-generated version of the same table (with
earned/total counts and maturity column) — rerun
`python3 scripts/summarise.py` after every PR to refresh it.

## Prerequisites

Simplest way to evaluate the FAIRness of your fork is to use the instance FUJI themselves apply: [https://www.f-uji.net/index.php?action=test](https://www.f-uji.net/index.php?action=test)

Otherwise you can build it to run locally with Docker:

- Docker (for F-UJI)
- Python 3.10+ (for the static server and the helper scripts)

## One-time setup

```bash
# 1. Start F-UJI on port 1071
docker run -d --name fuji -p 1071:1071 ghcr.io/pangaea-data-publisher/fuji:3.5.0

# 2. Wait until it answers (the connexion startup takes ~30 s):
until curl -fs http://localhost:1071/fuji/api/v1/openapi.json -o /dev/null;
  do sleep 2; done
echo "F-UJI ready."
```

Default credentials are `marvel` / `wonderwoman` (set in the image; the
scripts use them automatically).

## Serving the dataset

```bash
python3 server/serve.py --port 8000          # blocking; Ctrl-C to stop
```

The server is intentionally minimal but FAIR-aware:

- emits FAIR Signposting `Link:` headers parsed from `<link rel>` in
  `dataset/index.html`,
- content-negotiates on `Accept` for the root URL — `application/ld+json`
  returns `dataset/metadata.jsonld` if present, `application/rdf+xml`
  returns `dataset/metadata.xml` if present, else the HTML page,
- sets correct `Content-Type` and a friendly `Content-Disposition` on
  data files,
- **does not** hard-code any dataset metadata — everything F-UJI sees
  comes from files under `dataset/`.

The F-UJI container reaches the server via `http://host.docker.internal:8000/`
on macOS / Windows Docker Desktop.  On Linux pass `--add-host` or use a
shared docker network.

## Measuring a change

```bash
scripts/measure.sh my_change "http://host.docker.internal:8000/"
```

This POSTs to `/fuji/api/v1/evaluate`, prints a one-line summary, and
saves the full JSON to `assessments/my_change.json`.  After every PR,
also run:

```bash
python3 scripts/summarise.py        # rebuilds RESULTS.md
```

## PR rules

1. **One FAIR principle per PR.**  Tackle license, or provenance, or
   identifiers — but not all three at once.
2. **No edits outside `dataset/`** unless absolutely needed.  The server
   and scripts are infrastructure and should keep working unchanged.
3. **Include the assessment JSON** for your PR in `assessments/`, named
   `NN_short_slug.json`, where `NN` keeps the timeline monotonic.
4. **Cite the metric** in the PR description, e.g. *"adds Signposting
   `cite-as` Link header to satisfy FsF-F1-01D"*.
5. **No new external metadata services.**  All metadata must live in the
   `dataset/` directory; the server reads it from there.

## Walk the timeline

```bash
git log --oneline                  # see every destructive commit
git diff de0b39b 6daafb4 -- dataset/   # full diff: golden -> floor
git show 4199dec -- dataset/index.html # one specific destruction
```

Use the older commits as a cheat sheet for what each FAIR signal looks
like in practice.

## Repository layout

```
PLAN.md                  Project plan and destructive sequence
README.md                This file
RESULTS.md               Auto-generated F-UJI score timeline
assessments/*.json       One F-UJI JSON per commit
dataset/                 The dataset and its metadata (mutate this!)
  index.html             Landing page
  data/                  Data files
  (metadata.jsonld)      Machine-readable metadata (deleted at HEAD)
  (metadata.xml)         RDF/XML metadata        (deleted at HEAD)
  (LICENSE)              CC-BY-4.0 text          (deleted at HEAD)
  (README.md)            Dataset description     (deleted at HEAD)
server/serve.py          Tiny FAIR-aware static server
scripts/measure.sh       Run F-UJI and save JSON for one identifier
scripts/summarise.py     Rebuild RESULTS.md from assessments/
```

## Acknowledgements

- Source dataset: Palermo et al., 2023.
  *TIHM: An open dataset for remote healthcare monitoring in dementia.*
  Zenodo: [10.5281/zenodo.7622128](https://doi.org/10.5281/zenodo.7622128),
  CC-BY-4.0.
- F-UJI: PANGAEA / Pangaea Data Publisher,
  [pangaea-data-publisher/fuji](https://github.com/pangaea-data-publisher/fuji).
