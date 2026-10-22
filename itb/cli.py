"""Entry point. Dry-run is the default; --live sends for real under the spend cap."""
import argparse
import json
import os
import time

from solders.keypair import Keypair
from solders.pubkey import Pubkey

from .budget import Ledger
from .payers import load as load_payers
from .rpc import Rpc
from .sender import next_window, run
from .survey import main as survey


def load_keypair(path: str) -> Keypair:
    return Keypair.from_bytes(bytes(json.load(open(path))))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", help="client version string to target, e.g. 4.3.2")
    ap.add_argument("--leader", help="target one validator identity instead of a version")
    ap.add_argument("--order", choices=["asc", "desc", "random", "burst"], default="asc")
    ap.add_argument("--fees", default="0,1000,10000,100000", help="CU prices, micro-lamports")
    ap.add_argument("--gap-ms", type=float, help="timed first round: this many ms between probes (series 4)")
    ap.add_argument("--contended", action="store_true",
                    help="all probes credit one shared account (SHARED_ACCOUNT, default: the main key)")
    ap.add_argument("--seed", type=int, default=None, help="shuffle seed for --order random (default: from the clock)")
    ap.add_argument("--live", action="store_true", help="really send (default: dry-run)")
    ap.add_argument("--cap-sol", type=float, default=float(os.environ.get("SPEND_CAP_SOL", "0.05")))
    ap.add_argument("--out", default="data/runs")
    ap.add_argument("--survey-dir", default="data", help="where the leader/version survey is saved")
    ap.add_argument("--payers", type=int, default=0, help="use N funded payers from PAYERS_PATH (0 = main key only)")
    args = ap.parse_args()
    if not (args.version or args.leader):
        ap.error("give --version or --leader")

    key_path = os.environ.get("KEYPAIR_PATH")
    if key_path and os.path.exists(key_path):
        payer = load_keypair(key_path)
    elif args.live:
        raise SystemExit("--live needs KEYPAIR_PATH (mount the key file, never commit it)")
    else:  # dry-run without a key: a throwaway keypair; simulation then reports AccountNotFound
        payer = Keypair()
        print("dry-run with a throwaway key", payer.pubkey(), "(unfunded, so simulation says AccountNotFound)")
    rpc = Rpc()
    sv = survey(args.survey_dir)
    cands = [l for l in sv["leaders"] if l["slots_ahead"]
             and (l["identity"] == args.leader if args.leader else l["version"] == args.version)]
    now = rpc.call("getSlot", [{"commitment": "processed"}])
    windows = [(s, l) for l in cands if (s := next_window(now, l["slots_ahead"]))]
    target, leader = min(windows, key=lambda w: w[0]) if windows else (None, None)
    if target is None:
        raise SystemExit(f"no upcoming window for {args.leader or args.version}")
    fees = [int(x) for x in args.fees.split(",")]
    ledger = Ledger(os.path.join("data", "ledger.json"), args.cap_sol) if args.live else None
    payers = load_payers(os.environ.get("PAYERS_PATH", "secrets/payers.json"))[: args.payers] if args.payers else [payer]
    if not args.live and len(payers) < max(args.payers, 1):
        payers = [payer]
    elif args.payers and len(payers) < args.payers:
        raise SystemExit(f"need {args.payers} payers, have {len(payers)}: run python -m itb.payers fund")
    seed = args.seed if args.seed is not None else time.time_ns() % 2**32
    shared = Pubkey.from_string(os.environ.get("SHARED_ACCOUNT", str(payer.pubkey()))) if args.contended else None
    res = run(rpc, payers, fees, args.order, target, ledger, args.live, seed=seed, gap_ms=args.gap_ms, shared=shared)
    res.update({"leader": leader["identity"], "leader_version": leader["version"], "leader_jito": leader.get("jito"),
                "leader_bam": leader.get("bam"), "taken_at_unix": int(time.time())})
    os.makedirs(args.out, exist_ok=True)
    path = os.path.join(args.out, f"{res['mode']}_{target}.json")
    json.dump(res, open(path, "w"), indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != "probes"}))
    for p in res["probes"]:
        print(p["idx"], "fee", p["cu_price"], "rank", p["send_rank"], "sim", p["sim_err"] or "ok", p["sim_units"], p["signature"][:16])
    print("saved", path)


if __name__ == "__main__":
    main()
