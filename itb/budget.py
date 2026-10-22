"""Hard spend cap for live sending.

Every transaction reserves its worst-case fee before it is sent. When the next
reservation would cross the cap, the ledger refuses and the run stops. The
ledger lives in a JSON file so the cap holds across restarts.
"""
import fcntl
import json
import os

LAMPORTS_PER_SOL = 1_000_000_000
BASE_FEE_LAMPORTS = 5_000  # one signature


def max_fee_lamports(cu_limit: int, cu_price_micro: int) -> int:
    # priority fee = limit * price (micro-lamports per CU), rounded up
    return BASE_FEE_LAMPORTS + -(-cu_limit * cu_price_micro // 1_000_000)


class SpendCapExceeded(RuntimeError):
    pass


class Ledger:
    """Several series may run at once (one per rare leader), so every reservation
    takes a file lock and re-reads the total from disk before checking the cap."""

    def __init__(self, path: str, cap_sol: float):
        self.path = path
        self.cap = int(cap_sol * LAMPORTS_PER_SOL)
        self.spent = self._read()

    def _read(self) -> int:
        return json.load(open(self.path))["reserved_lamports"] if os.path.exists(self.path) else 0

    def reserve(self, lamports: int) -> None:
        with open(self.path + ".lock", "w") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            self.spent = self._read()
            if self.spent + lamports > self.cap:
                raise SpendCapExceeded(
                    f"cap {self.cap} lamports, reserved {self.spent}, next {lamports}")
            self.spent += lamports
            self._save()

    def _save(self) -> None:
        tmp = self.path + ".tmp"
        json.dump({"reserved_lamports": self.spent, "cap_lamports": self.cap}, open(tmp, "w"))
        os.replace(tmp, self.path)
