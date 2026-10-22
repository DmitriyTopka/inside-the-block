"""Find where each probe landed: slot, leader, and index inside the block.

Reads a run file written by itb.cli, asks the cluster which slot each signature
landed in, pulls those blocks (signatures only, in block order) and writes the
positions next to the run. Works for any run, live or replayed from raw data.
"""
import json
import sys

from .rpc import Rpc


def landed_slots(rpc: Rpc, sigs: list[str]) -> dict[str, int | None]:
    out = {}
    for i in range(0, len(sigs), 256):
        chunk = sigs[i:i + 256]
        res = rpc.call("getSignatureStatuses", [chunk, {"searchTransactionHistory": True}])["value"]
        for s, st in zip(chunk, res):
            out[s] = st["slot"] if st and st.get("err") is None else None
    return out


def block_order(rpc: Rpc, slot: int) -> list[str]:
    blk = rpc.call("getBlock", [slot, {"transactionDetails": "signatures", "rewards": False,
                                       "maxSupportedTransactionVersion": 1, "commitment": "confirmed"}])
    return blk["signatures"]


def analyze(run: dict, rpc: Rpc) -> dict:
    sigs = [p["signature"] for p in run["probes"]]
    slots = landed_slots(rpc, sigs)
    blocks = {s: block_order(rpc, s) for s in sorted({v for v in slots.values() if v is not None})}
    for p in run["probes"]:
        s = slots[p["signature"]]
        p["landed_slot"] = s
        if s is None:
            p["block_index"] = p["block_size"] = None
            continue
        order = blocks[s]
        p["block_index"] = order.index(p["signature"])
        p["block_size"] = len(order)
    ls = sorted(blocks)
    if ls:
        leaders = rpc.call("getSlotLeaders", [ls[0], ls[-1] - ls[0] + 1])
        for p in run["probes"]:
            if p["landed_slot"] is not None:
                p["landed_leader"] = leaders[p["landed_slot"] - ls[0]]
    landed = [p for p in run["probes"] if p["landed_slot"] is not None]
    landed.sort(key=lambda p: (p["landed_slot"], p["block_index"]))
    run["landed_order"] = [p["idx"] for p in landed]
    run["in_target_window"] = [p["idx"] for p in landed
                               if run["target_slot"] <= p["landed_slot"] < run["target_slot"] + 4]
    return run


def main(path: str):
    run = json.load(open(path))
    run = analyze(run, Rpc())
    json.dump(run, open(path, "w"), indent=1)
    print("target", run["target_slot"], "leader", run.get("leader_version"), "order", run["order"])
    for p in sorted(run["probes"], key=lambda p: p["send_rank"]):
        print(f"  send#{p['send_rank']} fee {p['cu_price']:>7} -> slot {p['landed_slot']} idx {p['block_index']}/{p['block_size']} leader {str(p.get('landed_leader'))[:8]}")
    print("landed order (by slot, index):", run["landed_order"], "| in target window:", run["in_target_window"])


if __name__ == "__main__":
    main(sys.argv[1])
