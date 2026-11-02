"""Does a probe's fee decide whether it lands at all? (exploratory, added 2026-11-02)

If cheap probes were dropped more often than dear ones, "dear came first" could partly
be "only dear ones were left to compare". This counts landed / sent per CU price for
series 1-4 and per probe for series 5. Offline, from the run files.

  python -m itb.landing            # data/LANDING.md
"""
import collections
import glob
import json
import os
import sys

from .figures import wilson
from .series5 import PAIRS, fisher_two_sided


def main(data_dir: str = "data"):
    by_fee = collections.defaultdict(lambda: [0, 0])
    for path in glob.glob(os.path.join(data_dir, "runs", "live_*.json")):
        for p in json.load(open(path))["probes"]:
            c = by_fee[p["cu_price"]]
            c[0] += p.get("landed_slot") is not None
            c[1] += 1
    out = ["# Landing rate against fee (exploratory, added 2026-11-02)", "",
           "## Series 1-4: landed / sent per CU price", "",
           "| CU price (micro-lamports) | landed / sent | share | 95% CI |", "|---|---|---|---|"]
    for fee in sorted(by_fee):
        k, n = by_fee[fee]
        lo, hi = wilson(k, n)
        out.append(f"| {fee:,} | {k} / {n} | {k / n:.2f} | {lo:.2f}-{hi:.2f} |")
    lo_fee, hi_fee = by_fee[min(by_fee)], by_fee[max(by_fee)]
    p = fisher_two_sided(lo_fee[0], lo_fee[1] - lo_fee[0], hi_fee[0], hi_fee[1] - hi_fee[0])
    out += ["", f"Lowest against highest price, Fisher's exact test: p = {p:.2f}.", ""]

    s5, one_only = collections.defaultdict(lambda: [0, 0]), 0
    for path in glob.glob(os.path.join(data_dir, "runs5", "live_*.json")):
        r = json.load(open(path))
        one_only += len({pr.get("landed_slot") is not None for pr in r["probes"]}) > 1
        for pr in r["probes"]:
            c = s5[(r["pair"], pr["idx"])]
            c[0] += pr.get("landed_slot") is not None
            c[1] += 1
    if s5:
        out += ["## Series 5: landed / sent per probe", "",
                "| pair | probe A (600 CU) | probe B (60,000 CU) |", "|---|---|---|"]
        for pair in PAIRS:
            a, b = s5[(pair, 0)], s5[(pair, 1)]
            out.append(f"| {pair} | {a[0]} / {a[1]} | {b[0]} / {b[1]} |")
        out += ["", f"Runs where exactly one of the two probes landed: {one_only}. Both landed or neither did."]
    text = "\n".join(out) + "\n"
    open(os.path.join(data_dir, "LANDING.md"), "w").write(text)
    print(text)


if __name__ == "__main__":
    main(*sys.argv[1:])
