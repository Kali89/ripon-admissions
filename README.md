# Ripon Grammar School — Admissions Boundary Analysis

Estimates the likely out-of-catchment admissions boundary (maximum day-place distance) at Ripon Grammar School in future entry years, using historical North Yorkshire admissions statistics and ONS birth cohort data.

## Context

Ripon Grammar School (RGS) is a non-selective state school with a defined catchment area. The admissions priority order places all in-catchment children above out-of-catchment children, who are then ranked by straight-line distance from the school. This project tracks the "distance of last child allocated" metric — the effective boundary for out-of-catchment day pupils — across 12 entry years (2013–2025) and builds simple projection models.

**PAN**: 117 (including 14 boarding places) → approximately 103 day places.

## Repository structure

```
ripon_admissions/
├── data/
│   ├── 2013-14-all-secondary-stats-data.xlsx   # raw North Yorkshire data
│   │   … (one file per year through 2025-26)
│   └── processed/
│       ├── rgs_admissions_clean.csv             # cleaned RGS rows, one per year
│       ├── ons_births_harrogate.csv             # Harrogate district births by cohort
│       ├── rgs_with_births.csv                  # merged analysis dataset
│       └── ons_births_la_msoa_1992_2021.xlsx    # cached ONS source file
├── notebooks/
│   └── 01_eda_and_model.ipynb                  # EDA, correlation analysis, projections
├── src/
│   ├── data_loader.py                           # normalise & parse all admissions years
│   ├── ons_births.py                            # download & extract ONS birth data
│   └── build_clean_data.py                      # regenerate processed CSVs
├── requirements.txt
└── README.md
```

## Quick start

```bash
# 1. Install dependencies (recommend a virtual environment)
pip install -r requirements.txt

# 2. Regenerate clean data files (Excel files must be in data/)
python -m src.build_clean_data

# 3. Open the analysis notebook
jupyter notebook notebooks/01_eda_and_model.ipynb
```

## Data sources

| Source | Coverage | Key column |
|--------|----------|------------|
| North Yorkshire secondary admissions statistics | 2013-14 → 2025-26 (annual Excel) | Distance of last out-of-catchment day pupil allocated |
| ONS live births by local authority & MSOA, 1992–2021 | Harrogate district (E07000165) | Total births per mid-year period |

ONS source:
> *Numbers of live births by local authority and MSOA, England and Wales: mid-year 1992 to mid-year 2021*
> https://www.ons.gov.uk/peoplepopulationandcommunity/birthsdeathsandmarriages/livebirths/adhocs/1391numbersoflivebirthsbylocalauthorityandmsoaenglandandwalesmidyear1992tomidyear2021

## Key findings (as of 2025-26 data)

- Historical out-of-catchment day boundary: **6.6 – 13.7 miles** (excluding the anomalous 2022-23 value of 20.4 miles)
- Central projection for 2026–2031: approximately **8–11 miles**, with wide uncertainty
- Harrogate district birth cohorts have declined from ~1,700 (2007 births) to ~1,437 (2014 births), a mild tailwind for out-of-catchment applicants
- Applications received is a stronger predictor of the boundary than birth cohort size alone

## Known data gaps

- **In-catchment vs out-of-catchment split** — would sharpen the model significantly; obtainable via FOI to North Yorkshire admissions
- **2022-23 anomaly** (20.4 miles) — cause unknown; may reflect unusual in-catchment take-up or a data error
- **ONS births post-2021** — needed for entry years 2032+; use ONS sub-national population projections
