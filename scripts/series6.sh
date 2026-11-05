#!/bin/bash
# Series 6 (PREREG_SERIES6.md): series 5 pairs K1/K2, sent over our own QUIC connection straight to the
# target leader's tpuQuic, no RPC in the path. One process per gossip clientId set:
#   CLIENT=JitoLabs PAYERS_PATH=secrets/payers_s6_jito.json SPEND_CAP_SOL=0.0417 scripts/series6.sh
# Stops at 200 runs for the class, at 2026-11-05 17:00 UTC, or when the ledger refuses (spend cap).
cd "$(dirname "$0")/.."
: "${KEYPAIR_PATH:?}" "${PAYERS_PATH:?}" "${CLIENT:?}"
OUT=data/runs6; mkdir -p $OUT data/survey6
STOP=$(date -u -d "${STOP_AT:-2026-11-05T17:00:00Z}" +%s)
log=$(mktemp)
while :; do
  n=$(grep -l "\"target_class\": \"$CLIENT\"" $OUT/live_*.json 2>/dev/null | wc -l)
  [ "$n" -ge "${RUNS:-200}" ] && { echo "done: $n runs for $CLIENT"; break; }
  [ "$(date -u +%s)" -ge "$STOP" ] && { echo "stop time reached"; break; }
  pair=K1; [ $((n % 2)) -eq 1 ] && pair=K2
  python -m itb.cli --target-client "$CLIENT" --pair $pair --order random --gap-ms 0 --contended --payers 2 \
    --via tpu --series 6 --out $OUT --survey-dir data/survey6 --max-per-leader 25 --live > $log 2>&1
  rc=$?
  grep -q SpendCapExceeded $log && { echo "spend cap reached"; break; }
  [ $rc -ne 0 ] && { echo "$(date -u +%FT%TZ) run fail $CLIENT: $(tail -1 $log)"; sleep 20; continue; }
  f=$(grep '^saved' $log | awk '{print $2}'); sleep 35
  echo "== $(date -u +%FT%TZ) $CLIENT run $((n + 1)) $pair file $f"
  python -m itb.analyze "$f" 2>&1 | tail -3
done
cat data/ledger.json
