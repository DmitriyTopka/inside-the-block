#!/bin/bash
# Series of live probe runs: 3 orders x 3 client versions, analyzed after each run.
cd "$(dirname "$0")/.."
: "${KEYPAIR_PATH:?}" "${PAYERS_PATH:?}"
for rep in 1 2; do for order in asc desc random; do for v in 4.3.2 26.10.4 4.3.0; do
  python -m itb.cli --version $v --order $order --payers 4 --live >/dev/null 2>&1 || { echo "run fail $v $order"; continue; }
  f=$(ls -t data/runs/live_*.json | head -1); sleep 35
  echo "== rep $rep order $order version $v file $f"
  python -m itb.analyze $f 2>&1 | tail -6
done; done; done
cat data/ledger.json
