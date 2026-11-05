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
    gaps = sorted(o["gap"] for o in obs)
    pos = sorted(o["rel_pos"] for o in obs)
    return {"runs": len(runs), "reasons": dict(reasons), "counted": len(obs),
            "median_gap": gaps[len(gaps) // 2] if gaps else None,
            "adjacent": sum(g <= 2 for g in gaps),
            "median_rel_pos": round(pos[len(pos) // 2], 2) if pos else None,
            "cells": {f"{c} {p}": v for (c, p), v in cells.items()}, "keys": keys}


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
    return "\n".join(out) + "\n"


def main(data_dir: str = "data"):
    s = summarize(data_dir)
    json.dump(s, open(os.path.join(data_dir, "series6_summary.json"), "w"), indent=1)
    open(os.path.join(data_dir, "SERIES6.md"), "w").write(md(s))
    print(md(s))


if __name__ == "__main__":
    main()
