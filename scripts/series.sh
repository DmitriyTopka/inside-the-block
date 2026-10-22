#!/bin/bash
# Live series: for each target validator, REPS burst runs and REPS asc runs with
# large fee spread, each analyzed ~35 s after its window (blocks must be confirmed).
# Needs KEYPAIR_PATH and PAYERS_PATH; every send goes through the spend-cap ledger.
#   TARGETS="id1 id2" REPS=4 ORDERS="burst asc" scripts/series.sh
cd "$(dirname "$0")/.."
: "${KEYPAIR_PATH:?}" "${PAYERS_PATH:?}"
FEES=${FEES:-0,100000,1000000,10000000}
REPS=${REPS:-4}
TARGETS=${TARGETS:-$(python -m itb.survey >/dev/null && PYTHONPATH=. python scripts/pick_targets.py)}
log=$(mktemp)
for rep in $(seq 1 "$REPS"); do for order in ${ORDERS:-burst asc}; do for id in $TARGETS; do
  python -m itb.cli --leader "$id" --order $order --fees "$FEES" --payers 4 --live > $log 2>&1 \
    || { echo "run fail $id $order: $(tail -1 $log)"; continue; }
  f=$(grep '^saved' $log | awk '{print $2}'); sleep 35
  echo "== $(date -u +%FT%TZ) rep $rep order $order leader $id file $f"
  python -m itb.analyze "$f" 2>&1 | tail -6
done; done; done
cat data/ledger.json
