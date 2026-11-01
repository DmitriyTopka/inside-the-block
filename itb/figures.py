"""Figures and the leader-level re-analysis (exploratory, added 2026-11-01 after submission).

Series 1-4 verdicts rest on runs as observations. A class cell can lean on one or
two validators, so here the same series 4 data is re-counted with the leader as
the unit: a cluster bootstrap over leaders and a count of leaders that lean each
way. Nothing here changes a planned verdict. Plain SVG, no plotting library.

  python -m itb.figures            # data/LEADERS.md and docs/*.svg, offline
"""
import collections
import glob
import json
import math
import os
import random
import sys

from .report import series4, versions
from .series5 import class_of

CLASSES = ["agave-bam", "agave-jito", "firedancer", "agave-plain"]
COLORS = {"agave-bam": "#2563eb", "agave-jito": "#d97706", "firedancer": "#dc2626", "agave-plain": "#6b7280"}


def boot(groups: list[list[bool]], level: float = 0.95, n: int = 10_000, seed: int = 5) -> tuple[float, float] | None:
    if len(groups) < 2:
        return None
    rng = random.Random(seed)
    shares = []
    for _ in range(n):
        pick = [groups[rng.randrange(len(groups))] for _ in groups]
        shares.append(sum(map(sum, pick)) / sum(map(len, pick)))
    shares.sort()
    return shares[int((1 - level) / 2 * n)], shares[int((1 + level) / 2 * n) - 1]


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if not n:
        return 0.0, 1.0
    p, d = k / n, 1 + z * z / n
    c, h = (p + z * z / (2 * n)) / d, z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


def load_runs(data_dir: str) -> list[dict]:
    runs = []
    for path in sorted(glob.glob(os.path.join(data_dir, "runs", "live_*.json"))):
        r = json.load(open(path))
        r["_file"] = os.path.relpath(path, data_dir)
        runs.append(r)
    return runs


def leader_table(obs: list[dict]) -> list[dict]:
    """Series 4, gap 0: per class and variant, run-level and leader-level views side by side."""
    rows = []
    for c in CLASSES:
        for var in ("independent", "contended"):
            sub = [o for o in obs if o["s5class"] == c and o["variant"] == var and o["gap_ms"] == 0]
            by = collections.defaultdict(list)
            for o in sub:
                by[o["leader"]].append(o["dear_first"])
            k, n = sum(o["dear_first"] for o in sub), len(sub)
            lean_dear = sum(1 for g in by.values() if sum(g) * 2 > len(g))
            lean_cheap = sum(1 for g in by.values() if sum(g) * 2 < len(g))
            top = max((len(g) for g in by.values()), default=0)
            rows.append({"class": c, "variant": var, "n": n, "k": k, "leaders": len(by), "top_leader_runs": top,
                         "share": k / n if n else None, "wilson": wilson(k, n) if n else None,
                         "boot": boot(list(by.values())), "lean_dear": lean_dear, "lean_cheap": lean_cheap})
    return rows


def gap_curve(obs: list[dict]) -> dict:
    """P(dear landed first | cheap sent first) per class and gap, both variants pooled."""
    out = {}
    for c in CLASSES:
        for g in (0, 5, 20, 50, 150):
            sub = [o for o in obs if o["s5class"] == c and o["gap_ms"] == g and not o["dear_sent_first"]]
            k = sum(o["dear_first"] for o in sub)
            out[(c, g)] = (k, len(sub))
    return out


def fmt(ci):
    return f"{ci[0]:.2f}-{ci[1]:.2f}" if ci else "-"


def leaders_md(rows: list[dict], curve: dict) -> str:
    out = ["# Series 4 seen per leader (exploratory, added 2026-11-01; planned verdicts stay in REPORT.md)", "",
           "Series 4 counted one run as one observation. Runs from one validator share its configuration, so this table",
           "re-counts gap-0 runs with the leader as the unit. Classes here are the series 5 grouping: agave-bam, agave-jito,",
           "firedancer (26.x), agave-plain. \"Lean\" counts leaders whose own majority went one way (ties excluded).", "",
           "| class | variant | dear first / runs | run-level 95% CI | leaders | runs of busiest leader | leader-bootstrap 95% CI | leaders leaning dear / cheap |",
           "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        if not r["n"]:
            continue
        out.append(f"| {r['class']} | {r['variant']} | {r['k']} / {r['n']} | {fmt(r['wilson'])} | {r['leaders']} | "
                   f"{r['top_leader_runs']} | {fmt(r['boot'])} | {r['lean_dear']} / {r['lean_cheap']} |")
    out += ["", "## Who wins when the cheap probe leaves first (both variants pooled)", "",
            "| class | " + " | ".join(f"{g} ms" for g in (0, 5, 20, 50, 150)) + " |", "|---|---|---|---|---|---|"]
    for c in CLASSES:
        out.append(f"| {c} | " + " | ".join(f"{k}/{n}" if n else "-" for k, n in (curve[(c, g)] for g in (0, 5, 20, 50, 150))) + " |")
    out += ["", "Cells show runs where the dear probe still landed first / runs where the cheap one was sent first."]
    return "\n".join(out) + "\n"


# ---------- SVG ----------

def svg(w: int, h: int, body: list[str], title: str) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
            f'font-family="-apple-system,Segoe UI,Helvetica,Arial,sans-serif" font-size="13">'
            f'<title>{title}</title><rect width="{w}" height="{h}" fill="#ffffff"/>' + "".join(body) + "</svg>\n")


def text(x, y, s, anchor="start", size=13, color="#111827", weight="normal"):
    return f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" font-size="{size}" fill="{color}" font-weight="{weight}">{s}</text>'


def hero_svg(rows: list[dict]) -> str:
    """Dear-first share at a 0 ms gap, per class and variant, run-level CI as a bar, leader CI as a thin line."""
    W, H, L, R, T, B = 820, 380, 70, 130, 56, 70
    pw, ph = W - L - R, H - T - B
    y = lambda v: T + ph * (1 - v)
    body = [text(L, 24, "Series 4, probes sent together (0 ms): how often the dearer probe came first", size=15, weight="600"),
            text(L, 42, "thick bar: 95% CI over runs; thin line: 95% CI over leaders; n = runs / leaders", size=12, color="#4b5563")]
    for v in (0, 0.25, 0.5, 0.75, 1):
        body.append(f'<line x1="{L}" x2="{W - R}" y1="{y(v):.1f}" y2="{y(v):.1f}" stroke="{"#9ca3af" if v == 0.5 else "#e5e7eb"}" '
                    f'stroke-dasharray="{"4 3" if v in (0.5, 0.75) else "0"}"/>')
        body.append(text(L - 8, y(v) + 4, f"{v:.2f}", "end", 11, "#6b7280"))
    body.append(text(W - R + 8, y(0.5) + 4, "coin flip", "start", 11, "#6b7280"))
    body.append(text(W - R + 8, y(0.75) + 4, "fee threshold", "start", 11, "#6b7280"))
    shown = [r for r in rows if r["n"]]
    slot = pw / max(1, len(CLASSES))
    for i, c in enumerate(CLASSES):
        cx0 = L + slot * i
        body.append(text(cx0 + slot / 2, H - B + 34, c, "middle", 13, COLORS[c], "600"))
        for j, var in enumerate(("independent", "contended")):
            r = next((r for r in shown if r["class"] == c and r["variant"] == var), None)
            x = cx0 + slot * (0.33 + 0.34 * j)
            body.append(text(x, H - B + 16, "indep." if var == "independent" else "shared acct", "middle", 11, "#4b5563"))
            if not r:
                body.append(text(x, y(0.5) + 4, "no data", "middle", 11, "#9ca3af"))
                continue
            lo, hi = r["wilson"]
            body.append(f'<rect x="{x - 9:.1f}" y="{y(hi):.1f}" width="18" height="{y(lo) - y(hi):.1f}" fill="{COLORS[c]}" opacity="0.25"/>')
            if r["boot"]:
                blo, bhi = r["boot"]
                body.append(f'<line x1="{x + 14:.1f}" x2="{x + 14:.1f}" y1="{y(bhi):.1f}" y2="{y(blo):.1f}" stroke="{COLORS[c]}" stroke-width="2"/>')
            body.append(f'<circle cx="{x:.1f}" cy="{y(r["share"]):.1f}" r="5" fill="{COLORS[c]}"/>')
            body.append(text(x, y(hi) - 6, f'{r["k"]}/{r["n"]} · {r["leaders"]}L', "middle", 10, "#374151"))
    return svg(W, H, body, "Series 4: dearer probe first at a 0 ms gap")


def gap_svg(curve: dict) -> str:
    """Share of runs where the dear probe still landed first although the cheap one left first, by gap."""
    W, H, L, R, T, B = 760, 360, 70, 150, 56, 50
    pw, ph = W - L - R, H - T - B
    gaps = [0, 5, 20, 50, 150]
    x = lambda i: L + pw * i / (len(gaps) - 1)
    y = lambda v: T + ph * (1 - v)
    body = [text(L, 24, "Cheap probe sent first: how often the dearer one still came first (exploratory)", size=15, weight="600"),
            text(L, 42, "series 4, both variants; points with fewer than 5 runs are hollow", size=12, color="#4b5563")]
    for v in (0, 0.5, 1):
        body.append(f'<line x1="{L}" x2="{L + pw}" y1="{y(v):.1f}" y2="{y(v):.1f}" stroke="#e5e7eb"/>')
        body.append(text(L - 8, y(v) + 4, f"{v:.1f}", "end", 11, "#6b7280"))
    for i, g in enumerate(gaps):
        body.append(text(x(i), H - B + 20, f"{g} ms", "middle", 11, "#4b5563"))
    for c in CLASSES:
        pts = [(i, k / n, n) for i, g in enumerate(gaps) if (n := curve[(c, g)][1]) for k in [curve[(c, g)][0]]]
        if not pts:
            continue
        body.append('<polyline fill="none" stroke="{}" stroke-width="2" points="{}"/>'.format(
            COLORS[c], " ".join(f"{x(i):.1f},{y(v):.1f}" for i, v, _ in pts)))
        for i, v, n in pts:
            fill = COLORS[c] if n >= 5 else "#ffffff"
            body.append(f'<circle cx="{x(i):.1f}" cy="{y(v):.1f}" r="4.5" fill="{fill}" stroke="{COLORS[c]}" stroke-width="2"/>')
        k = CLASSES.index(c)
        body.append(f'<line x1="{L + pw + 14}" x2="{L + pw + 34}" y1="{T + 10 + 22 * k}" y2="{T + 10 + 22 * k}" stroke="{COLORS[c]}" stroke-width="3"/>')
        body.append(text(L + pw + 40, T + 14 + 22 * k, c, "start", 12, COLORS[c], "600"))
    return svg(W, H, body, "Series 4: fee against arrival by send gap")


def series5_svg(cells: dict) -> str:
    """Series 5: share of counted runs where probe A (limit 600) came first, per class and pair."""
    W, H, L, R, T, B = 840, 390, 70, 150, 70, 70
    pw, ph = W - L - R, H - T - B
    y = lambda v: T + ph * (1 - v)
    body = [text(L, 24, "Series 5: how often probe A (small CU limit) came first", size=15, weight="600"),
            text(L, 42, "bar: planned 99.375% leader-bootstrap interval; K1: cu_price picks A, total fee B; K2: both pick B", size=12, color="#4b5563")]
    for v in (0, 0.25, 0.5, 0.75, 1):
        body.append(f'<line x1="{L}" x2="{W - R}" y1="{y(v):.1f}" y2="{y(v):.1f}" stroke="{"#9ca3af" if v == 0.5 else "#e5e7eb"}" '
                    f'stroke-dasharray="{"4 3" if v in (0.5, 0.75) else "0"}"/>')
        body.append(text(L - 8, y(v) + 4, f"{v:.2f}", "end", 11, "#6b7280"))
    body.append(text(W - R + 8, y(0.5) + 4, "coin flip", "start", 11, "#6b7280"))
    body.append(text(W - R + 8, y(0.75) + 4, "threshold", "start", 11, "#6b7280"))
    slot = pw / len(CLASSES)
    for i, c in enumerate(CLASSES):
        cx0 = L + slot * i
        body.append(text(cx0 + slot / 2, H - B + 34, c, "middle", 13, COLORS[c], "600"))
        for j, pair in enumerate(("K1", "K2")):
            v = cells.get((c, pair))
            x = cx0 + slot * (0.25 + 0.5 * j)
            body.append(text(x, H - B + 16, pair, "middle", 11, "#4b5563"))
            if not v or not v["n"]:
                continue
            top = v["share"]
            if v["ci"]:
                lo, hi = v["ci"]
                top = hi
                body.append(f'<rect x="{x - 9:.1f}" y="{y(hi):.1f}" width="18" height="{y(lo) - y(hi):.1f}" fill="{COLORS[c]}" opacity="0.25"/>')
            body.append(f'<circle cx="{x:.1f}" cy="{y(v["share"]):.1f}" r="5" fill="{COLORS[c]}"/>')
            body.append(text(x, y(top) - 18, v["verdict"], "middle", 10, "#111827", "600"))
            body.append(text(x, y(top) - 6, f'{v["a_first"]}/{v["n"]}', "middle", 10, "#374151"))
    return svg(W, H, body, "Series 5: which fee key")


def main(data_dir: str = "data", docs_dir: str = "docs"):
    ver = versions(data_dir)
    s4 = series4(load_runs(data_dir), ver)
    for o in s4["obs"]:
        o["s5class"] = class_of(o["class"])
    rows, curve = leader_table(s4["obs"]), gap_curve(s4["obs"])
    open(os.path.join(data_dir, "LEADERS.md"), "w").write(leaders_md(rows, curve))
    os.makedirs(docs_dir, exist_ok=True)
    open(os.path.join(docs_dir, "series4_gap0.svg"), "w").write(hero_svg(rows))
    open(os.path.join(docs_dir, "series4_gap_curve.svg"), "w").write(gap_svg(curve))
    if os.path.isdir(os.path.join(data_dir, "runs5")):
        from .series5 import summarize
        open(os.path.join(docs_dir, "series5.svg"), "w").write(series5_svg(summarize(data_dir)["cells"]))
    print(leaders_md(rows, curve))


if __name__ == "__main__":
    main(*sys.argv[1:])
