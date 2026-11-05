"""Series 6 counting rules (PREREG_SERIES6.md): a run counts only when both probes landed
in one block produced by the leader we connected to."""
from itb.series6 import observation


def run(**kw):
    base = {"mode": "live", "pair": "K1", "leader": "L1", "leader_client_id": "JitoLabs", "tpu": {"error": None},
            "probes": [
                {"idx": 0, "send_rank": 1, "landed_slot": 10, "block_index": 3, "block_size": 100, "landed_leader": "L1"},
                {"idx": 1, "send_rank": 0, "landed_slot": 10, "block_index": 7, "block_size": 100, "landed_leader": "L1"}]}
    base.update(kw)
    return base


def test_counted_and_a_first():
    why, o = observation(run())
    assert why == "counted" and o["a_first"] and o["gap"] == 4 and o["class"] == "JitoLabs"


def test_other_leader_not_counted():
    r = run()
    for p in r["probes"]:
        p["landed_leader"] = "L2"
    assert observation(r) == ("landed with another leader", None)


def test_split_blocks_and_missing_probe():
    r = run()
    r["probes"][1]["landed_slot"] = 11
    assert observation(r)[0] == "different blocks"
    r["probes"][1]["landed_slot"] = None
    assert observation(r)[0] == "a probe did not land"


def test_firebam_is_firedancer_and_connection_error():
    assert observation(run(leader_client_id="FireBAM"))[1]["class"] == "Firedancer"
    assert observation(run(tpu={"error": "ConnectionError"}))[0] == "connection failed"
