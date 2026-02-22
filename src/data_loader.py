"""
Load and normalise North Yorkshire secondary school admissions spreadsheets.

Each academic year's file uses slightly different column names.  This module
applies a consistent mapping, extracts numeric day-distance values from the
messy free-text distance field, and returns a tidy DataFrame ready for analysis.

Usage
-----
from src.data_loader import load_all_years, load_rgs

df_all = load_all_years("data/")
df_rgs  = load_rgs("data/")
"""

from __future__ import annotations

import glob
import os
import re

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Column-name normalisation
# ---------------------------------------------------------------------------

# Each entry maps a canonical name to a regex that matches the raw column.
# Order matters: the first match wins.
_COL_PATTERNS: list[tuple[str, str]] = [
    ("school_name",          r"school name|name and address"),
    ("type",                 r"type of establishment|^type$"),
    ("roll",                 r"number on roll|total no\. on roll"),
    ("pan",                  r"pan for academic|mal academic|^pan academic"),
    ("pan_sixth_form",       r"sixth form.*pan|sixth form.*mal|pan.*sixth form|mal.*sixth form"),
    ("applications",         r"total number of applications|total no.*applications"),
    ("allocated",            r"number of pup[ei]ls allocated|number of places allocated|"
                              r"total number of places allocated|total number of pupils allocated|"
                              r"number of puplis allocated"),
    ("criteria",             r"criteria of the last child"),
    ("distance_raw",         r"distance.*last child|last child.*distance|"
                              r"distance.*and.*criteria.*last child"),
    ("waiting_list",         r"waiting list"),
    ("appeals_heard",        r"appeals heard"),
    ("appeals_upheld",       r"appeals upheld|successful appeals"),
]


def _normalise_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Rename raw columns to canonical names, dropping unknowns and duplicates."""
    rename: dict[str, str] = {}
    seen_canonical: set[str] = set()

    for raw_col in df.columns:
        col_str = str(raw_col).strip()
        matched = False
        for canonical, pattern in _COL_PATTERNS:
            if re.search(pattern, col_str, re.IGNORECASE):
                if canonical not in seen_canonical:
                    rename[raw_col] = canonical
                    seen_canonical.add(canonical)
                matched = True
                break
        if not matched:
            # Drop columns we don't recognise (e.g. "Unnamed: 0", "Unnamed: 9")
            rename[raw_col] = f"_drop_{raw_col}"

    df = df.rename(columns=rename)
    drop_cols = [c for c in df.columns if c.startswith("_drop_")]
    return df.drop(columns=drop_cols)


# ---------------------------------------------------------------------------
# Distance extraction
# ---------------------------------------------------------------------------

def _extract_day_miles(raw: object) -> float | None:
    """
    Parse the messy 'distance of last child' field and return the day-place
    distance in miles as a float, or NaN if not parseable.

    Handles formats such as:
        6.62                                            (already numeric)
        "6.68 (Day) & 942 (Boarding)"
        "8.99 miles (Day) & 52.41 miles (Boarding)"
        "20.36 miles (Day) 120.86 miles (termly boarding place)"
        "Out of Catchment Distance - 9.864 Miles (Day)"
        "Contact the school"
        NaN
    """
    if raw is None or (isinstance(raw, float) and np.isnan(raw)):
        return np.nan
    if isinstance(raw, (int, float)):
        return float(raw)

    s = str(raw).strip()

    # Explicit day marker: grab the number that comes before "(Day)" or "Miles (Day)"
    day_match = re.search(r"([\d,]+\.?\d*)\s*miles?\s*\(day\)", s, re.IGNORECASE)
    if day_match:
        return float(day_match.group(1).replace(",", ""))

    # Older format: "6.68 (Day)" — number then space then "(Day)"
    day_match2 = re.search(r"([\d,]+\.?\d*)\s*\(day\)", s, re.IGNORECASE)
    if day_match2:
        return float(day_match2.group(1).replace(",", ""))

    # Fallback: just the first bare number (used in 2014-15 and 2015-16 where
    # the field is already clean and numeric-as-string)
    bare = re.match(r"^\s*([\d]+\.[\d]+)\s*$", s)
    if bare:
        return float(bare.group(1))

    return np.nan


# ---------------------------------------------------------------------------
# Year parsing
# ---------------------------------------------------------------------------

def _entry_year_from_key(key: str) -> int:
    """
    Given a key like '2016-17' return the September entry year (2016).
    For '2025-26' → 2025.
    """
    parts = key.split("-")
    return int(parts[0])


def _birth_year_from_entry(entry_year: int) -> int:
    """
    Children entering Year 7 in September of `entry_year` were (mostly) born
    in the academic year ending in entry_year - 11, i.e. calendar year
    entry_year - 12 (born Sep–Dec) or entry_year - 11 (born Jan–Aug).
    We use entry_year - 11 as the approximate birth cohort year.
    """
    return entry_year - 11


# ---------------------------------------------------------------------------
# Main loaders
# ---------------------------------------------------------------------------

def _load_one(filepath: str, year_key: str) -> pd.DataFrame:
    """Load and normalise a single year's spreadsheet."""
    df = pd.read_excel(filepath)
    df = _normalise_columns(df)

    # Remove fully empty rows and footer/note rows
    if "school_name" in df.columns:
        df = df[df["school_name"].notna()].copy()

    df["year_key"] = year_key
    df["entry_year"] = _entry_year_from_key(year_key)
    df["birth_cohort_year"] = _birth_year_from_entry(_entry_year_from_key(year_key))

    # Parse day distance
    if "distance_raw" in df.columns:
        df["day_distance_miles"] = df["distance_raw"].apply(_extract_day_miles)
    else:
        df["day_distance_miles"] = np.nan

    # Normalise numeric columns — extract leading integer from strings like
    # "117 inc 14 boarding places" before coercing to numeric.
    def _to_numeric(val: object) -> float:
        if isinstance(val, (int, float)):
            return float(val)
        m = re.match(r"\s*(\d+)", str(val))
        return float(m.group(1)) if m else float("nan")

    for col in ("roll", "applications", "allocated", "appeals_heard", "appeals_upheld", "waiting_list"):
        if col in df.columns:
            df[col] = df[col].apply(_to_numeric)

    # Strip school name
    if "school_name" in df.columns:
        df["school_name"] = df["school_name"].astype(str).str.strip()

    return df


def load_all_years(data_dir: str = "data/") -> pd.DataFrame:
    """
    Load every admissions spreadsheet found in `data_dir`, normalise columns,
    and return a single concatenated DataFrame.
    """
    pattern = os.path.join(data_dir, "*secondary*stats*.xlsx")
    files = glob.glob(pattern)
    # Also catch the 2021-22 file whose name differs slightly
    files += glob.glob(os.path.join(data_dir, "*secondary*data*.xlsx"))
    files += glob.glob(os.path.join(data_dir, "*secondary*statistics*.xlsx"))
    files = sorted(set(files))

    dfs = []
    for fp in files:
        basename = os.path.basename(fp)
        # Extract year key: first two hyphen-separated tokens, e.g. "2016-17"
        m = re.match(r"(\d{4}-\d{2,4})", basename)
        year_key = m.group(1) if m else basename
        dfs.append(_load_one(fp, year_key))

    combined = pd.concat(dfs, ignore_index=True)
    # Drop true duplicates that arise if glob patterns overlap
    combined = combined.drop_duplicates()
    return combined


def load_rgs(data_dir: str = "data/") -> pd.DataFrame:
    """
    Load all years and filter to Ripon Grammar School rows only.
    Returns a tidy DataFrame sorted by entry_year with key metrics.
    """
    df = load_all_years(data_dir)
    mask = df["school_name"].str.contains("Ripon Grammar", case=False, na=False)
    rgs = df[mask].copy()

    # Keep one row per year (in case of duplicates from glob overlap)
    rgs = rgs.sort_values("entry_year").drop_duplicates(subset=["entry_year"], keep="first")
    rgs = rgs.reset_index(drop=True)
    return rgs


def build_rgs_summary(data_dir: str = "data/") -> pd.DataFrame:
    """
    Return a clean, analysis-ready summary DataFrame for Ripon Grammar School
    with one row per entry year and only the most useful columns.
    """
    rgs = load_rgs(data_dir)

    cols = [
        "year_key", "entry_year", "birth_cohort_year",
        "roll", "applications", "allocated",
        "day_distance_miles",
        "waiting_list", "appeals_heard", "appeals_upheld",
        "distance_raw", "criteria",
    ]
    present = [c for c in cols if c in rgs.columns]
    return rgs[present].copy()
