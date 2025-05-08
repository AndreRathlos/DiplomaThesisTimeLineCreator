#!/usr/bin/env python3
"""
Timeline-Renderer (mehr­jährig) – Box-Rahmen sitzen jetzt perfekt.
CSV-Format:
date,description,status
2024-02-23,Genehmigung der DA,done
…

• Status  done/erledigt/true/yes/x/1 ⇒ grüner Punkt; sonst rot
"""

from __future__ import annotations
import csv, sys, pathlib, datetime as dt, itertools
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D

# ───────── Config ────────────────────────────────────────────────────────────
BAR_HEIGHT  = 0.32
LANE_STEP   = 0.9
DOT_R       = 0.13
SHADOW_OFF  = 0.06
FIG_DPI     = 300
FONT_SIZE   = 11
MONTH_C     = [
    "#e9ff00","#f6c820","#e47600","#ff6000",
    "#e40000","#c40016","#ff9cc7","#c38cff",
    "#937ebf","#645aaf","#475cc9","#1e4ba6"
]
DONE_VALS   = {"done","erledigt","true","yes","x","1"}
# ─────────────────────────────────────────────────────────────────────────────


def load(path: pathlib.Path):
    with open(path, newline="", encoding="utf-8") as f:
        rdr = csv.DictReader(f)
        items = [
            {
                "date": dt.datetime.strptime(r["date"], "%Y-%m-%d").date(),
                "label": r["description"].strip(),
                "done" : str(r.get("status","")).lower() in DONE_VALS
            }
            for r in rdr
        ]
    return sorted(items, key=lambda x: x["date"])


def lanes(items):
    """Symmetrisches Lane-Layout (0,+1,-1,+2,-2,…) pro Jahr."""
    per_year={}
    for it in items:
        per_year.setdefault(it["date"].year, []).append(it)

    char_w = 0.14  # grobe Breite, wird später nicht mehr gebraucht
    for year, lst in per_year.items():
        lanes={}
        for it in lst:
            x = it["date"].month-1 + it["date"].day/31
            w = max(len(it["label"])*char_w, 1)
            l,r = x-w/2, x+w/2
            for k in itertools.chain([0], *( (n,-n) for n in range(1,20))):
                if all(r<l2 or l>r2 for l2,r2 in lanes.get(k,[])):
                    it["lane"]=k
                    lanes.setdefault(k,[]).append((l,r))
                    break


def render(data, out_png: pathlib.Path):
    years = sorted({d["date"].year for d in data})
    max_lane = max(abs(d["lane"]) for d in data)
    year_y   = {y:-idx*(max_lane+4)*LANE_STEP for idx,y in enumerate(years)}

    fig = plt.figure(figsize=(16, 6+3*(len(years)-1)), dpi=FIG_DPI)
    ax  = fig.gca(); ax.axis("off"); plt.rcParams["font.size"]=FONT_SIZE

    # Monats­balken
    for y in years:
        y0 = year_y[y]
        for m in range(12):
            ax.add_patch(Rectangle((m,y0),1,BAR_HEIGHT,color=MONTH_C[m],zorder=1))
            ax.text(m+0.5,y0+BAR_HEIGHT/2,dt.date(1900,m+1,1).strftime("%b").upper(),
                    ha="center",va="center",weight="bold",zorder=2)
        ax.text(12.5,y0+BAR_HEIGHT/2,f"’{str(y)[-2:]}",ha="left",va="center",
                weight="bold",size=16,zorder=2)

    # Meilensteine
    for it in data:
        y0   = year_y[it["date"].year]
        lane = it["lane"]
        above= lane>=0
        x    = it["date"].month-1 + it["date"].day/31

        # berechne vorläufige Text-Y-Pos
        y_txt = y0 + (BAR_HEIGHT+0.45) + lane*LANE_STEP if above \
                else y0 -0.45 + lane*LANE_STEP

        # Schatten-Textbox
        shadow = ax.text(
            x+SHADOW_OFF, y_txt-SHADOW_OFF, it["label"],
            ha="center",va="center",color="none",zorder=3,
            bbox=dict(boxstyle="round,pad=0.3",fc="black",ec="none",alpha=0.12)
        )
        # Haupt-Textbox (mit Rahmen)
        txt = ax.text(
            x, y_txt, it["label"], ha="center",va="center",zorder=5,
            bbox=dict(boxstyle="round,pad=0.3",fc="white",ec="black",lw=1)
        )

        # Exakte Box-Höhe ermitteln, um Linienlänge anzupassen
        bb = txt.get_window_extent(fig.canvas.get_renderer())
        h  = (ax.transData.inverted().transform(bb))[1,1] - \
             (ax.transData.inverted().transform(bb))[0,1]

        y_dot = y0 + (BAR_HEIGHT if above else 0) + (0.17 if above else -0.17)
        y_box_edge = y_txt - h/2 if above else y_txt + h/2

        # Linie
        ax.add_line(Line2D([x,x],[y_dot,y_box_edge],color="black",lw=1,zorder=4))

        # Punkt
        ax.add_patch(plt.Circle((x,y_dot),DOT_R,
                    color="#34c759" if it["done"] else "#e63946",zorder=4))

    ax.set_xlim(-0.5,13)
    ax.set_ylim(min(year_y.values())-3,3)
    plt.tight_layout()
    out_png.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_png,dpi=FIG_DPI,bbox_inches="tight")
    plt.close()


# ────────── Main ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv)!=3:
        sys.exit("Usage: generate_timeline.py <milestones.csv> <output.png>")
    csv_file, png_file = map(pathlib.Path, sys.argv[1:])
    items = load(csv_file)
    lanes(items)
    render(items, png_file)
