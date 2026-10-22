from itb.analyze import analyze


class FakeRpc:
    """Two probes land in slot 100, one in 101, one never lands."""
    def call(self, method, params):
        if method == "getSignatureStatuses":
            m = {"a": 100, "b": 100, "c": 101}
            return {"value": [{"slot": m[s], "err": None} if s in m else None for s in params[0]]}
        if method == "getSlotLeaders":
            return ["L100", "L101"][: params[1]]
        if method == "getBlock":
            return {"signatures": {100: ["x", "b", "y", "a"], 101: ["c"]}[params[0]]}
        raise AssertionError(method)


def test_positions_and_order():
    run = {"target_slot": 100, "order": "asc", "probes": [
        {"idx": 0, "signature": "a", "send_rank": 0, "cu_price": 0},
        {"idx": 1, "signature": "b", "send_rank": 1, "cu_price": 10},
        {"idx": 2, "signature": "c", "send_rank": 2, "cu_price": 20},
        {"idx": 3, "signature": "d", "send_rank": 3, "cu_price": 30},
    ]}
    out = analyze(run, FakeRpc())
    by = {p["idx"]: p for p in out["probes"]}
    assert (by[0]["block_index"], by[1]["block_index"]) == (3, 1)
    assert by[3]["landed_slot"] is None
    assert out["landed_order"] == [1, 0, 2]
    assert out["in_target_window"] == [1, 0, 2]
    assert by[2]["landed_leader"] == "L101"
