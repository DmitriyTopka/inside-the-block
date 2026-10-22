"""Turn analyzed runs into per-leader evidence. Offline: reads only data/.

For every two probes of one run that landed in the SAME block with different
fees we ask which one the leader put first:
  - send order and fee order disagree -> a discriminating pair: the block
    order tells "arrival" (sent first is earlier) from "fee" (dearer is earlier);
  - they agree -> a concordant pair: the block either follows both or neither;
  - burst runs send all probes at the same moment -> "dearer" or "cheaper" first.
Pairs from different blocks say nothing about in-block ordering and are skipped.

  python -m itb.report            # prints the tables, writes data/summary.json
"""
import glob
import itertools
import json
import math
import os
import sys
import time


def client_class(l: dict) -> str:
    """Version string plus the Jito flavour, e.g. '4.3.2 bam', '26.10.4 jito', '4.3.2 plain'."""
    flavour = "bam" if l.get("bam") else "jito" if l.get("jito") else "plain" if l.get("jito") is False else "?"
    return f"{l['version']} {flavour}"


def versions(data_dir: str) -> dict[str, str]:
    """identity -> client class, later surveys override earlier ones.

    Surveys taken before the Jito flags were recorded get them from the saved
    copy of Jito's validator list, data/jito_validators_*.json.
    """
    jito = {}
    for path in sorted(glob.glob(os.path.join(data_dir, "jito_validators_*.json"))):
        for v in json.load(open(path))["validators"]:
            jito[v["identity_account"]] = {"jito": v["running_jito"], "bam": v["running_bam"]}
    out = {}
    for path in sorted(glob.glob(os.path.join(data_dir, "survey_*.json"))):
        for l in json.load(open(path))["leaders"]:
            if l.get("version"):
                if "jito" not in l:
                    l = {**l, **jito.get(l["identity"], {"jito": False, "bam": False})}
                out[l["identity"]] = client_class(l)
    return out


def pairs(run: dict):
    landed = [p for p in run["probes"] if p.get("landed_slot") is not None]
    for a, b in itertools.combinations(landed, 2):
        if a["landed_slot"] != b["landed_slot"] or a["cu_price"] == b["cu_price"]:
            continue
        sent_first = a if a["send_rank"] < b["send_rank"] else b
        fee_first = a if a["cu_price"] > b["cu_price"] else b
        block_first = a if a["block_index"] < b["block_index"] else b
        if run["order"] == "burst":  # sent together: only the fee can explain a systematic order
            kind, winner = "burst", "dearer" if block_first is fee_first else "cheaper"
        elif sent_first is not fee_first:
            kind, winner = "discriminating", "arrival" if block_first is sent_first else "fee"
        else:
            kind, winner = "concordant", "both" if block_first is sent_first else "neither"
        yield {
            "slot": a["landed_slot"], "leader": a.get("landed_leader"),
            "kind": kind, "winner": winner,
            "fees": sorted([a["cu_price"], b["cu_price"]]),
            "gap_ms": round(abs(a["sent_at"] - b["sent_at"]) * 1000) if a.get("sent_at") and b.get("sent_at") else None,
            "index_gap": abs(a["block_index"] - b["block_index"]),
            "signatures": [a["signature"], b["signature"]],
            "run": run["_file"],
        }


def series4_obs(run: dict, ver: dict) -> dict | None:
    """One observation per series 4 run: both probes in one block, which came first."""
    landed = [p for p in run["probes"] if p.get("landed_slot") is not None]
    if len(landed) != 2 or landed[0]["landed_slot"] != landed[1]["landed_slot"]:
        return None
    dear = max(landed, key=lambda p: p["cu_price"])
    cheap = min(landed, key=lambda p: p["cu_price"])
    return {"run": run["_file"], "slot": dear["landed_slot"], "leader": dear.get("landed_leader"),
            "class": ver.get(dear.get("landed_leader"), "unknown"),
            "variant": "contended" if run.get("shared_account") else "independent",
            "gap_ms": run["gap_ms"], "dear_sent_first": dear["send_rank"] < cheap["send_rank"],
            "dear_first": dear["block_index"] < cheap["block_index"],
            "index_gap": abs(dear["block_index"] - cheap["block_index"])}


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    ph = k / n
    d = 1 + z * z / n
    c = (ph + z * z / (2 * n)) / d
    h = z * math.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / d
    return (round(c - h, 3), round(c + h, 3))


def holm(ps: list[float]) -> list[float]:
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    adj, run_max = [0.0] * len(ps), 0.0
    for rank, i in enumerate(order):
        run_max = max(run_max, min(1.0, (len(ps) - rank) * ps[i]))
        adj[i] = run_max
    return adj


def series4(runs: list[dict], ver: dict) -> dict:
    """Apply the decision rules of ANALYSIS_PLAN.md (written before series 4)."""
    s4 = [r for r in runs if r.get("gap_ms") is not None]
    obs = [o for r in s4 if (o := series4_obs(r, ver))]
    cells = {}
    for o in obs:
        c = cells.setdefault((o["class"], o["variant"], o["gap_ms"]), {"obs": [], "leaders": set()})
        c["obs"].append(o)
        c["leaders"].add(o["leader"])
    rows = []
    for (cls, var, gap), c in sorted(cells.items(), key=lambda kv: (kv[0][0], kv[0][1], kv[0][2])):
        n, k = len(c["obs"]), sum(o["dear_first"] for o in c["obs"])
        cheap_first = [o for o in c["obs"] if not o["dear_sent_first"]]
        arr = sum(not o["dear_first"] for o in cheap_first)  # cheap sent first and landed first
        rows.append({"class": cls, "variant": var, "gap_ms": gap, "n": n, "dear_first": k,
                     "share": round(k / n, 3) if n else None, "ci95": wilson(k, n), "p": sign_test(k, n),
                     "leaders": len(c["leaders"]), "n_cheap_sent_first": len(cheap_first),
                     "arrival_kept": arr, "p_arrival": sign_test(arr, len(cheap_first))})
    zero = [r for r in rows if r["gap_ms"] == 0]
    for r, a in zip(zero, holm([r["p"] for r in zero])):
        r["p_holm"] = round(a, 4)
    for r in rows:
        lo, hi = r["ci95"]
        if r["gap_ms"] == 0:
            if r["share"] is not None and r["share"] >= 0.75 and r["p_holm"] < 0.05:
                r["verdict"] = "fee"
            elif r["n"] >= 10 and lo <= 0.5 <= hi and hi < 0.75:
                r["verdict"] = "no fee rule"
            else:
                r["verdict"] = f"undetermined (n={r['n']})"
        else:
            m = r["n_cheap_sent_first"]
            if m and r["arrival_kept"] / m >= 0.75 and r["p_arrival"] < 0.05:
                r["verdict"] = "arrival"
            else:
                r["verdict"] = f"undetermined (n={m})"
    return {"runs": len(s4), "observations": len(obs), "cells": rows, "obs": obs}


def series4_md(s4: dict) -> str:
    lines = [f"Series 4 runs {s4['runs']}, counted (both probes in one block) {s4['observations']}.", "",
             "| class | variant | gap ms | n | dear first | share (95% CI) | p | p Holm | leaders | "
             "cheap sent first: kept order / n | verdict |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in s4["cells"]:
        lines.append(f"| {r['class']} | {r['variant']} | {r['gap_ms']:g} | {r['n']} | {r['dear_first']} | "
                     f"{r['share']} ({r['ci95'][0]}-{r['ci95'][1]}) | {round(r['p'], 4)} | {r.get('p_holm', '')} | "
                     f"{r['leaders']} | {r['arrival_kept']} / {r['n_cheap_sent_first']} | {r['verdict']} |")
    return "\n".join(lines)


def sign_test(k: int, n: int) -> float:
    """Two-sided exact binomial p-value for k of n under p=0.5."""
    if n == 0:
        return 1.0
    tail = sum(math.comb(n, i) for i in range(0, min(k, n - k) + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def summarize(data_dir: str = "data") -> dict:
    ver = versions(data_dir)
    runs = []
    for path in sorted(glob.glob(os.path.join(data_dir, "runs", "live_*.json"))):
        run = json.load(open(path))
        run["_file"] = os.path.relpath(path, data_dir)
        runs.append(run)
    all_pairs = [p for r in runs if r.get("gap_ms") is None for p in pairs(r)]  # series 1-3
    for p in all_pairs:
        p["version"] = ver.get(p["leader"], "unknown")
    by_leader = {}
    for p in all_pairs:
        row = by_leader.setdefault(p["leader"], {"leader": p["leader"], "version": p["version"], "blocks": set(),
                                                 "arrival": 0, "fee": 0, "both": 0, "neither": 0,
                                                 "dearer": 0, "cheaper": 0})
        row["blocks"].add(p["slot"])
        row[p["winner"]] += 1
    # Pairs from one block share that block's conditions, so they are not independent.
    # The block-level vote: each (run, block) leans one way by majority of its pairs; ties drop out.
    votes = {}
    for p in all_pairs:
        v = votes.setdefault((p["run"], p["slot"]), {"leader": p["leader"], "seq": 0, "burst": 0})
        v["seq"] += {"arrival": 1, "fee": -1}.get(p["winner"], 0)
        v["burst"] += {"dearer": 1, "cheaper": -1}.get(p["winner"], 0)
    for v in votes.values():
        r = by_leader[v["leader"]]
        for key, val, pos, neg in (("seq", v["seq"], "blk_arrival", "blk_fee"), ("burst", v["burst"], "blk_dearer", "blk_cheaper")):
            r.setdefault(pos, 0); r.setdefault(neg, 0)
            if val > 0:
                r[pos] += 1
            elif val < 0:
                r[neg] += 1
    rows = []
    for r in by_leader.values():
        r["blocks"] = len(r["blocks"])
        rows.append(r)
    rows.sort(key=lambda r: (r["version"], r["leader"]))
    by_version = {}
    for r in rows:
        v = by_version.setdefault(r["version"], {"version": r["version"], "leaders": 0, "blocks": 0,
                                                 "arrival": 0, "fee": 0, "both": 0, "neither": 0,
                                                 "dearer": 0, "cheaper": 0, "blk_arrival": 0, "blk_fee": 0,
                                                 "blk_dearer": 0, "blk_cheaper": 0})
        v["leaders"] += 1
        for k in ("blocks", "arrival", "fee", "both", "neither", "dearer", "cheaper",
                  "blk_arrival", "blk_fee", "blk_dearer", "blk_cheaper"):
            v[k] += r[k]
    for v in list(by_version.values()) + rows:
        v["p_arrival_vs_fee"] = round(sign_test(v["arrival"], v["arrival"] + v["fee"]), 4)
        v["p_burst"] = round(sign_test(v["dearer"], v["dearer"] + v["cheaper"]), 4)
        v["p_blk_seq"] = round(sign_test(v["blk_arrival"], v["blk_arrival"] + v["blk_fee"]), 4)
        v["p_blk_burst"] = round(sign_test(v["blk_dearer"], v["blk_dearer"] + v["blk_cheaper"]), 4)
    run_rows = [{
        "file": r["_file"], "utc": time.strftime("%Y-%m-%d %H:%M", time.gmtime(r["taken_at_unix"])),
        "target_slot": r["target_slot"], "target_leader": r["leader"], "target_class": ver.get(r["leader"], "unknown"),
        "order": r["order"], "fees": [p["cu_price"] for p in sorted(r["probes"], key=lambda p: p["send_rank"])],
        "landed": sum(1 for p in r["probes"] if p.get("landed_slot") is not None),
        "in_window": len(r.get("in_target_window", [])),
        "blocks": sorted({p["landed_slot"] for p in r["probes"] if p.get("landed_slot") is not None}),
    } for r in runs]
    landed = sum(1 for r in runs for p in r["probes"] if p.get("landed_slot") is not None)
    in_window = sum(len(r.get("in_target_window", [])) for r in runs)
    return {
        "runs": len(runs), "probes_sent": sum(len(r["probes"]) for r in runs),
        "probes_landed": landed, "probes_in_target_window": in_window,
        "first_run_unix": min(r["taken_at_unix"] for r in runs) if runs else None,
        "last_run_unix": max(r["taken_at_unix"] for r in runs) if runs else None,
        "by_version": sorted(by_version.values(), key=lambda v: -v["leaders"]),
        "by_leader": rows, "runs_list": run_rows, "pairs": all_pairs,
        "series4": series4(runs, ver),
    }


def block_table(rows: list[dict], key: str) -> str:
    lines = [f"| {key} | sequential blocks: arrival / fee | p | burst blocks: dearer / cheaper | p |",
             "|---|---|---|---|---|"]
    for r in rows:
        name = r[key] if key == "version" else f"`{r['leader'][:8]}` ({r['version']})"
        lines.append(f"| {name} | {r['blk_arrival']} / {r['blk_fee']} | {r['p_blk_seq']} | "
                     f"{r['blk_dearer']} / {r['blk_cheaper']} | {r['p_blk_burst']} |")
    return "\n".join(lines)


def table(rows: list[dict], key: str) -> str:
    head = (f"| {key} | blocks | sequential: arrival won | sequential: fee won | p | "
            f"concordant: followed / broke | burst: dearer first | burst: cheaper first | p |")
    lines = [head, "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        name = r[key] if key == "version" else f"`{r['leader'][:8]}` ({r['version']})"
        lines.append(f"| {name} | {r['blocks']} | {r['arrival']} | {r['fee']} | {r['p_arrival_vs_fee']} | "
                     f"{r['both']} / {r['neither']} | {r['dearer']} | {r['cheaper']} | {r['p_burst']} |")
    return "\n".join(lines)


def results_md(s: dict) -> str:
    out = ["# Results (generated by `python -m itb.report`, do not edit by hand)", "",
           f"Runs {s['runs']}, probes sent {s['probes_sent']}, landed {s['probes_landed']}, "
           f"landed inside the targeted 4-slot window {s['probes_in_target_window']}.", "",
           "Pairs are counted per block: two of our probes from one run that landed in the same block.", "",
           "## By client class", "", table(s["by_version"], "version"), "",
           "## By client class, one vote per block", "",
           "Each block where a run had two or more probes votes once, by the majority of its pairs; ties drop out. "
           "This is the test to trust: pairs from one block are not independent.", "",
           block_table(s["by_version"], "version"), "",
           "## By leader (the validator that actually produced the block)", "", table(s["by_leader"], "leader"), "",
           block_table(s["by_leader"], "leader"), "",
           "## Series 4: gap and contention (decision rules fixed in ANALYSIS_PLAN.md before the series)", "",
           series4_md(s["series4"]), "",
           "## Every run (UTC time of the run, all after the Alpenglow activation on 2026-10-21)", "",
           "| UTC | file | target leader | class | order | fees by send order (micro-lamports/CU) | landed | in window | blocks |",
           "|---|---|---|---|---|---|---|---|---|"]
    for r in s["runs_list"]:
        out.append(f"| {r['utc']} | `{r['file']}` | `{r['target_leader'][:8]}` | {r['target_class']} | {r['order']} | "
                   f"{', '.join(map(str, r['fees']))} | {r['landed']}/{len(r['fees'])} | {r['in_window']} | "
                   f"{' '.join(map(str, r['blocks']))} |")
    return "\n".join(out) + "\n"


def main(data_dir: str = "data"):
    s = summarize(data_dir)
    json.dump(s, open(os.path.join(data_dir, "summary.json"), "w"), indent=1)
    open(os.path.join(data_dir, "RESULTS.md"), "w").write(results_md(s))
    print(f"runs {s['runs']}, probes sent {s['probes_sent']}, landed {s['probes_landed']}, "
          f"in target window {s['probes_in_target_window']}")
    print(table(s["by_version"], "version"))
    print()
    print(block_table(s["by_version"], "version"))
    print()
    print(table(s["by_leader"], "leader"))
    print("wrote", os.path.join(data_dir, "RESULTS.md"))


if __name__ == "__main__":
    main(*sys.argv[1:])
