#!/bin/sh
# What `docker compose up` runs. Spends nothing and needs no key.
set -e
echo "== 1/4 unit tests (spend cap, block parsing)"
python -m pytest -q tests
echo "== 2/4 report from the shipped raw data (offline)"
python -m itb.report
python -m itb.figures > /dev/null && echo "leader-level view: data/LEADERS.md, figures: docs/"
python -m itb.series5 > /dev/null && echo "series 5 tables: data/SERIES5.md"
python -m itb.clientid > /dev/null && python -m itb.landing > /dev/null && echo "checks after the fact: data/CLIENTID.md, data/LANDING.md"
python -m itb.series6 > /dev/null && echo "series 6 (direct to the leader) tables: data/SERIES6.md, figure: docs/series6.svg"
echo "== 3/4 spot-check the raw data against mainnet with getBlock (${VERIFY_SAMPLE:-10} random runs)"
python -m itb.verify --sample "${VERIFY_SAMPLE:-10}"
echo "== 4/4 dry-run: survey the live leader schedule and client versions, pick the next window of a ${DRY_VERSION:-4.3.2} leader, build, sign and simulate a burst (nothing is sent)"
python -m itb.cli --version "${DRY_VERSION:-4.3.2}" --order burst --fees 0,100000,1000000,10000000 --out data/fresh --survey-dir data/fresh
