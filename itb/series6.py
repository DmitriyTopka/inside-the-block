"""Series 6 tables (PREREG_SERIES6.md): the series 5 pairs sent straight to the leader over QUIC.

Same rules as series 5 (itb/series5.py: verdict thresholds, leader-cluster bootstrap,
MIN_RUNS / MIN_LEADERS, the K1 + K2 key table). Two differences, both fixed in the
pre-registration: the class is the leader's gossip clientId recorded at run time, and a
run counts only if both probes landed in one block produced by the leader we connected to.

  python -m itb.series6            # writes data/SERIES6.md and data/series6_summary.json
"""
import collections
import glob
import json
import os

from .series5 import KEY, PAIRS, PREDICT, fmt_ci, verdict

CLASS_OF = {"JitoLabs": "JitoLabs", "AgaveBam": "AgaveBam", "Firedancer": "Firedancer",
            "FireBAM": "Firedancer", "HarmonicAgave": "HarmonicAgave"}
CLASSES = ["AgaveBam", "JitoLabs", "Firedancer", "HarmonicAgave"]
S5_NAME = {"AgaveBam": "agave-bam", "JitoLabs": "agave-jito (Jito Labs builds)", "Firedancer": "firedancer",
           "HarmonicAgave": "agave-jito (Harmonic builds)"}


def observation(run: dict) -> tuple[str, dict | None]:
    """('counted', obs) or (reason, None)."""
    if run.get("mode") != "live" or len(run.get("probes") or []) != 2:
        return "not live", None
    a, b = sorted(run["probes"], key=lambda p: p["idx"])
    if (run.get("tpu") or {}).get("error"):
        return "connection failed", None
    if a.get("landed_slot") is None or b.get("landed_slot") is None:
        return "a probe did not land", None
    if a["landed_slot"] != b["landed_slot"]:
        return "different blocks", None
    if a.get("landed_leader") != run.get("leader"):
        return "landed with another leader", None
    cls = CLASS_OF.get(run.get("leader_client_id") or "")
    if not cls:
        return "unknown client", None
    return "counted", {"pair": run["pair"], "leader": run["leader"], "class": cls,
                       "a_first": a["block_index"] < b["block_index"],
                       "a_sent_first": a["send_rank"] < b["send_rank"],
                       "gap": abs(a["block_index"] - b["block_index"]),
                       "rel_pos": min(a["block_index"], b["block_index"]) / max(1, a.get("block_size") or 1)}


def summarize(data_dir: str = "data") -> dict:
    runs = [json.load(open(p)) for p in sorted(glob.glob(os.path.join(data_dir, "runs6", "live_*.json")))]
    reasons = collections.Counter()
    obs = []
    for r in runs:
        why, o = observation(r)
        reasons[why] += 1
        if o:
            obs.append(o)
    cells, keys = {}, {}
    for c in CLASSES:
        for pair in PAIRS:
            cells[(c, pair)] = verdict([o for o in obs if o["class"] == c and o["pair"] == pair])
        v1, v2 = cells[(c, "K1")]["verdict"], cells[(c, "K2")]["verdict"]
        keys[c] = KEY[(v1, v2)] if v1 in ("A", "B") and v2 in ("A", "B") else f"none (K1 {v1}, K2 {v2})"
    per = collections.defaultdict(lambda: {"class": None, "runs": 0, "a_first": 0, "K1": [0, 0], "K2": [0, 0]})
    for o in obs:
        row = per[o["leader"]]
        row["class"] = o["class"]
        row["runs"] += 1
        row["a_first"] += o["a_first"]
        row[o["pair"]][0] += o["a_first"]
        row[o["pair"]][1] += 1
    gaps = sorted(o["gap"] for o in obs)
    pos = sorted(o["rel_pos"] for o in obs)
    return {"runs": len(runs), "reasons": dict(reasons), "counted": len(obs),
            "median_gap": gaps[len(gaps) // 2] if gaps else None,
            "adjacent": sum(g <= 2 for g in gaps),
            "median_rel_pos": round(pos[len(pos) // 2], 2) if pos else None,
            "cells": {f"{c} {p}": v for (c, p), v in cells.items()}, "keys": keys,
            "leaders": dict(sorted(per.items(), key=lambda kv: (kv[1]["class"], -kv[1]["runs"])))}


def md(s: dict) -> str:
    out = ["# Series 6: series 5 pairs sent straight to the leader over QUIC", "",
           f"Runs {s['runs']}, counted {s['counted']} (both probes in one block of the target leader).",
           "Not counted: " + ", ".join(f"{k} {v}" for k, v in sorted(s["reasons"].items()) if k != "counted") + ".",
           f"Counted pairs: median {s['median_gap']} transactions between the two probes, "
           f"{s['adjacent']} of {s['counted']} adjacent (2 or fewer apart); median relative position "
           f"of the first probe in its block {s['median_rel_pos']}.", "",
           "| class | pair | A first / runs | leaders | 99.375% CI (leader bootstrap) | verdict | predicted |",
           "|---|---|---|---|---|---|---|"]
    for key, v in s["cells"].items():
        c, pair = key.rsplit(" ", 1)
        out.append(f"| {c} | {pair} | {v['a_first']} / {v['n']} | {v['leaders']} | {fmt_ci(v['ci'])} | "
                   f"**{v['verdict']}** | A ({PREDICT[pair]['reward/cost']} under reward/cost) |")
    out += ["", "| class | key, direct arm (series 6) | series 5 class it compares with |", "|---|---|---|"]
    for c, k in s["keys"].items():
        out.append(f"| {c} | **{k}** | {S5_NAME[c]} |")
    out += ["", "## Per validator (every leader with a counted run)", "",
            "| validator | class | A first / runs | K1 | K2 |", "|---|---|---|---|---|"]
    for pk, r in s["leaders"].items():
        out.append(f"| `{pk[:8]}` | {r['class']} | {r['a_first']} / {r['runs']} | "
                   f"{r['K1'][0]} / {r['K1'][1]} | {r['K2'][0]} / {r['K2'][1]} |")
    return "\n".join(out) + "\n"


def rpc_arm(data_dir: str = "data") -> dict:
    """Series 5 counts by gossip clientId, read from data/CLIENTID.md (generated by itb.clientid).
    Firedancer pools the Firedancer and FireBAM rows, as series 6 does."""
    import re
    out = collections.defaultdict(lambda: [0, 0])
    path = os.path.join(data_dir, "CLIENTID.md")
    if not os.path.exists(path):
        return {}
    text = open(path).read().split("## Series 5", 1)[-1].split("\n## ", 1)[0]
    # main table only: its rows carry a share column right after the count
    for cid, pair, k, n in re.findall(r"^\| (\w+) \| (K[12]) \| (\d+) / (\d+) \| [01]\.\d\d \|", text, re.M):
        cls = CLASS_OF.get(cid)
        if cls:
            out[(cls, pair)][0] += int(k)
            out[(cls, pair)][1] += int(n)
    return dict(out)


def two_arm_svg(s: dict, rpc: dict) -> str:
    from .figures import svg, text
    W, H, L, R, T, B = 860, 400, 70, 170, 76, 70
    pw, ph = W - L - R, H - T - B
    y = lambda v: T + ph * (1 - v)
    body = [text(L, 24, "Same probe pairs, two delivery paths: how often probe A came first", size=15, weight="600"),
            text(L, 42, "hollow: series 5 through public RPC (by gossip clientId); filled: series 6 straight to the leader over QUIC",
                 size=12, color="#4b5563"),
            text(L, 58, "A is the small-limit probe; reward/cost picks A in both pairs", size=12, color="#4b5563")]
    for v in (0, 0.25, 0.5, 0.75, 1):
        body.append(f'<line x1="{L}" x2="{W - R}" y1="{y(v):.1f}" y2="{y(v):.1f}" stroke="{"#9ca3af" if v == 0.5 else "#e5e7eb"}" '
                    f'stroke-dasharray="{"4 3" if v in (0.5, 0.75) else "0"}"/>')
        body.append(text(L - 8, y(v) + 4, f"{v:.2f}", "end", 11, "#6b7280"))
    body.append(text(W - R + 8, y(0.5) + 4, "coin flip", "start", 11, "#6b7280"))
    body.append(text(W - R + 8, y(0.75) + 4, "threshold", "start", 11, "#6b7280"))
    colors = {"AgaveBam": "#2563eb", "JitoLabs": "#dc2626", "Firedancer": "#059669", "HarmonicAgave": "#7c3aed"}
    slot = pw / len(CLASSES)
    for i, c in enumerate(CLASSES):
        cx0 = L + slot * i
        body.append(text(cx0 + slot / 2, H - B + 34, c, "middle", 13, colors[c], "600"))
        for j, pair in enumerate(("K1", "K2")):
            x = cx0 + slot * (0.25 + 0.5 * j)
            body.append(text(x, H - B + 16, pair, "middle", 11, "#4b5563"))
            k, n = rpc.get((c, pair), (0, 0))
            if n:
                body.append(f'<circle cx="{x - 8:.1f}" cy="{y(k / n):.1f}" r="5" fill="#ffffff" stroke="{colors[c]}" stroke-width="2"/>')
            v = s["cells"].get(f"{c} {pair}")
            if v and v["n"]:
                body.append(f'<circle cx="{x + 8:.1f}" cy="{y(v["a_first"] / v["n"]):.1f}" r="5" fill="{colors[c]}"/>')
                body.append(text(x + 8, y(v["a_first"] / v["n"]) - 10, f'{v["a_first"]}/{v["n"]}', "middle", 10, "#374151"))
    return svg(W, H, body, "Series 5 vs series 6")


def main(data_dir: str = "data"):
    s = summarize(data_dir)
    json.dump(s, open(os.path.join(data_dir, "series6_summary.json"), "w"), indent=1)
    open(os.path.join(data_dir, "SERIES6.md"), "w").write(md(s))
    docs = os.path.join(os.path.dirname(os.path.abspath(data_dir)), "docs")
    if os.path.isdir(docs):
        open(os.path.join(docs, "series6.svg"), "w").write(two_arm_svg(s, rpc_arm(data_dir)))
    print(md(s))


if __name__ == "__main__":
    main()
