"""
How far from Ripon Grammar School can you live and still get a day place?

Combines three things:
  1. The RGS catchment polygon (NYC "Synergy areas Secondary update July 2025",
     from the sibling repo ~/src/ny-school-catchments, supplied under FOI/EIR).
     In-catchment qualifiers are admitted ahead of every out-of-catchment
     applicant, and every year 2013-2025 made out-of-catchment offers, so a
     qualifying in-catchment child has always got a place.
  2. Network distance from the school to every live residential postcode,
     computed on OpenStreetMap roads (+ footpaths). NYC measures "the nearest
     route ... using footpaths and roads" (FOI CN29389 Q3).
  3. The published "distance of last out-of-catchment day pupil" for 2014-2025,
     with 2019 set to 0: FOI CN29389 Q2b says NO out-of-catchment offers were
     made on distance that year (the published 6.68 mi is a copy of 2018's).

P(place | pass, out of catchment, distance d) = share of years whose boundary >= d.

The boundaries' onward licence is unconfirmed and this repo is public, so all
outputs go to data/private/ (gitignored). Do not commit them.

Run (needs osmium, geopandas, pyogrio, scipy, pyproj):
    python -m src.catchment_reach --pbf path/to/north-yorkshire-latest.osm.pbf --home "<your postcode>"
The PBF is https://download.geofabrik.de/europe/united-kingdom/england/north-yorkshire-latest.osm.pbf
"""

from __future__ import annotations

import argparse
import zipfile
from pathlib import Path

import geopandas as gpd
import numpy as np
import osmium
import pandas as pd
from pyproj import Transformer
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
from scipy.spatial import cKDTree

MI = 1609.344
RGS_EN = (430209.0, 471578.0)          # GIAS 2026, URN 121694, HG4 2DG
OUT = Path("data/private")

CATCH_SHP = Path("~/src/ny-school-catchments/data/raw/"
                 "250207 Synergy areas Secondary update July 2025 region.shp").expanduser()
RGS_CATCHMENT = "Ripon Grammar School & Outwood Academy Ripon"
ONSPD_ZIP = Path("~/src/asylum-site-local-impacts/data/raw/onspd/ONSPD_MAY_2026.zip").expanduser()
ONSPD_AREAS = ["HG", "YO", "LS", "DL", "BD", "TS"]

# Distance of last out-of-catchment day offer, NYC road miles, by entry year.
BOUNDARY_MI = {2014: 6.62, 2015: 7.567, 2016: 13.74, 2017: 12.48, 2018: 6.68,
               2019: 0.0,  # FOI CN29389: zero distance-criterion offers
               2020: 8.99, 2021: 9.588, 2022: 20.36, 2023: 11.07, 2024: 7.13,
               2025: 9.864}

DRIVE = {"motorway", "motorway_link", "trunk", "trunk_link", "primary", "primary_link",
         "secondary", "secondary_link", "tertiary", "tertiary_link", "unclassified",
         "residential", "living_street", "service", "road"}
FOOT = {"footway", "path", "pedestrian", "steps", "bridleway", "cycleway", "track"}
RADIUS_M = 42_000


class _OSM(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.ways, self.places = [], []

    def node(self, n):
        p = n.tags.get("place")
        if p in ("city", "town", "village", "hamlet") and n.tags.get("name"):
            self.places.append((n.tags["name"], p, n.location.lon, n.location.lat))

    def way(self, w):
        hw = w.tags.get("highway")
        if hw not in DRIVE and hw not in FOOT:
            return
        access = w.tags.get("access")
        drive_ok = hw in DRIVE and access not in ("private", "no")
        foot_ok = (not hw.startswith("motorway") and w.tags.get("foot") != "no"
                   and (access not in ("private", "no") or w.tags.get("foot") in ("yes", "designated")))
        if not (drive_ok or foot_ok):
            return
        try:
            pts = [(nd.ref, nd.lon, nd.lat) for nd in w.nodes]
        except osmium.InvalidLocationError:
            return
        self.ways.append((pts, drive_ok, foot_ok))


def network_distances(pbf: Path):
    """Shortest network distance (m) from RGS to every graph node, two profiles."""
    h = _OSM()
    h.apply_file(str(pbf), locations=True)
    to_bng = Transformer.from_crs(4326, 27700, always_xy=True)
    ids, xs, ys = {}, [], []

    def nid(ref, lon, lat):
        if ref not in ids:
            x, y = to_bng.transform(lon, lat)
            ids[ref] = len(xs); xs.append(x); ys.append(y)
        return ids[ref]

    edges = {"drive": ([], [], []), "all": ([], [], [])}
    for pts, dok, fok in h.ways:
        idx = [nid(*p) for p in pts]
        for a, b in zip(idx[:-1], idx[1:]):
            if np.hypot(xs[a] - RGS_EN[0], ys[a] - RGS_EN[1]) > RADIUS_M * 1.4:
                continue
            d = np.hypot(xs[a] - xs[b], ys[a] - ys[b])
            for k, ok in (("drive", dok), ("all", dok or fok)):
                if ok:
                    r, c, w = edges[k]
                    r.append(a); c.append(b); w.append(d)
    xy = np.c_[xs, ys]
    out = {}
    for k, (r, c, w) in edges.items():
        m = coo_matrix((w, (r, c)), shape=(len(xy), len(xy))).tocsr()
        used = np.unique(np.r_[r, c])
        _, j = cKDTree(xy[used]).query(RGS_EN)
        dist = dijkstra(m, indices=used[j], directed=False)[used]
        ok = np.isfinite(dist)
        out[k] = (cKDTree(xy[used][ok]), dist[ok])
    places = pd.DataFrame(h.places, columns=["name", "place", "lon", "lat"])
    places["e"], places["n"] = to_bng.transform(places.lon.values, places.lat.values)
    return out, places


def load_postcodes() -> pd.DataFrame:
    z = zipfile.ZipFile(ONSPD_ZIP)
    cols = ["pcds", "doterm", "usrtypind", "east1m", "north1m"]
    d = pd.concat(pd.read_csv(z.open(f"Data/multi_csv/ONSPD_MAY_2026_UK_{a}.csv"),
                              usecols=cols, low_memory=False) for a in ONSPD_AREAS)
    d = d[d.doterm.isna() & (d.usrtypind == 0)].dropna(subset=["east1m"])
    d = d[np.hypot(d.east1m - RGS_EN[0], d.north1m - RGS_EN[1]) < 40_000]
    return d.drop(columns=["doterm", "usrtypind"]).reset_index(drop=True)


def p_out_of_catchment(d_mi) -> np.ndarray:
    b = np.array(list(BOUNDARY_MI.values()))
    return (b[None, :] >= np.asarray(d_mi)[:, None]).mean(1)


def score(df: pd.DataFrame, e: str, n: str, nets, sec) -> pd.DataFrame:
    xy = df[[e, n]].values
    df["sl_mi"] = np.hypot(xy[:, 0] - RGS_EN[0], xy[:, 1] - RGS_EN[1]) / MI
    for k, (tree, dist) in nets.items():
        snap, j = tree.query(xy)
        df[f"{k}_mi"] = (dist[j] + snap) / MI
    pts = gpd.GeoDataFrame(geometry=gpd.points_from_xy(xy[:, 0], xy[:, 1]), crs=27700)
    j = gpd.sjoin(pts, sec[["Schoolname", "geometry"]], how="left", predicate="within")
    df["catchment"] = j[~j.index.duplicated()].Schoolname.str.strip().values
    df["in_rgs"] = df.catchment.eq(RGS_CATCHMENT)
    for k in nets:
        df[f"P_{k}"] = np.where(df.in_rgs, 1.0, p_out_of_catchment(df[f"{k}_mi"]))
    return df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pbf", type=Path, required=True)
    ap.add_argument("--home", required=True, help="your postcode, e.g. 'HG4 1AA' (kept out of the repo)")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)

    sec = gpd.read_file(CATCH_SHP).set_crs(27700, allow_override=True)
    sec["geometry"] = sec.geometry.force_2d().make_valid()
    nets, places = network_distances(args.pbf)

    pcs = score(load_postcodes(), "east1m", "north1m", nets, sec)
    places = score(places, "e", "n", nets, sec)
    home = pcs.loc[pcs.pcds == args.home, ["east1m", "north1m"]].values[0]
    for df, e, n in ((pcs, "east1m", "north1m"), (places, "e", "n")):
        df["from_home_mi"] = np.hypot(df[e] - home[0], df[n] - home[1]) / MI

    pcs.to_csv(OUT / "rgs_reach_postcodes.csv", index=False)
    places = places[places.drive_mi < 16].sort_values("from_home_mi")
    places.drop(columns=["lon", "lat"]).round(3).to_csv(OUT / "rgs_reach_places.csv", index=False)

    for thr in (0.5, 0.75, 0.95):
        ok = pcs[pcs.P_all >= thr]
        far, near = ok.loc[ok.sl_mi.idxmax()], ok.loc[ok.from_home_mi.idxmin()]
        print(f"P>={thr:.0%}: furthest {far.pcds} ({far.sl_mi:.1f} mi crow / {far.all_mi:.1f} road); "
              f"nearest home {near.pcds} ({near.from_home_mi:.1f} mi from {args.home})")
    print(places[["name", "catchment", "drive_mi", "all_mi", "from_home_mi", "P_all", "P_drive"]]
          .head(40).round(2).to_string())


if __name__ == "__main__":
    main()
