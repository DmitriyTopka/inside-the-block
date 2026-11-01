"""Series 5 (PREREG_SERIES5.md): which fee key the scheduler sorts by.

Two probes per run, A and B, both crediting one shared account and sent together.
K1 and K2 are chosen so that cu_price, total fee and Agave's reward/cost pick
different winners; see the table in PREREG_SERIES5.md. This module holds the
pair definitions, the class mapping used to pick targets, and the planned
analysis (cluster bootstrap over leaders). Run files live in data/runs5/, apart
from series 1-4.

  python -m itb.series5            # tables into data/SERIES5.md, offline
"""
import collections
import glob
import json
import math
import os
import random
import sys

from .report import versions

# index 0 is probe A, index 1 is probe B (fees in micro-lamports per CU)
PAIRS = {
    "K1": {"fees": [10_000_000, 200_000], "limits": [600, 60_000]},
    "K2": {"fees": [1_000, 2_000], "limits": [600, 60_000]},
}
# which probe each key predicts first (PREREG table)
PREDICT = {"K1": {"cu_price": "A", "total fee": "B", "reward/cost": "A"},
           "K2": {"cu_price": "B", "total fee": "B", "reward/cost": "A"}}
KEY = {("A", "A"): "reward/cost", ("A", "B"): "cu_price", ("B", "B"): "total fee", ("B", "A"): "contradiction"}
CLASSES = ["agave-bam", "agave-jito", "firedancer", "agave-plain"]
MIN_RUNS, MIN_LEADERS = 40, 5
LEVEL = 1 - 0.05 / 8  # 99.375%: 95% with Bonferroni over 8 class x pair cells
RESAMPLES, SEED = 10_000, 5


def s5_class(l: dict) -> str | None:
    """Series 5 class from a survey entry (version + Jito flags)."""
    v = l.get("version") or ""
    if not v:
        return None
    if v.startswith("26."):
        return "firedancer"
    if not v[:1].isdigit() or int(v.split(".")[0]) < 2:  # e.g. 0.1.1: unknown client, not targeted
        return None
    return "agave-bam" if l.get("bam") else "agave-jito" if l.get("jito") else "agave-plain" if l.get("jito") is False else None


def class_of(cls_str: str | None) -> str | None:
    """Map report.client_class strings ('4.3.2 bam', '26.10.5 jito') to the series 5 class."""
    if not cls_str:
        return None
    v, _, flavour = cls_str.partition(" ")
    return s5_class({"version": v, "bam": flavour == "bam", "jito": flavour in ("bam", "jito") if flavour != "?" else None})


def leader_counts(runs_dir: str) -> collections.Counter:
    """Runs already aimed at each leader, for the per-leader cap."""
    c = collections.Counter()
    for path in glob.glob(os.path.join(runs_dir, "live_*.json")):
        try:
            c[json.load(open(path)).get("leader")] += 1
        except (ValueError, OSError):
            continue
    return c


def observation(run: dict, ver: dict) -> dict | None:
    """One counted run: both probes in one block. A is the probe with idx 0."""
    a, b = sorted(run["probes"], key=lambda p: p["idx"])
    if a.get("landed_slot") is None or a.get("landed_slot") != b.get("landed_slot"):
        return None
    leader = a.get("landed_leader")
    return {"pair": run["pair"], "leader": leader, "version": (ver.get(leader) or "? ?").split(" ")[0],
            "class": class_of(ver.get(leader)), "a_first": a["block_index"] < b["block_index"],
            "a_sent_first": a["send_rank"] < b["send_rank"],
            "endpoint": run["send_urls"][0] if len(run.get("send_urls") or []) == 1 else "both"}


def cluster_bootstrap(obs: list[dict], level: float = LEVEL) -> tuple[float, float]:
    """Interval for the share of A-first, resampling leaders with replacement."""
    by = collections.defaultdict(list)
    for o in obs:
        by[o["leader"]].append(o["a_first"])
    groups = list(by.values())
    rng = random.Random(SEED)
    shares = []
    for _ in range(RESAMPLES):
        pick = [groups[rng.randrange(len(groups))] for _ in groups]
        n = sum(len(g) for g in pick)
        shares.append(sum(sum(g) for g in pick) / n)
    shares.sort()
    lo_i = int(math.floor((1 - level) / 2 * RESAMPLES))
    hi_i = min(RESAMPLES - 1, int(math.ceil((1 + level) / 2 * RESAMPLES)) - 1)
    return shares[lo_i], shares[hi_i]


def verdict(obs: list[dict]) -> dict:
    n, leaders = len(obs), len({o["leader"] for o in obs})
    k = sum(o["a_first"] for o in obs)
    out = {"n": n, "a_first": k, "leaders": leaders, "share": k / n if n else None, "ci": None}
    if n < MIN_RUNS or leaders < MIN_LEADERS:
        out["verdict"] = "insufficient"
        return out
    lo, hi = cluster_bootstrap(obs)
    p = k / n
    out["ci"] = (lo, hi)
    if p >= 0.75 and lo > 0.5:
        out["verdict"] = "A"
    elif p <= 0.25 and hi < 0.5:
        out["verdict"] = "B"
    elif lo <= 0.5 <= hi and lo >= 0.25 and hi <= 0.75:
        out["verdict"] = "no rule"
    else:
        out["verdict"] = "undetermined"
    return out


def fisher_two_sided(a: int, b: int, c: int, d: int) -> float:
    """Fisher's exact test for the 2x2 table [[a, b], [c, d]]."""
    r1, c1, n = a + b, a + c, a + b + c + d

    def prob(x):
        return math.comb(c1, x) * math.comb(n - c1, r1 - x) / math.comb(n, r1)
    p0 = prob(a)
    return min(1.0, sum(prob(x) for x in range(max(0, r1 + c1 - n), min(r1, c1) + 1) if prob(x) <= p0 * (1 + 1e-9)))


def endpoint_check(obs: list[dict]) -> float | None:
    eps = sorted({o["endpoint"] for o in obs if o["endpoint"] != "both"})
    if len(eps) != 2:
        return None
    t = [[sum(1 for o in obs if o["endpoint"] == e and o["a_first"] == f) for f in (True, False)] for e in eps]
    return fisher_two_sided(t[0][0], t[0][1], t[1][0], t[1][1])


def summarize(data_dir: str = "data") -> dict:
    ver = versions(os.path.join(data_dir, "survey5"))  # series 5 surveys only: leaders upgraded since series 1-4
    runs = [json.load(open(p)) for p in sorted(glob.glob(os.path.join(data_dir, "runs5", "live_*.json")))]
    obs = [o for r in runs if "probes" in r and r.get("pair") and (o := observation(r, ver))]
    cells, keys = {}, {}
    for c in CLASSES:
        for pair in PAIRS:
            sub = [o for o in obs if o["class"] == c and o["pair"] == pair]
            cells[(c, pair)] = {**verdict(sub), "endpoint_p": endpoint_check(sub)}
        v1, v2 = cells[(c, "K1")]["verdict"], cells[(c, "K2")]["verdict"]
        keys[c] = KEY[(v1, v2)] if v1 in ("A", "B") and v2 in ("A", "B") else f"none (K1 {v1}, K2 {v2})"
    landed = sum(1 for r in runs for p in r.get("probes", []) if p.get("landed_slot") is not None)
    return {"runs": len(runs), "probes_landed": landed, "counted": len(obs), "cells": cells, "keys": keys, "obs": obs}


def fmt_ci(ci):
    return f"{ci[0]:.2f}-{ci[1]:.2f}" if ci else "-"


def md(s: dict) -> str:
    out = ["# Series 5 results (generated by `python -m itb.series5`, do not edit by hand)", "",
           f"Runs {s['runs']}, probes landed {s['probes_landed']}, counted runs (both probes in one block) {s['counted']}.",
           "Rules: PREREG_SERIES5.md. Interval: 99.375% cluster bootstrap over leaders.", "",
           "| class | pair | A first / counted | share | interval | leaders | verdict | endpoint Fisher p |",
           "|---|---|---|---|---|---|---|---|"]
    for (c, pair), v in s["cells"].items():
        share = f"{v['share']:.2f}" if v["share"] is not None else "-"
        ep = f"{v['endpoint_p']:.2f}" if v["endpoint_p"] is not None else "-"
        out.append(f"| {c} | {pair} | {v['a_first']} / {v['n']} | {share} | {fmt_ci(v['ci'])} | {v['leaders']} | {v['verdict']} | {ep} |")
    out += ["", "| class | key (K1 verdict + K2 verdict) |", "|---|---|"]
    out += [f"| {c} | {k} |" for c, k in s["keys"].items()]
    out += ["", "## Exploratory: by version string", "", "| class | version | pair | A first / counted |", "|---|---|---|---|"]
    by = collections.Counter((o["class"], o["version"], o["pair"], o["a_first"]) for o in s["obs"])
    for c, v, pair in sorted({(o["class"], o["version"], o["pair"]) for o in s["obs"]}, key=str):
        out.append(f"| {c} | {v} | {pair} | {by[(c, v, pair, True)]} / {by[(c, v, pair, True)] + by[(c, v, pair, False)]} |")
    return "\n".join(out) + "\n"


def main(data_dir: str = "data"):
    s = summarize(data_dir)
    path = os.path.join(data_dir, "SERIES5.md")
    open(path, "w").write(md(s))
    json.dump({"cells": {f"{c} {p}": v for (c, p), v in s["cells"].items()}, "keys": s["keys"],
               "runs": s["runs"], "counted": s["counted"]}, open(os.path.join(data_dir, "series5_summary.json"), "w"), indent=1)
    print(md(s))


if __name__ == "__main__":
    main(*sys.argv[1:])
