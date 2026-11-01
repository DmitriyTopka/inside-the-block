from solders.hash import Hash
from solders.keypair import Keypair

from itb.budget import max_fee_lamports
from itb.sender import build_tx, plan
from itb.series5 import KEY, PAIRS, PREDICT, class_of, fisher_two_sided, s5_class, verdict


def test_pair_reserves_match_prereg():
    k1 = sum(max_fee_lamports(l, f) for l, f in zip(PAIRS["K1"]["limits"], PAIRS["K1"]["fees"]))
    k2 = sum(max_fee_lamports(l, f) for l, f in zip(PAIRS["K2"]["limits"], PAIRS["K2"]["fees"]))
    assert (k1, k2) == (28_000, 10_121)


def test_pairs_separate_the_keys():
    def winners(pair):
        (la, lb), (fa, fb) = PAIRS[pair]["limits"], PAIRS[pair]["fees"]
        prio = [-(-l * f // 1_000_000) for l, f in ((la, fa), (lb, fb))]
        cost = [720 + 600 + l + 16_384 for l in (la, lb)]
        reward = [p + 2_500 for p in prio]
        pick = lambda x: "A" if x[0] > x[1] else "B"
        return {"cu_price": pick((fa, fb)), "total fee": pick(prio),
                "reward/cost": pick([r / c for r, c in zip(reward, cost)])}
    assert winners("K1") == PREDICT["K1"] and winners("K2") == PREDICT["K2"]
    assert {KEY[(PREDICT["K1"][k], PREDICT["K2"][k])] for k in PREDICT["K1"]} == set(PREDICT["K1"])


def test_limit_goes_into_the_transaction_and_plan():
    kp = Keypair()
    tx = build_tx(kp, 5, 1, Hash.default(), cu_limit=60_000)
    assert (60_000).to_bytes(4, "little") in bytes(tx)
    probes = plan([kp, Keypair()], [10, 20], "random", 1, [600, 60_000])
    assert [p.cu_limit for p in probes] == [600, 60_000]


def test_classes():
    assert s5_class({"version": "26.10.5", "jito": True}) == "firedancer"
    assert s5_class({"version": "4.4.0", "jito": True, "bam": True}) == "agave-bam"
    assert s5_class({"version": "4.3.2", "jito": True, "bam": False}) == "agave-jito"
    assert s5_class({"version": "4.3.2", "jito": False, "bam": False}) == "agave-plain"
    assert s5_class({"version": "0.1.1", "jito": True}) is None
    assert class_of("4.3.2 plain") == "agave-plain" and class_of("26.10.4 bam") == "firedancer"


def test_verdict_rules():
    obs = lambda k, n, leaders: [{"leader": f"L{i % leaders}", "a_first": i < k} for i in range(n)]
    assert verdict(obs(30, 39, 8))["verdict"] == "insufficient"
    assert verdict(obs(40, 40, 4))["verdict"] == "insufficient"
    assert verdict([{"leader": f"L{i % 8}", "a_first": i % 10 != 0} for i in range(80)])["verdict"] == "A"
    assert verdict([{"leader": f"L{i % 8}", "a_first": i % 10 == 0} for i in range(80)])["verdict"] == "B"
    assert verdict([{"leader": f"L{i % 7}", "a_first": i % 2 == 0} for i in range(140)])["verdict"] == "no rule"


def test_fisher():
    assert abs(fisher_two_sided(3, 1, 1, 3) - 0.4857) < 1e-3
    assert fisher_two_sided(5, 5, 5, 5) == 1.0
