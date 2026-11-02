"""Post-hoc re-grouping by gossip clientId (exploratory, added 2026-11-02).

Our classes come from the version string plus Jito's validator list. getClusterNodes
also reports a clientId (Agave, JitoLabs, AgaveBam, HarmonicAgave, Firedancer,
HarmonicFiredancer, FireBAM, Rakurai, ...), which tells apart builds that report the
same version string. We did not save it while measuring, so this module takes one
snapshot now and re-counts series 4 and 5 by it. A validator may have changed build
between our runs and the snapshot; the table of agreement with our own survey flags
says how often that shows. Planned verdicts are not touched.

  python -m itb.clientid --snapshot    # save data/clientid_<date>.json (one RPC read)
  python -m itb.clientid               # data/CLIENTID.md from the newest snapshot, offline
"""
import argparse
import collections
import glob
import json
import os
import time

from .report import series4, versions
from .figures import load_runs
from .series5 import summarize, verdict, fmt_ci
from .rpc import Rpc

ORDER = ["AgaveBam", "JitoLabs", "HarmonicAgave", "Agave", "Rakurai", "Firedancer", "HarmonicFiredancer", "FireBAM"]


def snapshot(data_dir: str) -> str:
    nodes = Rpc(os.environ.get("VERIFY_RPC_URL", "https://api.mainnet-beta.solana.com")).call("getClusterNodes")
    now = int(time.time())
    out = {"taken_at_unix": now, "source": "getClusterNodes",
           "nodes": {n["pubkey"]: {"clientId": n.get("clientId"), "version": n.get("version")} for n in nodes}}
    path = os.path.join(data_dir, f"clientid_{time.strftime('%Y-%m-%d', time.gmtime(now))}.json")
    json.dump(out, open(path, "w"), indent=0)
    print(f"{len(nodes)} nodes, saved {path}")
    return path


def load(data_dir: str) -> tuple[dict, str]:
    paths = sorted(glob.glob(os.path.join(data_dir, "clientid_*.json")))
    if not paths:
        raise SystemExit("no clientid snapshot: run python -m itb.clientid --snapshot")
    snap = json.load(open(paths[-1]))
    return {k: v["clientId"] for k, v in snap["nodes"].items()}, os.path.basename(paths[-1])


def agreement(data_dir: str, cid: dict) -> list[str]:
    """Our series 5 survey flags against today's clientId, for the leaders we counted."""
    surv = json.load(open(sorted(glob.glob(os.path.join(data_dir, "survey5", "survey_*.json")))[-1]))
    s5 = summarize(data_dir)
    counted = {o["leader"] for o in s5["obs"]}
    t = collections.Counter()
    for l in surv["leaders"]:
        if l["identity"] not in counted:
            continue
        ours = "26.x" if (l["version"] or "").startswith("26.") else "bam" if l["bam"] else "jito" if l["jito"] else "plain"
        t[(ours, cid.get(l["identity"]) or "not in gossip")] += 1
    rows = ["| our class (survey 01.11) | clientId (snapshot) | leaders |", "|---|---|---|"]
    rows += [f"| {a} | {b} | {n} |" for (a, b), n in sorted(t.items())]
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data")
    ap.add_argument("--snapshot", action="store_true")
    a = ap.parse_args()
    if a.snapshot:
        snapshot(a.data)
    cid, snap_name = load(a.data)
    key = lambda c: ORDER.index(c) if c in ORDER else len(ORDER)
    out = [f"# Series 4 and 5 re-grouped by gossip clientId (exploratory, post-hoc, snapshot `{snap_name}`)", "",
           "The clientId is today's, not the one at measurement time (2026-10-22/23 and 2026-11-01). Planned verdicts stay",
           "in REPORT.md and data/SERIES5.md. Series 5 cells use the same rules as PREREG_SERIES5.md (99.375% leader",
           "bootstrap, at least 40 counted runs and 5 leaders), applied here to groups we did not plan.", ""]

    s5 = summarize(a.data)
    groups = sorted({cid.get(o["leader"]) or "not in gossip" for o in s5["obs"]}, key=key)
    out += ["## Series 5: share of counted runs where A (600 CU) came first", "",
            "| clientId | pair | A first / counted | share | interval | leaders | verdict | key |", "|---|---|---|---|---|---|---|---|"]
    for g in groups:
        cells = {}
        for pair in ("K1", "K2"):
            sub = [o for o in s5["obs"] if (cid.get(o["leader"]) or "not in gossip") == g and o["pair"] == pair]
            cells[pair] = verdict(sub)
        v1, v2 = cells["K1"]["verdict"], cells["K2"]["verdict"]
        k = {("A", "A"): "reward/cost", ("A", "B"): "cu_price", ("B", "B"): "total fee", ("B", "A"): "contradiction"}.get((v1, v2), "-")
        for pair, v in cells.items():
            share = f"{v['share']:.2f}" if v["share"] is not None else "-"
            out.append(f"| {g} | {pair} | {v['a_first']} / {v['n']} | {share} | {fmt_ci(v['ci'])} | {v['leaders']} | {v['verdict']} | {k if pair == 'K1' else ''} |")

    ep = collections.defaultdict(lambda: [0, 0])
    for o in s5["obs"]:
        if o["endpoint"] != "both":
            e = ep[(cid.get(o["leader"]) or "not in gossip", o["pair"], o["endpoint"].split("//")[1].split(".")[0])]
            e[0] += o["a_first"]
            e[1] += 1
    out += ["", "### Series 5 by forwarding RPC (A first / counted)", "", "| clientId | pair | api.mainnet-beta | publicnode |", "|---|---|---|---|"]
    for g in groups:
        for pair in ("K1", "K2"):
            m, p = ep[(g, pair, "api")], ep[(g, pair, "solana-rpc")]
            if m[1] + p[1]:
                out.append(f"| {g} | {pair} | {m[0]} / {m[1]} | {p[0]} / {p[1]} |")

    s4 = series4(load_runs(a.data), versions(a.data))
    obs4 = [o for o in s4["obs"] if o["gap_ms"] == 0]
    out += ["", "## Series 4, 0 ms gap: dear probe first / runs (leaders)", "", "| clientId | independent | shared account |", "|---|---|---|"]
    for g in sorted({cid.get(o["leader"]) or "not in gossip" for o in obs4}, key=key):
        cell = []
        for var in ("independent", "contended"):
            sub = [o for o in obs4 if (cid.get(o["leader"]) or "not in gossip") == g and o["variant"] == var]
            cell.append(f"{sum(o['dear_first'] for o in sub)} / {len(sub)} ({len({o['leader'] for o in sub})})" if sub else "-")
        out.append(f"| {g} | {cell[0]} | {cell[1]} |")

    out += ["", "## How far today's clientId agrees with our own survey of 2026-11-01", "",
            "Series 5 counted leaders only. A BAM flag from Jito's list against clientId AgaveBam or FireBAM, and so on.", ""]
    out += agreement(a.data, cid)
    text = "\n".join(out) + "\n"
    open(os.path.join(a.data, "CLIENTID.md"), "w").write(text)
    print(text)


if __name__ == "__main__":
    main()
