# F-UJI Score Timeline

Generated from `assessments/*.json`.  Each row corresponds to one commit on this branch.

Columns are F-UJI subscores: F=Findable, A=Accessible, I=Interoperable, R=Reusable.  Earned/total in parens.

| # | Step (commit slug) | FAIR % | F | A | I | R | Maturity | Notes |
|---|--------------------|-------:|--:|--:|--:|--:|---------:|-------|
| 00 | `baseline_zenodo` | **83.33** | 100.00 (7.0/7) | 100.00 (3.0/3) | 75.00 (3.0/4) | 70.00 (7.0/10) | 2.5 | doi:10.5281/zenodo.7622128 |
| 01 | `self_hosted_golden` | **83.33** | 71.43 (5.0/7) | 100.00 (3.0/3) | 100.00 (4.0/4) | 80.00 (8.0/10) | 2.5 | (self-hosted) |
| 02 | `strip_signposting` | **83.33** | 71.43 (5.0/7) | 100.00 (3.0/3) | 100.00 (4.0/4) | 80.00 (8.0/10) | 2.5 | (self-hosted) |
| 03 | `strip_qualified_refs` | **75.00** | 71.43 (5.0/7) | 100.00 (3.0/3) | 75.00 (3.0/4) | 70.00 (7.0/10) | 2.25 | (self-hosted) |
| 04 | `strip_license` | **66.67** | 71.43 (5.0/7) | 100.00 (3.0/3) | 75.00 (3.0/4) | 50.00 (5.0/10) | 2.0 | (self-hosted) |
| 05 | `strip_provenance` | **60.42** | 50.00 (3.5/7) | 100.00 (3.0/3) | 75.00 (3.0/4) | 50.00 (5.0/10) | 2.0 | (self-hosted) |
| 06 | `strip_content_metadata` | **43.75** | 35.71 (2.5/7) | 66.67 (2.0/3) | 75.00 (3.0/4) | 30.00 (3.0/10) | 1.5 | (self-hosted) |
| 07 | `strip_descriptive` | **39.58** | 35.71 (2.5/7) | 66.67 (2.0/3) | 75.00 (3.0/4) | 20.00 (2.0/10) | 1.5 | (self-hosted) |
| 08 | `strip_rdf_metadata` | **27.08** | 35.71 (2.5/7) | 33.33 (1.0/3) | 25.00 (1.0/4) | 20.00 (2.0/10) | 1.0 | (self-hosted) |
| 09 | `strip_head_metadata` | **8.33** | 14.29 (1/7) | 33.33 (1/3) | 0.00 (0/4) | 0.00 (0/10) | 1.0 | (self-hosted) |
| 10 | `obfuscate_files` | **8.33** | 14.29 (1/7) | 33.33 (1/3) | 0.00 (0/4) | 0.00 (0/10) | 1.0 | (self-hosted) |
| 11 | `restore_license` | **8.33** | 14.29 (1/7) | 33.33 (1/3) | 0.00 (0/4) | 0.00 (0/10) | 1.0 | (self-hosted) |

## How to read this

- Row `00_baseline_zenodo` is the unmodified Zenodo DOI — our gold standard.
- Row `01_self_hosted_golden` is our locally-hosted copy with rich metadata (JSON-LD + DCAT + Signposting + LICENSE + README).  Same overall % as Zenodo with a different breakdown.
- Rows `02_…` through `10_…` are destructive commits — each removes one FAIR signal.  Each commit message names the removal and the score delta.
- The score floor (~8%) is reached when every metadata signal is stripped and only the URL itself remains.
