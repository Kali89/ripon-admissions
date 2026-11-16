"""Map of RGS admission chance by postcode. Run after src.catchment_reach:
    python -m src.catchment_reach_map "<your postcode>"
Writes data/private/rgs_reach_map.png (gitignored - derived from NYC boundaries)."""
import sys
import pandas as pd, geopandas as gpd, numpy as np, matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
d=pd.read_csv("data/private/rgs_reach_postcodes.csv"); pl=pd.read_csv("data/private/rgs_reach_places.csv")
sec=gpd.read_file("/Users/matt/src/ny-school-catchments/data/raw/250207 Synergy areas Secondary update July 2025 region.shp").set_crs(27700,allow_override=True)
bands=[(0.95,1.01,"#0d366b","In RGS catchment (~100%)"),(0.75,0.95,"#256abf","75–92%"),(0.5,0.75,"#5598e7","50–67%"),(0.25,0.5,"#9ec5f4","25–42%"),(0,0.25,"#e3e1dc","under 25%")]
fig,ax=plt.subplots(figsize=(11,9),dpi=150)
sec.boundary.plot(ax=ax,color="#b9b6ae",lw=0.6)
for lo,hi,c,lab in bands[::-1]:
    x=d[(d.P_all>=lo)&(d.P_all<hi)]; ax.scatter(x.east1m,x.north1m,s=5,c=c,lw=0)
sec[sec.Schoolname.str.startswith("Ripon Grammar")].boundary.plot(ax=ax,color="#0d366b",lw=1.6)
ax.plot(430209,471578,marker="s",ms=8,color="#111",ls="")
ax.annotate("Ripon Grammar",(430209,471578),xytext=(6,6),textcoords="offset points",fontsize=9,weight="bold")
HOME=sys.argv[1]  # your postcode; not stored in the repo
home=d[d.pcds==HOME].iloc[0]; ax.plot(home.east1m,home.north1m,marker="*",ms=14,color="#c0392b",ls="")
ax.annotate(f"You — {home.P_all:.0%}",(home.east1m,home.north1m),xytext=(6,-12),textcoords="offset points",fontsize=9,weight="bold",color="#c0392b")
lab=["Boroughbridge","Langthorpe","Kirby Hill","Roecliffe","Aldborough","Minskip","Staveley","Skelton","Bishop Monkton","Burton Leonard","Marton le Moor","Dishforth","Copgrove","Knaresborough","Marton-cum-Grafton","Arkendale","Ferrensby","Kirkby Malzeard","Masham","Pateley Bridge","Topcliffe","Helperby"]
for _,r in pl[pl.name.isin(lab)].drop_duplicates("name").iterrows():
    ax.annotate(f"{r['name']} {r.P_all:.0%}",(r.e,r.n),fontsize=7.5,color="#222",xytext=(3,3),textcoords="offset points")
ax.set_xlim(411000,452000); ax.set_ylim(455000,482000); ax.set_aspect("equal"); ax.set_axis_off()
for s in ax.spines.values(): s.set_visible(False)
ax.legend(handles=[Patch(color=c,label=l) for *_,c,l in bands]+[Line2D([],[],color="#0d366b",lw=1.6,label="RGS catchment boundary (NYC, Jul 2025)")],
          loc="lower left",fontsize=8,frameon=False,title="Chance of a day place, given a pass\n(share of 2014–2025 years; road+footpath distance)",title_fontsize=8.5)
fig.suptitle("How far from Ripon Grammar can you live?",x=0.02,ha="left",fontsize=13,weight="bold")
ax.text(0,1.0,"Each dot is a residential postcode. Out-of-catchment odds = share of 12 years in which the last distance offer reached that far.",transform=ax.transAxes,fontsize=8,color="#555",va="bottom")
fig.text(0.02,0.01,"Boundaries: NYC catchments (Jul 2025, FOI). Roads: © OpenStreetMap contributors. Postcodes: ONSPD May 2026.",fontsize=7,color="#777")
fig.tight_layout(); fig.savefig("data/private/rgs_reach_map.png")
