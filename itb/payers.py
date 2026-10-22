"""Separate fee payers, so probes in one batch never write-lock the same account.

  python -m itb.payers show
  python -m itb.payers fund  --n 4 --live     # top each payer up to --lamports (default 0.001 SOL)
  python -m itb.payers sweep --live           # everything back to the main key

Funding and sweeping move SOL, they do not spend it; only the 5000-lamport
fee of each transfer goes through the spend-cap ledger.
"""
import argparse
import base64
import json
import os

from solders.hash import Hash
from solders.keypair import Keypair
from solders.message import MessageV0
from solders.system_program import TransferParams, transfer
from solders.transaction import VersionedTransaction

from .budget import BASE_FEE_LAMPORTS, Ledger
from .rpc import Rpc

# A fee payer must stay above the rent-exempt minimum (890,880 lamports for a
# 0-byte account), so a payer funded with 1,000,000 has ~109k lamports of fees in it.
FUND_LAMPORTS = 1_000_000


def load(path: str) -> list[Keypair]:
    if not os.path.exists(path):
        return []
    return [Keypair.from_bytes(bytes(k)) for k in json.load(open(path))]


def save(path: str, kps: list[Keypair]) -> None:
    json.dump([list(bytes(k)) for k in kps], open(path, "w"))
    os.chmod(path, 0o600)


def send_transfer(rpc: Rpc, src: Keypair, dst, lamports: int) -> str:
    bh = Hash.from_string(rpc.call("getLatestBlockhash", [{"commitment": "confirmed"}])["value"]["blockhash"])
    msg = MessageV0.try_compile(src.pubkey(), [transfer(TransferParams(from_pubkey=src.pubkey(), to_pubkey=dst, lamports=lamports))], [], bh)
    tx = VersionedTransaction(msg, [src])
    return rpc.call("sendTransaction", [base64.b64encode(bytes(tx)).decode(), {"encoding": "base64", "preflightCommitment": "confirmed"}])


def balance(rpc: Rpc, pk) -> int:
    return rpc.call("getBalance", [str(pk), {"commitment": "confirmed"}])["value"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["show", "fund", "sweep"])
    ap.add_argument("--n", type=int, default=4)
    ap.add_argument("--lamports", type=int, default=FUND_LAMPORTS, help="target balance per payer")
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--cap-sol", type=float, default=float(os.environ.get("SPEND_CAP_SOL", "0.05")))
    a = ap.parse_args()
    main_kp = Keypair.from_bytes(bytes(json.load(open(os.environ["KEYPAIR_PATH"]))))
    path = os.environ.get("PAYERS_PATH", "secrets/payers.json")
    rpc = Rpc()
    kps = load(path)
    if a.cmd == "fund" and len(kps) < a.n:
        kps += [Keypair() for _ in range(a.n - len(kps))]
        save(path, kps)
    print("main", main_kp.pubkey(), balance(rpc, main_kp.pubkey()))
    for k in kps:
        print("payer", k.pubkey(), balance(rpc, k.pubkey()))
    if a.cmd == "show":
        return
    ledger = Ledger(os.path.join("data", "ledger.json"), a.cap_sol) if a.live else None
    for k in kps[: a.n] if a.cmd == "fund" else kps:
        if a.cmd == "fund":
            need = a.lamports - balance(rpc, k.pubkey())
            if need <= 0:
                continue
            src, dst, amt = main_kp, k.pubkey(), need
        else:
            amt = balance(rpc, k.pubkey()) - BASE_FEE_LAMPORTS
            if amt <= 0:
                continue
            src, dst = k, main_kp.pubkey()
        print(("SEND " if a.live else "DRY  ") + f"{a.cmd} {amt} lamports {src.pubkey()} -> {dst}")
        if a.live:
            ledger.reserve(BASE_FEE_LAMPORTS)
            print("  sig", send_transfer(rpc, src, dst, amt))


if __name__ == "__main__":
    main()
