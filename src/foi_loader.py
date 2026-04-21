"""
Load the CN29389 FOI response data into a clean DataFrame.

The FOI (ref CN29389) asked North Yorkshire Council for:
  Q1: Applications by catchment status (in / out), 2013–2026
  Q2: Offers on National Offer Day by catchment, and distance-criterion subset
  Q3: Distance measurement method (confirmed: road-routed, not straight-line)
  Q4: Explanation of the 2022-23 outlier (no explanation provided)

Data notes:
  - Q1 data is only available from entry year 2018 onwards; earlier years
    are recorded as "Information not held" in the FOI response.
  - Q2b "Less than 5" for 2017 and 2018 is stored as NaN.
  - All figures exclude SEN/LAC/PLAC/Staff applications (those are handled
    outside the normal over-subscription criteria).
  - Application totals include withdrawn applications and those who did not
    reach the qualifying cut-off mark.

Distance methodology (Q3):
  "All distance measurements are based on the nearest route recognised by our
  electronic mapping system from a child's home address to school. The
  measurement is made from a fixed point within the dwelling, as identified by
  Ordnance Survey, to the nearest school entrance using footpaths and roads."
  This has been used consistently throughout 2013–2026.
  IMPORTANT: This is road-routed distance, NOT straight-line (Haversine).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# Entry years covered in the FOI response
_YEARS = list(range(2013, 2026))

# ── Q1a: applications by catchment status ────────────────────────────────────
# "Information not held" for 2013–2017 (first five years)
_APPS_IN_CATCHMENT = [
    np.nan, np.nan, np.nan, np.nan, np.nan,   # 2013–2017
    118, 135, 117, 161, 113, 110, 108, 105,    # 2018–2025
]
_APPS_OUT_CATCHMENT = [
    np.nan, np.nan, np.nan, np.nan, np.nan,    # 2013–2017
    83, 81, 92, 135, 72, 126, 150, 123,        # 2018–2025
]

# ── Q1b: applications where RGS was listed as first preference ────────────────
_APPS_FIRST_PREF = [
    np.nan, np.nan, np.nan, np.nan, np.nan,    # 2013–2017
    165, 182, 161, 227, 143, 150, 164, 149,    # 2018–2025
]

# ── Q2a: offers on National Offer Day by catchment ───────────────────────────
_OFFERS_IN_CATCHMENT = [85, 85, 89, 92, 97, 84, 103, 87, 79, 84, 77, 79, 83]
_OFFERS_OUT_CATCHMENT = [22, 18, 22, 18, 9, 24, 8, 17, 23, 25, 24, 21, 25]

# ── Q2b: out-of-catchment offers under pure distance criterion ────────────────
# (excludes siblings and looked-after children)
# "Less than 5" for 2017 and 2018 → NaN
_OFFERS_DISTANCE_CRITERION = [
    10, 11, 9, 13,           # 2013–2016
    np.nan, np.nan,          # 2017–2018 ("Less than 5")
    0, 10, 10, 23, 17, 9, 15 # 2019–2025
]


def load_foi_catchment() -> pd.DataFrame:
    """
    Return a DataFrame with FOI catchment split data, one row per entry year.

    Columns
    -------
    entry_year              : int
    apps_in_catchment       : float  (NaN for 2013–2017, "not held")
    apps_out_catchment      : float  (NaN for 2013–2017, "not held")
    apps_first_pref         : float  (NaN for 2013–2017, "not held")
    offers_in_catchment     : int
    offers_out_catchment    : int
    offers_distance_crit    : float  (NaN for 2017–2018, "Less than 5")
    """
    return pd.DataFrame({
        "entry_year":            _YEARS,
        "apps_in_catchment":     _APPS_IN_CATCHMENT,
        "apps_out_catchment":    _APPS_OUT_CATCHMENT,
        "apps_first_pref":       _APPS_FIRST_PREF,
        "offers_in_catchment":   _OFFERS_IN_CATCHMENT,
        "offers_out_catchment":  _OFFERS_OUT_CATCHMENT,
        "offers_distance_crit":  _OFFERS_DISTANCE_CRITERION,
    })
