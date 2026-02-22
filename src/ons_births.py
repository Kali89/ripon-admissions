"""
Fetch and process ONS live birth data for Harrogate district (E07000165).

Source: ONS adhoc release — "Numbers of live births by local authority and MSOA,
England and Wales: mid-year 1992 to mid-year 2021"
https://www.ons.gov.uk/peoplepopulationandcommunity/birthsdeathsandmarriages/livebirths/adhocs/1391numbersoflivebirthsbylocalauthorityandmsoaenglandandwalesmidyear1992tomidyear2021

The downloaded file is cached at data/processed/ons_births_la_msoa_1992_2021.xlsx.
Run `python -m src.ons_births` to regenerate the processed CSV.
"""

from __future__ import annotations

import os
import re
import urllib.request

import pandas as pd

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ONS_URL = (
    "https://www.ons.gov.uk/file?uri=/peoplepopulationandcommunity/"
    "birthsdeathsandmarriages/livebirths/adhocs/1391numbersoflivebirths"
    "bylocalauthorityandmsoaenglandandwalesmidyear1992tomidyear2021/"
    "livebirthsfinal.xlsx"
)
RAW_CACHE = "data/processed/ons_births_la_msoa_1992_2021.xlsx"
OUTPUT_CSV = "data/processed/ons_births_harrogate.csv"

# Harrogate district ONS code (pre-2023 reorganisation)
HARROGATE_CODE = "E07000165"


# ---------------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------------

def download_raw(dest: str = RAW_CACHE, force: bool = False) -> None:
    """Download the ONS Excel file if not already cached."""
    if os.path.exists(dest) and not force:
        print(f"Using cached file: {dest}")
        return
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    print(f"Downloading ONS births data → {dest}")
    urllib.request.urlretrieve(ONS_URL, dest)
    print("  Done.")


# ---------------------------------------------------------------------------
# Parse
# ---------------------------------------------------------------------------

def _parse_period(period: str) -> int:
    """
    Convert a mid-year period like '2001-2002' or '2001-02' to the start
    calendar year (2001).
    """
    m = re.match(r"(\d{4})", str(period).strip())
    return int(m.group(1)) if m else -1


def load_harrogate_births(raw_path: str = RAW_CACHE) -> pd.DataFrame:
    """
    Parse Table 1 from the ONS Excel file and return total annual births for
    Harrogate district with the entry year into Year 7 appended.

    Returns columns:
        period          str     e.g. "2001-2002"
        birth_year      int     start year of the mid-year period
        total_births    int     all-age total live births in Harrogate district
        entry_year      int     year the cohort enters secondary school (Year 7)
                                = birth_year + 11  (approximate)
    """
    xl = pd.ExcelFile(raw_path)
    # Find header row in Table 1
    df_raw = xl.parse("1", header=None)
    header_row = next(
        i for i, row in df_raw.iterrows() if "Period" in str(row.values)
    )
    df = xl.parse("1", header=header_row)

    # Filter to Harrogate district
    harro = df[df["Local authority code"] == HARROGATE_CODE].copy()

    # Sum across all age-of-mother columns to get total births
    age_cols = [c for c in df.columns if c not in ("Period", "Local authority code", "Local authority name")]
    harro["total_births"] = harro[age_cols].apply(pd.to_numeric, errors="coerce").sum(axis=1)

    harro["period"] = harro["Period"].astype(str).str.strip()
    harro["birth_year"] = harro["period"].apply(_parse_period)
    harro["entry_year"] = harro["birth_year"] + 11  # rough Year 7 entry year

    result = (
        harro[["period", "birth_year", "total_births", "entry_year"]]
        .sort_values("birth_year")
        .reset_index(drop=True)
    )
    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_csv(output_path: str = OUTPUT_CSV) -> pd.DataFrame:
    download_raw()
    df = load_harrogate_births()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Saved {len(df)} rows → {output_path}")
    return df


if __name__ == "__main__":
    df = build_csv()
    print(df.to_string(index=False))
