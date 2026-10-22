from itb.blocks import block_stats, parse_tx, spearman
from itb.report import pairs, sign_test


def probe(i, fee, rank, slot, idx):
    return {"idx": i, "cu_price": fee, "send_rank": rank, "landed_slot": slot, "block_index": idx,
            "signature": f"s{i}", "sent_at": 1.0 + rank / 10, "landed_leader": "L"}


def test_sequential_pairs_split_arrival_from_fee():
    # asc: cheapest sent first. Probe 0 (fee 0) lands before probe 1 (fee 10): arrival wins.
    # Probe 2 (fee 20) lands before probe 1: fee wins. Probe 3 is in another block: skipped.
    run = {"_file": "r", "order": "asc", "probes": [
        probe(0, 0, 0, 100, 5), probe(1, 10, 1, 100, 9), probe(2, 20, 2, 100, 7), probe(3, 30, 3, 101, 0)]}
    got = {(p["fees"][0], p["fees"][1]): (p["kind"], p["winner"]) for p in pairs(run)}
    assert got == {(0, 10): ("discriminating", "arrival"), (0, 20): ("discriminating", "arrival"),
                   (10, 20): ("discriminating", "fee")}


def test_burst_pairs_count_dearer_first():
    run = {"_file": "r", "order": "burst", "probes": [probe(0, 0, 0, 100, 9), probe(1, 10, 1, 100, 3)]}
    assert [p["winner"] for p in pairs(run)] == ["dearer"]


def test_sign_test():
    assert sign_test(0, 0) == 1.0
    assert sign_test(5, 5) == 0.0625
    assert abs(sign_test(24, 28) - 2 * 24158 / 2 ** 28) < 1e-12


def v1_entry(fee, cost, keys, sigs=1):
    return {"version": 1, "meta": {"fee": fee, "costUnits": cost, "err": None, "loadedAddresses": {}},
            "transaction": {"signatures": ["x"], "message": {
                "header": {"numRequiredSignatures": sigs}, "accountKeys": keys,
                "instructions": [{"programIdIndex": len(keys) - 1}]}}}


def test_parse_tx_priority_per_cost_unit_and_tip():
    tip = "96gYZGLnJYVFmbjzopPSU6QiEV5fGqZNyN9nmNhvrZU5"
    t = parse_tx(v1_entry(5080, 9775, ["payer", tip, "11111111111111111111111111111111"]))
    assert t["prio_per_cu"] == round(80 * 1e6 / 9775)
    assert t["jito_tip"] and not t["vote"]


def test_spearman_and_block_stats():
    assert spearman([1, 2, 3, 4], [4, 3, 2, 1]) == -1.0
    txs = [{"vote": False, "prio_per_cu": p, "jito_tip": False} for p in (40, 30, 20, 10)]
    assert block_stats(txs)["spearman_index_vs_price"] == -1.0


def test_series4_rules():
    from itb.report import holm, series4

    def run(i, gap, dear_first, dear_sent_first, shared=None):
        d, c = (0, 1) if dear_first else (1, 0)
        sr = (0, 1) if dear_sent_first else (1, 0)
        return {"_file": f"r{i}", "gap_ms": gap, "shared_account": shared, "probes": [
            {"cu_price": 10_000_000, "send_rank": sr[0], "landed_slot": 5, "block_index": d, "landed_leader": "L"},
            {"cu_price": 0, "send_rank": sr[1], "landed_slot": 5, "block_index": c, "landed_leader": "L"}]}

    runs = [run(i, 0, True, i % 2 == 0) for i in range(12)]                      # dear always first at gap 0
    runs += [run(100 + i, 150, False, False) for i in range(10)]                 # cheap sent first, kept first
    runs += [{"_file": "x", "gap_ms": 0, "probes": [{"cu_price": 0, "landed_slot": None}]}]  # did not land
    out = series4(runs, {"L": "4.3.2 jito"})
    cells = {(c["gap_ms"]): c for c in out["cells"]}
    assert out["observations"] == 22
    assert cells[0]["verdict"] == "fee"
    assert cells[150]["verdict"] == "arrival"
    assert holm([0.01, 0.04, 0.03]) == [0.03, 0.06, 0.06]


def test_send_urls_are_stored_without_keys():
    from itb.sender import redact
    assert redact("https://mainnet.helius-rpc.com/?api-key=SECRET") == "https://mainnet.helius-rpc.com"
    assert redact("https://user:pw@rpc.example.com/x") == "https://rpc.example.com"
