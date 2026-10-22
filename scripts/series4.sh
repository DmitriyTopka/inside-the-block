#!/bin/bash
# Series 4 (ANALYSIS_PLAN.md): two probes per run, fee 0 vs 10,000,000 micro-lamports/CU,
# who-first by coin flip (--order random, clock seed), first-round gap 0/5/20/50/150 ms,
# independent payers vs one shared write-locked account. One process per leader:
#   TARGET=<identity> REPS=4 [GAPS="0 150"] scripts/series4.sh
cd "$(dirname "$0")/.."
: "${KEYPAIR_PATH:?}" "${PAYERS_PATH:?}" "${TARGET:?}"
REPS=${REPS:-4}
log=$(mktemp)
for rep in $(seq 1 "$REPS"); do for variant in independent contended; do for gap in ${GAPS:-0 5 20 50 150}; do
  extra=""; [ "$variant" = contended ] && extra="--contended"
  python -m itb.cli --leader "$TARGET" --order random --fees 0,10000000 --payers 2 --gap-ms $gap $extra --live > $log 2>&1 \
    || { echo "run fail $TARGET $variant $gap: $(tail -1 $log)"; continue; }
  f=$(grep '^saved' $log | awk '{print $2}'); sleep 35
  echo "== $(date -u +%FT%TZ) rep $rep $variant gap $gap leader $TARGET file $f"
  python -m itb.analyze "$f" 2>&1 | tail -4
done; done; done
cat data/ledger.json
