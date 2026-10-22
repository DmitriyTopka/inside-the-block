# Inside the Block: how Solana leaders order transactions

We send our own small transactions into the 4-slot windows of chosen mainnet leaders, then read the produced blocks and check which of our transactions the leader placed first. Each run varies two things only: the priority fee and the moment of sending. If the dearer transaction lands first when it was sent later, the leader ranks by fee. If the one sent first lands first regardless of fee, the leader works in arrival order. If neither holds, we call it noise.

All measurements ran on mainnet on 2026-10-22, after the Alpenglow activation on 2026-10-21. No measurement from before the upgrade is mixed in.

- Findings: [REPORT.md](REPORT.md)
- Generated tables, with the UTC time of every run: [data/RESULTS.md](data/RESULTS.md)
- Raw data: [data/](#raw-data)

## Run it

```bash
docker compose up
```

This needs no key and spends nothing. It runs the unit tests, rebuilds the result tables from the shipped raw data, re-fetches 10 random runs' blocks from mainnet with `getBlock` to confirm every recorded slot and in-block index, and finishes with a mainnet dry-run: it reads the live leader schedule and client versions, picks the next window of a 4.3.2 leader, then builds, signs and simulates a burst of probes without sending them.

Check every run instead of 10:

```bash
VERIFY_SAMPLE=1000 docker compose up
```

Live sending spends SOL. Put a keypair file (JSON array, as written by `solana-keygen`) in `./secrets/measure.json`, fund it, then:

```bash
docker compose run --rm itb python -m itb.payers fund --n 4 --lamports 3000000 --live
docker compose run --rm itb python -m itb.cli --leader <identity> --order burst --fees 0,100000,1000000,10000000 --payers 4 --live
docker compose run --rm itb python -m itb.analyze data/runs/live_<slot>.json
```

`scripts/series.sh` repeats this over a set of leaders, which is how we collected the data. `python -m itb.payers sweep --live` returns what is left on the payers to the main key.

## Safety: dry-run, keys, spend cap

- Without `--live` nothing reaches the network. The dry-run signs each probe and calls `simulateTransaction`. Without a key it uses a throwaway keypair, so the simulation reports `AccountNotFound`.
- Keys come only from files named by `KEYPAIR_PATH` and `PAYERS_PATH`, mounted from `./secrets` (in `.gitignore` and `.dockerignore`). The repository holds no key.
- `itb/budget.py` keeps a ledger in `data/ledger.json`. Before a probe goes out, the ledger reserves its worst-case fee: 5000 lamports base plus CU limit times CU price. A reservation that would cross `SPEND_CAP_SOL` (default 0.05) raises and stops the run. The reservation happens once per probe, even though we re-send the same signed bytes several times: a signature can land once and pay once. The ledger takes a file lock and re-reads the total on every reservation, so two series running in parallel share one cap. Tests: `tests/test_budget.py`.
- Total reserved for all our measurements: see `data/ledger.json` (the cap is 50,000,000 lamports).

## Design, and how it handles each point the bounty lists

### Leader schedule and leader types

`itb/survey.py` takes `getLeaderSchedule`, `getClusterNodes` (the `version` field) and stake from `getVoteAccounts`. It also pulls Jito's public validator list (`kobe.mainnet.jito.network/api/v1/validators`) for two flags: `running_jito` and `running_bam`. BAM, Jito's Block Assembly Marketplace, has an external node assemble the block, so we treat it as its own fork. A client class is the version string plus that flavour, for example `4.3.2 bam` or `26.10.4 jito` (26.10.x is the Firedancer version line). Every survey is saved in `data/survey_<epoch>.json`, so the class each leader had at measurement time is on record.

We first tried to spot Jito leaders by transfers to Jito tip accounts inside their blocks. That failed: every block we fetched had such transfers, Firedancer blocks included, because anyone can send a plain transfer to a tip account. We dropped the method and kept the note in `itb/survey.py`.

Leaders hold 4 consecutive slots. We aim at the first slot of a window and keep re-sending until 4 slots into it.

### The path from our backend to the executing node

Our probes go to two public RPC endpoints (`SEND_URLS`, default publicnode and api.mainnet-beta). Each endpoint forwards to the current and next leaders over QUIC on its own terms: stake-weighted QoS, its own retry policy, its own view of the schedule. A Jito or BAM leader may add a hop of its own (relayer or BAM node) before the scheduler. We see none of these hops. We see when we sent, and where the transaction landed.

What we do about it:

- We send to two forwarders at once and re-send every ~150 ms. The probe reaches the leader through whichever path is fastest. Duplicates cost nothing: the same signature cannot land twice.
- We cannot sign ahead of time, since a blockhash expires after ~150 slots and the next window may be minutes away. The sender sleeps until 10 slots before the window, takes a fresh blockhash, signs, and starts sending 3 slots before the window.
- The local slot clock interpolates between `getSlot` reads and anchors on the highest slot several endpoints report. One endpoint lagged the cluster by 2-6 slots, once by 50, which made us miss windows before this fix.
- A probe that misses the target window often lands with the next leader. The analysis attributes every block to the leader that produced it (`getSlotLeaders`), never to the one we aimed at.

### Interaction of our own transactions with each other

Each probe is a 1-lamport transfer from a payer to itself, plus `SetComputeUnitLimit(600)` and `SetComputeUnitPrice`. The probes of one run use four separate funded payers (`itb/payers.py`), so no two probes write-lock the same account and the scheduler can run them in parallel or in any order. The transfer amount is `1 + index`, which keeps signatures distinct. Probes differ only in priority fee, payer and send time. They use the same program and the same compute units (450 consumed), so the cost model gives them the same cost and the fee alone sets their priority.

### Competition inside the block

Blocks we landed in held 270 to 1,670 transactions. Ours are tiny, so we never compete for block space; we compete for position. We compare our probes only against each other, inside one block. `itb/blocks.py` adds context from everyone else's transactions in those blocks: priority per cost unit (fee minus base fee, divided by `meta.costUnits`) against position, as a Spearman correlation. Since mainnet now carries v1 transactions that set the price in a `transactionConfig` field instead of a ComputeBudget instruction, we read what the ledger charged, not the instructions. This is supplementary. The claims rest on our own probes.

### Send order

Two designs, run in turn against the same leaders:

- Sequential (`asc`, `desc`, `random`): probes leave one after another, each to all endpoints before the next. The gap between consecutive probes is one RPC round trip, tens of milliseconds (recorded per probe as `sent_at`). In `asc` the cheapest goes first, so arrival order and fee order point in opposite directions: every pair that lands in one block discriminates between the two rules.
- Burst: all four probes go out in the same instant, to all endpoints in parallel. Arrival order at the leader is then down to network jitter. A leader that ranks by fee puts the dearer one first nearly every time; a leader that does not gives a coin flip.

Fees in the second series: 0, 100,000, 1,000,000 and 10,000,000 micro-lamports per CU, so 0, 60, 600 and 6,000 lamports of priority fee. The first series topped out at 60 lamports, small next to what the block's other transactions pay, so the second series covers the range where a fee-ranking scheduler has a reason to act.

### Noise versus rule

`itb/report.py` counts, per leader and per client class:

- sequential pairs where arrival and fee disagree: how often arrival won, how often fee won, with an exact two-sided sign test;
- sequential pairs where arrival and fee agree: how often the block followed them, how often it broke both (a direct noise measure);
- burst pairs: dearer first versus cheaper first, with the same sign test.

Pairs from one run share a block, so they are not independent. We report block counts next to pair counts and read the p-values with that in mind. "No rule" counts as a valid answer: a burst result near 50/50 says so.

## What this design does NOT separate

- Arrival order at the leader. We know our send order, not the order in which packets reached the scheduler. A sequential pair with a fee win can mean the dearer probe overtook, or that the forwarders swapped them in transit.
- The Agave or Firedancer scheduler from the Jito or BAM layer on top of it. We tag leaders by Jito's list, which states intent. A BAM leader's own `bam_connection_rate` is below 1 for some, so a given slot may have been built without BAM.
- Scheduling batches. If the fee rule holds only among transactions that wait in the buffer together, a probe that arrives into an idle scheduler goes out at once. Our gap of tens of milliseconds may sit below or above that batch window, and we do not vary it in steps.
- Slots within a window. We pool the 4 slots of a window, and a probe that arrives later in the window goes to a later slot.
- Validator-specific patches. Two leaders with the same version string can run different scheduler settings. Per-leader rows show this; we do not explain it.

## Raw data

- `data/runs/live_<target_slot>.json`: one file per run. Per probe: signature, payer, CU price, send rank, send time (unix), landed slot, index in that block, block size, producing leader. Per run: target leader, its version and Jito flags, order, blockhash, number of send calls, UTC time (`taken_at_unix`).
- `data/survey_<epoch>.json`: leader schedule with version, stake and Jito flags at measurement time. `data/jito_validators_2026-10-22.json`: the Jito list used to tag the first series.
- `data/blocks/<slot>.json`: every transaction of every block we landed in (signature, fee, cost units, priority per CU, tip and vote flags). `data/blocks_summary.json`: the per-block correlation.
- `data/summary.json`, `data/RESULTS.md`: generated by `python -m itb.report`, offline.
- `data/ledger.json`: lamports reserved under the spend cap.

To check one claim by hand: take a signature and slot from a run file, call `getBlock(slot, {"transactionDetails": "signatures", "maxSupportedTransactionVersion": 1})`, and find the signature's index in the list.

## Code map

| File | What it does |
|---|---|
| `itb/survey.py` | leader schedule, client versions, Jito/BAM flags |
| `itb/sender.py` | probe building, slot clock, timed sending, dry-run simulation |
| `itb/cli.py` | one run against a version or a leader; dry-run unless `--live` |
| `itb/budget.py` | spend-cap ledger |
| `itb/payers.py` | fund, show and sweep the separate fee payers |
| `itb/analyze.py` | landed slot, block index and producing leader per probe |
| `itb/report.py` | pair statistics, `RESULTS.md` |
| `itb/blocks.py` | whole-block context: priority vs position, tip transfers |
| `itb/verify.py` | re-check the raw data against mainnet |
| `scripts/series.sh` | the live series as we ran it |
