"""
Build the clean analysis-ready CSV files:
  data/processed/rgs_admissions_clean.csv   — one row per entry year for RGS
  data/processed/ons_births_harrogate.csv   — Harrogate births by cohort year

Run:
    python -m src.build_clean_data
"""

from __future__ import annotations

import os
import sys

import pandas as pd

# Allow running as a script from the repo root
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.data_loader import build_rgs_summary
from src.ons_births import build_csv as build_births_csv, load_harrogate_births

ADMISSIONS_OUT = "data/processed/rgs_admissions_clean.csv"
BIRTHS_OUT = "data/processed/ons_births_harrogate.csv"
MERGED_OUT = "data/processed/rgs_with_births.csv"


def build_admissions_csv(output_path: str = ADMISSIONS_OUT) -> pd.DataFrame:
    df = build_rgs_summary()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Saved {len(df)} rows → {output_path}")
    return df


def build_merged(admissions: pd.DataFrame, births: pd.DataFrame,
                 output_path: str = MERGED_OUT) -> pd.DataFrame:
    """
    Merge admissions data with Harrogate birth counts for the corresponding
    cohort year.  Both DataFrames must have an 'entry_year' column.
    """
    merged = admissions.merge(
        births[["entry_year", "birth_year", "total_births"]],
        on="entry_year",
        how="left",
    )
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    merged.to_csv(output_path, index=False)
    print(f"Saved {len(merged)} rows → {output_path}")
    return merged


if __name__ == "__main__":
    print("=== Building RGS admissions CSV ===")
    admissions = build_admissions_csv()
    print(admissions[["year_key", "entry_year", "birth_cohort_year",
                       "applications", "allocated", "day_distance_miles",
                       "waiting_list"]].to_string(index=False))

    print("\n=== Building ONS births CSV ===")
    births = build_births_csv(BIRTHS_OUT)
    births = load_harrogate_births()

    print("\n=== Building merged CSV ===")
    merged = build_merged(admissions, births)
    print(merged[["year_key", "entry_year", "birth_year", "total_births",
                  "applications", "day_distance_miles"]].to_string(index=False))
