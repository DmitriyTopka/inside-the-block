"""Whole-block context for the blocks our probes landed in. Read-only, no keys.

For each block: every transaction's priority per cost unit, whether it pays a Jito tip, and how block
position relates to price. This is supplementary evidence: it tells which
leaders run a Jito block engine and whether the block as a whole looks
fee-sorted, but the ordering claims rest on our own probes (itb.report).

  python -m itb.blocks            # all landed slots in data/runs, cached in data/blocks/
"""
import glob
import json
import os
import sys

from .budget import BASE_FEE_LAMPORTS
from .rpc import Rpc
from .survey import JITO_TIP_ACCOUNTS

VOTE = "Vote111111111111111111111111111111111111111"


def parse_tx(entry: dict) -> dict:
    """Priority is measured the way the schedulers rank: priority lamports per cost unit.

    Since the v1 transaction format (seen on mainnet in our blocks) the price can sit
    in the message's transactionConfig instead of a ComputeBudget instruction, so we
    use what the ledger charged: fee minus the 5000-lamport base per signature,
    divided by the cost units the leader's cost model assigned (meta.costUnits).
    """
    msg = entry["transaction"]["message"]
    meta = entry.get("meta") or {}
    loaded = meta.get("loadedAddresses") or {}
    keys = msg["accountKeys"] + loaded.get("writable", []) + loaded.get("readonly", [])
    nsig = msg["header"]["numRequiredSignatures"]
    prio = max(0, (meta.get("fee") or 0) - BASE_FEE_LAMPORTS * nsig)
    cost = meta.get("costUnits")
    programs = {keys[ix["programIdIndex"]] for ix in msg["instructions"]}
    return {
        "sig": entry["transaction"]["signatures"][0],
        "version": entry.get("version"),
        "fee": meta.get("fee"), "cost_units": cost,
        "prio_per_cu": round(prio * 1e6 / cost) if cost else None,  # micro-lamports per cost unit
        "jito_tip": any(k in JITO_TIP_ACCOUNTS for k in keys),
        "vote": VOTE in programs,
        "failed": meta.get("err") is not None,
    }


def spearman(xs: list[float], ys: list[float]) -> float | None:
    n = len(xs)
    if n < 3:
        return None

    def ranks(v):
        order = sorted(range(n), key=lambda i: v[i])
        r = [0.0] * n
        i = 0
        while i < n:
            j = i
            while j + 1 < n and v[order[j + 1]] == v[order[i]]:
                j += 1
            for k in range(i, j + 1):
                r[order[k]] = (i + j) / 2
            i = j + 1
        return r

    rx, ry = ranks(xs), ranks(ys)
    mx, my = sum(rx) / n, sum(ry) / n
    cov = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    vx = sum((a - mx) ** 2 for a in rx) ** 0.5
    vy = sum((b - my) ** 2 for b in ry) ** 0.5
    return round(cov / (vx * vy), 3) if vx and vy else None


def block_stats(txs: list[dict]) -> dict:
    """Spearman(index, prio_per_cu) over non-vote transactions: negative = dearer earlier."""
    nv = [(i, t) for i, t in enumerate(txs) if not t["vote"] and t["prio_per_cu"] is not None]
    tips = [i for i, t in nv if t["jito_tip"]]
    return {
        "tx_count": len(txs), "non_vote": len(nv),
        "jito_tip_txs": len(tips),
        "jito_tip_positions": tips[:50],
        "share_zero_price": round(sum(1 for _, t in nv if t["prio_per_cu"] == 0) / len(nv), 3) if nv else None,
        "spearman_index_vs_price": spearman([i for i, _ in nv], [t["prio_per_cu"] for _, t in nv]),
    }


def fetch(rpc: Rpc, slot: int, cache_dir: str) -> list[dict]:
    path = os.path.join(cache_dir, f"{slot}.json")
    if os.path.exists(path):
        return json.load(open(path))
    blk = rpc.call("getBlock", [slot, {"encoding": "json", "transactionDetails": "full", "rewards": False,
                                       "maxSupportedTransactionVersion": 1, "commitment": "confirmed"}])
    txs = [parse_tx(e) for e in blk["transactions"]]
    os.makedirs(cache_dir, exist_ok=True)
    json.dump(txs, open(path, "w"))
    return txs


def main(data_dir: str = "data"):
    rpc = Rpc()
    leaders = {}
    for path in glob.glob(os.path.join(data_dir, "runs", "live_*.json")):
        for p in json.load(open(path))["probes"]:
            if p.get("landed_slot") is not None:
                leaders[p["landed_slot"]] = p.get("landed_leader")
    out = []
    for slot in sorted(leaders):
        txs = fetch(rpc, slot, os.path.join(data_dir, "blocks"))
        out.append({"slot": slot, "leader": leaders[slot], **block_stats(txs)})
        r = out[-1]
        print(slot, str(r["leader"])[:8], "txs", r["tx_count"], "jito tips", r["jito_tip_txs"],
              "rho(index, price)", r["spearman_index_vs_price"])
    json.dump(out, open(os.path.join(data_dir, "blocks_summary.json"), "w"), indent=1)


if __name__ == "__main__":
    main(*sys.argv[1:])
