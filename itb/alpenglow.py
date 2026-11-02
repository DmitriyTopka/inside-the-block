"""Show from the chain that every probe landed after the Alpenglow switch.

Under Tower BFT validators vote with on-chain transactions to the Vote program, so
every block carries them. Under Alpenglow votes leave the block. This module binary
searches getBlock for the last block that still holds a Vote program transaction,
then compares that slot with the earliest slot any of our probes landed in.

  python -m itb.alpenglow          # about 25 getBlock calls on an archive RPC, no key, no spend
"""
import glob
import json
import os
import sys
import time

from .rpc import Rpc

VOTE_PROGRAM = "Vote111111111111111111111111111111111111111"
RPC_URL = os.environ.get("VERIFY_RPC_URL", "https://api.mainnet-beta.solana.com")


def first_probe_slot(data_dir: str) -> int:
    slots = [p["landed_slot"] for path in glob.glob(os.path.join(data_dir, "runs*", "live_*.json"))
             for p in json.load(open(path))["probes"] if p.get("landed_slot") is not None]
    return min(slots)


def block_votes(rpc: Rpc, slot: int) -> tuple[int, bool] | None:
    """(produced slot, has vote txs) for the first produced block at or after slot."""
    for s in range(slot, slot + 50):
        try:
            b = rpc.call("getBlock", [s, {"transactionDetails": "accounts", "rewards": False,
                                          "maxSupportedTransactionVersion": 1, "commitment": "finalized"}])
        except RuntimeError as e:  # skipped slot
            if "skipped" in str(e) or "-32007" in str(e) or "-32009" in str(e):
                continue
            raise
        if b is None:
            continue
        keys = (k["pubkey"] if isinstance(k, dict) else k for t in b["transactions"] for k in t["transaction"]["accountKeys"])
        return s, any(k == VOTE_PROGRAM for k in keys)
    return None


def main(data_dir: str = "data"):
    rpc = Rpc(RPC_URL)
    first = first_probe_slot(data_dir)
    lo, hi = first - 1_000_000, first  # about 4.6 days before our first probe
    s_lo, v_lo = block_votes(rpc, lo)
    s_hi, v_hi = block_votes(rpc, hi)
    print(f"slot {s_lo}: votes in block = {v_lo}; slot {s_hi} (our first landed probe): votes in block = {v_hi}")
    if not v_lo or v_hi:
        raise SystemExit("no vote-to-no-vote switch between these slots; nothing to search")
    while hi - lo > 1:
        mid = (lo + hi) // 2
        s, v = block_votes(rpc, mid)
        if s >= hi:  # only skipped slots up to hi: treat as no-vote side
            hi = mid
        elif v:
            lo = s
        else:
            hi = s
    hi, _ = block_votes(rpc, lo + 1)  # hi may be a skipped slot; take the next produced block
    t = lambda slot: time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(rpc.call("getBlockTime", [slot])))
    print(f"last block with Vote program transactions: {lo} ({t(lo)})")
    print(f"next produced block, without them: {hi} ({t(hi)})")
    print(f"earliest slot any of our probes landed in: {first} ({t(first)}), {first - hi:,} slots later")


if __name__ == "__main__":
    main(*sys.argv[1:])
