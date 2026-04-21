---
name: Work done
description: Analysis completed, data sources integrated, key findings, and important corrections made
type: project
---

## Data sources integrated

1. **North Yorkshire secondary admissions statistics** — Excel files 2013-14 to 2025-26, one per year, in `data/`. Parsed by `src/data_loader.py` into `data/processed/rgs_admissions_clean.csv`.
2. **ONS births (Harrogate district, E07000165)** — 1992–2021. Parsed by `src/ons_births.py` into `data/processed/ons_births_harrogate.csv`.
3. **FOI from RGS (Jan 2024)** — Test statistics 2013–2023 (total tested, cutoff mark, total passing, intake) and birth-season distribution Y7–Y13. Hardcoded in notebook cell a004.
4. **FOI CN29389 from North Yorkshire Council** — Applications and offers split by catchment status (2018–2025 for apps, 2013–2025 for offers), distance-criterion offer counts, and distance methodology confirmation. Parsed by `src/foi_loader.py` into `data/processed/rgs_full.csv`.

**Master merged dataset**: `data/processed/rgs_full.csv` — one row per entry year 2013–2025, all sources combined.

## Key findings

- **RGS boundary at 12.4 miles (road)**: exceeded in only 2/11 non-outlier years. ~18% base rate.
- **2022-23 outlier (20.36 miles)** is explained: only 72 out-of-catchment applications that year (lowest in series), so the school ran out of closer candidates. Not an anomaly to bank on.
- **Out-of-catchment applications nearly doubled** (83 in 2018-19 → 150 in 2024-25) while offers held steady at ~20-25/year. The out-of-catchment offer rate has roughly halved — this is the clearest headwind.
- **Pass rate (~50%)** is not contradictory with the 28% threshold: the 28% is calculated over Ripon-area test-takers only; out-of-catchment applicants are self-selected and pass at a much higher rate. The rising overall pass rate reflects growth in out-of-catchment applicants.
- **Distance measurement**: road-routed (not straight-line), confirmed by FOI CN29389 Q3. The published boundary distances in the NYCC stats are road distances. Haversine/straight-line calculations in the notebook underestimate the official figure by ~1.1–1.5×.
- **Boroughbridge High School**: user is in catchment, guaranteed a place. Not the focus of analysis.
- **Outwood Academy Easingwold**: at 9.6 miles road, both years with distance data showed boundaries well beyond this (12.15 mi in 2022-23, 17.81 mi in 2023-24). Probably 80-90%+ chance if out-of-catchment. Data is sparse — only 2 years of hard distance figures.
- **Birth season**: no relative age effect at RGS — test uses age-standardised scores. Summer-born children are not disadvantaged.
- **Harrogate births 2019 (cohort for entry 2030)**: 1,262 — the lowest in the ONS series. A tailwind for future boundary.

## Figures generated (in `data/processed/`)

- `fig_foi_test_stats.png` — test volume, pass rates, cut-off, surplus
- `fig_birth_seasons.png` — birth season distribution (no relative age effect)
- `fig_timeseries.png` — 4-panel: boundary distance, tests, surplus, births
- `fig_correlations.png` — nothing predicts the boundary well
- `fig_historical_dist.png` — histogram + empirical CDF of boundary distances
- `fig_projections.png` — historical + projected boundary to 2032 (3 demand scenarios)
- `fig_distance_safety.png` — P(place) by straight-line distance, key villages marked
- `fig_catchment_split.png` — out-of-catchment applications vs offers, offer rate trend (FOI CN29389)

## Important corrections already made

- Distance methodology corrected throughout notebook (was incorrectly described as straight-line)
- Pass rate explanation corrected (norm-referenced to local cohort, not all test-takers)
- 2022-23 outlier explained (thin out-of-catchment demand, not a data error)
- Open questions table updated to reflect what FOI CN29389 answered
