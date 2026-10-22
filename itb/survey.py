"""Map upcoming leader slots to the validator's client version.

Output: data/survey_<epoch>.json with, per leader, version, stake and the
leader slots still ahead in the current epoch.
"""
import collections
import json
import os
import sys
import time

import httpx

from .rpc import Rpc

# Jito's public validator list: running_jito (block engine) and running_bam
# (Block Assembly Marketplace, where an external node assembles the block).
JITO_VALIDATORS_URL = "https://kobe.mainnet.jito.network/api/v1/validators"

# Jito tip payment accounts (public, from Jito docs). Used by itb.blocks to
# mark tip-paying transactions. A tip inside a block does NOT prove the leader
# runs Jito: anyone can transfer to these accounts in a plain transaction, and
# on 22.10 every block we checked, Firedancer ones included, had such transfers.
JITO_TIP_ACCOUNTS = {
    "96gYZGLnJYVFmbjzopPSU6QiEV5fGqZNyN9nmNhvrZU5",
    "HFqU5x63VTqvQss8hp11i4wVV8bD44PvwucfZ2bU7gRe",
    "Cw8CFyM9FkoMi7K7Crf6HNQqf4uEMzpKw6QNghXLvLkY",
    "ADaUMid9yfUytqMBgopwjb2DTLSokTSzL1zt6iGPaS49",
    "DfXygSm4jCyNCybVYYK6DwvWqjKee8pbDmJGcLWNDXjh",
    "ADuUkR4vqLUMWXxW9gh6D6L8pMSawimctcNZ5pGwDcEt",
    "DttWaMuVvTiduZRnguLF7jNxTgiMBZ1hyAumKUiL2KRL",
    "3AVi9Tg9Uo68tJfuvoKvqKNWKkC5wPdSSdeBnizKZ6jT",
}


def main(out_dir="data"):
    rpc = Rpc()
    ei = rpc.call("getEpochInfo")
    first = ei["absoluteSlot"] - ei["slotIndex"]
    nodes = {n["pubkey"]: n for n in rpc.call("getClusterNodes")}
    votes = rpc.call("getVoteAccounts")["current"]
    stake = {v["nodePubkey"]: v["activatedStake"] for v in votes}
    sched = rpc.call("getLeaderSchedule", [None, {}]) or {}
    now = ei["absoluteSlot"]
    try:
        jito = {v["identity_account"]: v for v in httpx.get(JITO_VALIDATORS_URL, timeout=30).json()["validators"]}
    except Exception as e:  # the survey still works without it, the class is then "unknown"
        print("jito list unavailable:", e)
        jito = None
    leaders = []
    for pk, idx in sched.items():
        j = (jito or {}).get(pk, {})
        ahead = sorted(first + i for i in idx if first + i > now)
        leaders.append({
            "identity": pk,
            "version": (nodes.get(pk) or {}).get("version"),
            "feature_set": (nodes.get(pk) or {}).get("featureSet"),
            "tpu": (nodes.get(pk) or {}).get("tpuQuic") or (nodes.get(pk) or {}).get("tpu"),
            "stake_sol": round(stake.get(pk, 0) / 1e9),
            "jito": j.get("running_jito", False) if jito is not None else None,
            "bam": j.get("running_bam", False) if jito is not None else None,
            "bam_connection_rate": j.get("bam_connection_rate"),
            "slots_ahead": ahead,
        })
    by_ver = collections.Counter()
    for l in leaders:
        by_ver[l["version"]] += len(l["slots_ahead"])
    os.makedirs(out_dir, exist_ok=True)
    out = {"taken_at_unix": int(time.time()), "epoch": ei["epoch"], "slot": now,
           "epoch_end_slot": first + ei["slotsInEpoch"] - 1, "leaders": leaders}
    path = os.path.join(out_dir, f"survey_{ei['epoch']}.json")
    tmp = f"{path}.{os.getpid()}.tmp"  # several series run at once: write whole, then swap in
    json.dump(out, open(tmp, "w"))
    os.replace(tmp, path)
    print(f"epoch {ei['epoch']} slot {now}, {len(leaders)} leaders, saved {path}")
    print("leader slots ahead by version:", by_ver.most_common(12))
    return out


if __name__ == "__main__":
    main(*sys.argv[1:])
