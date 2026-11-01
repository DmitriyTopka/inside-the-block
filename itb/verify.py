"""Re-check the raw data against the chain: for every landed probe, fetch its block
with getBlock and confirm the signature sits at the recorded slot and index.

  python -m itb.verify              # all live runs
  python -m itb.verify --sample 10  # 10 random runs (quick check)
  python -m itb.verify --runs runs5 # series 5
"""
import argparse
import glob
import json
import os
import random

from .rpc import Rpc

# Old blocks need an RPC that keeps history: publicnode drops blocks after about ten
# days (series 1-4 were gone by 2026-11-01), api.mainnet-beta serves them from its archive.
VERIFY_RPC_URL = os.environ.get("VERIFY_RPC_URL", "https://api.mainnet-beta.solana.com")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data")
    ap.add_argument("--runs", default="runs", help="run folder under --data (runs5 for series 5)")
    ap.add_argument("--sample", type=int, default=0, help="check only N random runs")
    a = ap.parse_args()
    paths = sorted(glob.glob(os.path.join(a.data, a.runs, "live_*.json")))
    if a.sample:
        paths = random.sample(paths, min(a.sample, len(paths)))
    rpc = Rpc(VERIFY_RPC_URL)
    blocks, ok, bad = {}, 0, []
    for path in paths:
        for p in json.load(open(path))["probes"]:
            slot = p.get("landed_slot")
            if slot is None:
                continue
            if slot not in blocks:
                blocks[slot] = rpc.call("getBlock", [slot, {"transactionDetails": "signatures", "rewards": False,
                                                            "maxSupportedTransactionVersion": 1,
                                                            "commitment": "finalized"}])["signatures"]
            sigs = blocks[slot]
            if p["signature"] in sigs and sigs.index(p["signature"]) == p["block_index"]:
                ok += 1
            else:
                bad.append((os.path.basename(path), p["signature"], slot, p["block_index"]))
    print(f"runs {len(paths)}, blocks fetched {len(blocks)}, probes confirmed {ok}, mismatches {len(bad)}")
    for b in bad:
        print("  MISMATCH", *b)
    raise SystemExit(1 if bad else 0)


if __name__ == "__main__":
    main()
