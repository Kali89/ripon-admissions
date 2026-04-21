---
name: Update guide
description: Exactly what to do when new annual admissions data arrives, in order
type: project
---

## When new annual data arrives (North Yorkshire publish each April)

### 1. Add the new Excel file
Drop the new year's file into `data/`. It will be picked up automatically by `src/data_loader.py` via glob patterns matching `*secondary*stats*.xlsx`, `*secondary*data*.xlsx`, or `*secondary*statistics*.xlsx`.

### 2. Rebuild the processed CSVs
```
python -m src.build_clean_data
```
This regenerates:
- `data/processed/rgs_admissions_clean.csv`
- `data/processed/ons_births_harrogate.csv`
- `data/processed/rgs_with_births.csv`
- `data/processed/rgs_full.csv` (includes FOI CN29389 catchment split data)

Check the printed output to confirm the new year appears and `day_distance_miles` parsed correctly. The `distance_raw` field is messy — if parsing fails for the new year, fix `_extract_day_miles()` in `src/data_loader.py`.

### 3. Update FOI catchment data if a new FOI response arrives
Edit `src/foi_loader.py` — append the new year's values to each list. The lists must stay in sync (one entry per entry year, starting 2013). The FOI CN29389 data covers up to 2025-26; anything beyond that needs a new FOI request to NYC.

### 4. Update FOI test statistics if new data arrives
The test stats (total tested, cutoff mark, total passing, intake) are hardcoded in notebook cell `a004`. The series currently runs 2013–2023. Extend it when new FOI data from RGS arrives.

### 5. Re-execute the notebook
```
jupyter nbconvert --to notebook --execute --inplace notebooks/01_eda_and_model.ipynb
```
This regenerates all 8 figures in `data/processed/`.

### 6. Check the key numbers
After re-executing, verify:
- The new boundary distance for the latest entry year looks plausible
- The user's probability (12.4 miles road distance) — check how many years now exceed it
- The out-of-catchment application trend (fig_catchment_split.png) — is it still rising?
- The Outwood Academy Easingwold boundary (9.6 miles road) — update if new distance data appears

### 7. Update `USER_DISTANCE` if needed
`USER_DISTANCE = 10.34` in notebook cell `a002` is the **straight-line** (Haversine) distance — used for the geographic probability chart. The actual road distance is **12.4 miles**. The straight-line figure is kept for the chart because all other locations are also plotted as straight-line. Do not change it to 12.4. The road distance comparison is done separately in the summary text.

### 8. Commit and push
```
git add data/<new-file>.xlsx data/processed/*.csv data/processed/fig_*.png notebooks/01_eda_and_model.ipynb
git commit -m "Add <year> admissions data and regenerate figures"
git push
```

---

## What we're still waiting for / open questions

- **ONS births 2022+** — needed for projections beyond entry year 2033. Check ONS sub-national population projections when available.
- **Annual RGS FOI update** — the test statistics (total tested, cutoff, passing) currently end at 2023. A new FOI to RGS each year extends this series.
- **In/out catchment split pre-2018** — NYC confirmed they don't hold this data. It cannot be recovered.
- **Out-of-catchment day qualifiers (separate from boarding)** — not provided in CN29389. Would need a further FOI to get the number who passed the test and applied for day places specifically, which would give a cleaner competition signal than total surplus passers.
- **Outwood Academy Easingwold distance data** — only have 2022-23 and 2023-24 boundary distances. More data points would improve confidence in the ~80-90% estimate.
- **Road-routed distance for Boroughbridge and other relocation candidates** — the geographic analysis still uses straight-line. If the user is seriously considering relocation, road-route each candidate village.
