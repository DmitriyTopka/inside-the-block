#!/bin/bash
# Series 5 (PREREG_SERIES5.md): pairs K1 and K2 alternate, both probes sent together (gap 0) to one
# shared write-locked account, who-first and the endpoint by coin flip. One process per class:
#   CLASS=agave-bam PAYERS_PATH=secrets/payers_bam.json SPEND_CAP_SOL=0.0293 scripts/series5.sh
# Stops at 200 runs for the class, at 2026-11-04 06:00 UTC, or when the ledger refuses (spend cap).
cd "$(dirname "$0")/.."
: "${KEYPAIR_PATH:?}" "${PAYERS_PATH:?}" "${CLASS:?}"
OUT=data/runs5; mkdir -p $OUT
STOP=$(date -u -d "2026-11-04T06:00:00Z" +%s)
log=$(mktemp)
while :; do
  n=$(grep -l "\"target_class\": \"$CLASS\"" $OUT/live_*.json 2>/dev/null | wc -l)
  [ "$n" -ge "${RUNS:-200}" ] && { echo "done: $n runs for $CLASS"; break; }
  [ "$(date -u +%s)" -ge "$STOP" ] && { echo "stop time reached"; break; }
  pair=K1; [ $((n % 2)) -eq 1 ] && pair=K2
  python -m itb.cli --target-class "$CLASS" --pair $pair --order random --gap-ms 0 --contended --payers 2 \
    --endpoint-coin --series 5 --out $OUT --survey-dir data/survey5 --live > $log 2>&1
  rc=$?
  grep -q SpendCapExceeded $log && { echo "spend cap reached"; break; }
  [ $rc -ne 0 ] && { echo "$(date -u +%FT%TZ) run fail $CLASS: $(tail -1 $log)"; sleep 20; continue; }
  f=$(grep '^saved' $log | awk '{print $2}'); sleep 35
  echo "== $(date -u +%FT%TZ) $CLASS run $((n + 1)) $pair file $f"
  python -m itb.analyze "$f" 2>&1 | tail -3
done
cat data/ledger.json
