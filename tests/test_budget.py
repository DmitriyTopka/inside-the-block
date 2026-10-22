import pytest

from itb.budget import BASE_FEE_LAMPORTS, Ledger, SpendCapExceeded, max_fee_lamports


def test_fee_includes_priority_rounded_up():
    assert max_fee_lamports(600, 0) == BASE_FEE_LAMPORTS
    assert max_fee_lamports(600, 1) == BASE_FEE_LAMPORTS + 1
    assert max_fee_lamports(600, 100_000) == BASE_FEE_LAMPORTS + 60


def test_cap_refuses_and_survives_restart(tmp_path):
    p = str(tmp_path / "ledger.json")
    led = Ledger(p, cap_sol=0.00001)  # 10_000 lamports
    led.reserve(5_000)
    led.reserve(5_000)
    with pytest.raises(SpendCapExceeded):
        led.reserve(1)
    again = Ledger(p, cap_sol=0.00001)
    assert again.spent == 10_000
    with pytest.raises(SpendCapExceeded):
        again.reserve(1)


def test_two_processes_share_one_cap(tmp_path):
    p = str(tmp_path / "ledger.json")
    a, b = Ledger(p, cap_sol=0.00001), Ledger(p, cap_sol=0.00001)  # opened before either spends
    a.reserve(6_000)
    with pytest.raises(SpendCapExceeded):
        b.reserve(6_000)  # b must see a's reservation, not its stale zero
    b.reserve(4_000)
    assert Ledger(p, cap_sol=0.00001).spent == 10_000
