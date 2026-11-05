"""Entry point. Dry-run is the default; --live sends for real under the spend cap."""
import argparse
import json
import os
import random
import time

from solders.keypair import Keypair
from solders.pubkey import Pubkey

from .budget import Ledger
from .payers import load as load_payers
from .rpc import Rpc
from .rpc import SEND_URLS
from .sender import next_window, run
from .series5 import PAIRS, leader_counts, s5_class
from .survey import main as survey


def load_keypair(path: str) -> Keypair:
    return Keypair.from_bytes(bytes(json.load(open(path))))


def dead_ingress(runs_dir: str, tries: int = 2) -> set:
    """Series 6 target selection: leaders we aimed at `tries` times without a single probe landing
    in any block at all. Their advertised ingress does not take unstaked QUIC, so more runs there
    only spend time. Decided on landing alone, never on which probe came first."""
    import glob as _g
    seen, landed = {}, set()
    for path in _g.glob(os.path.join(runs_dir, "live_*.json")):
        try:
            r = json.load(open(path))
        except (ValueError, OSError):
            continue
        seen[r.get("leader")] = seen.get(r.get("leader"), 0) + 1
        if any(p.get("landed_slot") for p in r.get("probes", [])):
            landed.add(r.get("leader"))
    return {k for k, n in seen.items() if n >= tries and k not in landed}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", help="client version string to target, e.g. 4.3.2")
    ap.add_argument("--leader", help="target one validator identity instead of a version")
    ap.add_argument("--order", choices=["asc", "desc", "random", "burst"], default="asc")
    ap.add_argument("--fees", default="0,1000,10000,100000", help="CU prices, micro-lamports")
    ap.add_argument("--limits", help="CU limit per probe, same order as --fees (default 600 each)")
    ap.add_argument("--pair", choices=sorted(PAIRS), help="series 5: sets --fees and --limits to pair K1 or K2")
    ap.add_argument("--target-class", help="series 5: aim at the next window of any leader in this class "
                    "(agave-bam, agave-jito, firedancer, agave-plain)")
    ap.add_argument("--target-client", help="series 6: aim at the next window of any leader whose gossip clientId "
                    "is in this comma list, e.g. JitoLabs or AgaveBam")
    ap.add_argument("--max-per-leader", type=int, default=25, help="series 5: skip leaders with this many runs in --out")
    ap.add_argument("--endpoint-coin", action="store_true", help="send through ONE of SEND_URLS, picked by coin flip")
    ap.add_argument("--series", type=int, help="series number, saved in the run file")
    ap.add_argument("--gap-ms", type=float, help="timed first round: this many ms between probes (series 4)")
    ap.add_argument("--contended", action="store_true",
                    help="all probes credit one shared account (SHARED_ACCOUNT, default: the main key)")
    ap.add_argument("--seed", type=int, default=None, help="shuffle seed for --order random (default: from the clock)")
    ap.add_argument("--via", choices=["rpc", "tpu"], default="rpc",
                    help="series 6: 'tpu' sends over our own QUIC connection to the leader's advertised tpuQuic")
    ap.add_argument("--live", action="store_true", help="really send (default: dry-run)")
    ap.add_argument("--cap-sol", type=float, default=float(os.environ.get("SPEND_CAP_SOL", "0.05")))
    ap.add_argument("--out", default="data/runs")
    ap.add_argument("--survey-dir", default="data", help="where the leader/version survey is saved")
    ap.add_argument("--payers", type=int, default=0, help="use N funded payers from PAYERS_PATH (0 = main key only)")
    args = ap.parse_args()
    if not (args.version or args.leader or args.target_class or args.target_client):
        ap.error("give --version, --leader or --target-class")
    if args.pair:
        args.fees = ",".join(str(f) for f in PAIRS[args.pair]["fees"])
        args.limits = ",".join(str(x) for x in PAIRS[args.pair]["limits"])

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
    if args.target_client:
        want = set(args.target_client.split(","))
        full = {k for k, n in leader_counts(args.out).items() if n >= args.max_per_leader}
        full |= dead_ingress(args.out)
        cands = [l for l in sv["leaders"] if l["slots_ahead"] and l.get("client_id") in want and l.get("tpu")
                 and l["identity"] not in full]
    elif args.target_class:
        full = {k for k, n in leader_counts(args.out).items() if n >= args.max_per_leader}
        cands = [l for l in sv["leaders"] if l["slots_ahead"] and s5_class(l) == args.target_class
                 and l["identity"] not in full]
    else:
        cands = [l for l in sv["leaders"] if l["slots_ahead"]
                 and (l["identity"] == args.leader if args.leader else l["version"] == args.version)]
    now = rpc.call("getSlot", [{"commitment": "processed"}])
    windows = [(s, l) for l in cands if (s := next_window(now, l["slots_ahead"]))]
    target, leader = min(windows, key=lambda w: w[0]) if windows else (None, None)
    if target is None:
        raise SystemExit(f"no upcoming window for {args.leader or args.version or args.target_class}")
    fees = [int(x) for x in args.fees.split(",")]
    limits = [int(x) for x in args.limits.split(",")] if args.limits else None
    if limits and len(limits) != len(fees):
        ap.error("--limits needs one value per fee")
    ledger = Ledger(os.path.join("data", "ledger.json"), args.cap_sol) if args.live else None
    payers = load_payers(os.environ.get("PAYERS_PATH", "secrets/payers.json"))[: args.payers] if args.payers else [payer]
    if not args.live and len(payers) < max(args.payers, 1):
        payers = [payer]
    elif args.payers and len(payers) < args.payers:
        raise SystemExit(f"need {args.payers} payers, have {len(payers)}: run python -m itb.payers fund")
    seed = args.seed if args.seed is not None else time.time_ns() % 2**32
    shared = Pubkey.from_string(os.environ.get("SHARED_ACCOUNT", str(payer.pubkey()))) if args.contended else None
    # endpoint coin: its own stream from the saved seed, separate from the who-first shuffle
    urls = [SEND_URLS[random.Random(seed + 1).randrange(len(SEND_URLS))]] if args.endpoint_coin else None
    res = run(rpc, payers, fees, args.order, target, ledger, args.live, seed=seed, gap_ms=args.gap_ms, shared=shared,
              limits=limits, send_urls=urls, tpu_addr=leader.get("tpu") if args.via == "tpu" else None)
    res.update({"series": args.series, "pair": args.pair, "target_class": args.target_class or args.target_client})
    res["leader_client_id"] = leader.get("client_id")
    res.update({"leader": leader["identity"], "leader_version": leader["version"], "leader_jito": leader.get("jito"),
                "leader_bam": leader.get("bam"), "taken_at_unix": int(time.time())})
    os.makedirs(args.out, exist_ok=True)
    path = os.path.join(args.out, f"{res['mode']}_{target}.json")
    if os.path.exists(path):  # two series aimed at one window: keep both files (see data/collisions.json)
        path = os.path.join(args.out, f"{res['mode']}_{target}_{os.getpid()}.json")
    json.dump(res, open(path, "w"), indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != "probes"}))
    for p in res["probes"]:
        print(p["idx"], "fee", p["cu_price"], "limit", p["cu_limit"], "rank", p["send_rank"], "sim", p["sim_err"] or "ok", p["sim_units"], p["signature"][:16])
    print("saved", path)


if __name__ == "__main__":
    main()
