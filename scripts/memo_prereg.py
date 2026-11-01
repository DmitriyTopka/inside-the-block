"""Write the SHA-256 of a pre-registration file into a mainnet Memo transaction.

  python scripts/memo_prereg.py PREREG_SERIES5.md          # dry-run: prints the memo
  python scripts/memo_prereg.py PREREG_SERIES5.md --live   # sends it (5,000 lamports, under the ledger cap)
"""
import base64
import hashlib
import json
import os
import sys

from solders.hash import Hash
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.message import MessageV0
from solders.pubkey import Pubkey
from solders.transaction import VersionedTransaction

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from itb.budget import BASE_FEE_LAMPORTS, Ledger  # noqa: E402
from itb.rpc import Rpc  # noqa: E402

MEMO_PROGRAM = Pubkey.from_string("MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr")


def main(path: str, live: bool):
    digest = hashlib.sha256(open(path, "rb").read()).hexdigest()
    memo = f"inside-the-block {os.path.basename(path)} sha256 {digest}"
    print(memo)
    if not live:
        return
    kp = Keypair.from_bytes(bytes(json.load(open(os.environ["KEYPAIR_PATH"]))))
    rpc = Rpc()
    Ledger(os.path.join("data", "ledger.json"), float(os.environ.get("SPEND_CAP_SOL", "0.05"))).reserve(BASE_FEE_LAMPORTS)
    bh = Hash.from_string(rpc.call("getLatestBlockhash", [{"commitment": "confirmed"}])["value"]["blockhash"])
    ix = Instruction(MEMO_PROGRAM, memo.encode(), [AccountMeta(kp.pubkey(), True, False)])
    tx = VersionedTransaction(MessageV0.try_compile(kp.pubkey(), [ix], [], bh), [kp])
    sig = rpc.call("sendTransaction", [base64.b64encode(bytes(tx)).decode(), {"encoding": "base64", "preflightCommitment": "confirmed"}])
    print("memo signature", sig)


if __name__ == "__main__":
    main(sys.argv[1], "--live" in sys.argv)
