# Inside the Block: how Solana leaders order transactions

We send our own small transactions into the 4-slot windows of chosen mainnet leaders, then read the produced blocks and check which of our transactions the leader placed first. Each run varies the priority fee and the moment of sending (series 5 also the compute-unit limit). If the dearer transaction lands first when it was sent later, the leader ranks by fee. If the one sent first lands first regardless of fee, the leader works in arrival order. If neither holds, we call it noise.

**In three lines.** Transactions that reach a leader tens of milliseconds apart land in the order they arrived, whatever the client. Transactions that arrive together are sorted by fee at BAM leaders (13 of 14 BAM leaders lean that way, not one busy validator), and a pre-registered follow-up shows the measure is fee per unit of requested compute, Agave's reward / cost, not the total fee. Firedancer, and Jito-Agave without BAM when both probes touch one account, lean fee-first but do not pass our pre-set threshold; plain Agave has too little data.

![Series 4 at a 0 ms gap: share of runs where the dearer probe came first, per client class](docs/series4_gap0.svg)

**Scale, honestly.** Series 1-4 ran on mainnet between 2026-10-22 13:10 and 2026-10-23 03:11 UTC, after the Alpenglow activation on 2026-10-21; we took nothing before the upgrade. 613 runs, 1,498 probes; our probes landed in blocks of 119 different leaders over all series, but the planned test (series 4) aimed at 4 validators, one per class, and the Firedancer and plain-Agave cells rest on few machines (see [data/LEADERS.md](data/LEADERS.md)). Series 5 (2026-11-01, 07:01-20:00 UTC, pre-registered in [PREREG_SERIES5.md](PREREG_SERIES5.md)) asked which fee measure the scheduler sorts by: 800 runs, 627 of them with both probes in one block. Spend reserved under the cap for all five series: 0.0266 SOL of 0.05 ([data/ledger.json](data/ledger.json)).

### Words used below

- **Client class**: the version string plus the Jito flavour. 26.10.x is Firedancer; 4.x is Agave.
- **Jito / BAM / plain**: Agave with Jito's block engine; with Jito's Block Assembly Marketplace, where an outside node assembles the block; or with neither. From Jito's public validator list at measurement time.
- **Probe**: one of our transactions, a 1-lamport transfer. **Dear / cheap**: higher / lower priority fee.
- **Shared account**: both probes of a run credit one account, so both write-lock it and the scheduler must put one after the other.
- **Holm**: a correction for testing several cells at once. **Leader-level**: counting validators, not runs, so one busy validator cannot carry a class.

## The answer in short

- **When our transactions reach a leader tens of milliseconds apart, every client class we measured keeps arrival order.** We sent cheap-first and dear-first in turn; the block followed the send order either way (4.3.2 Jito: 17 of 18 blocks, Firedancer 26.10.4: 12 of 12, 4.3.2 BAM: 11 of 13).
- **When they arrive together, BAM leaders put the higher fee first.** In series 4 (rules fixed before the data, see [ANALYSIS_PLAN.md](ANALYSIS_PLAN.md)) the dear probe came first in 21 of 23 runs with independent accounts and 25 of 29 with a shared write-locked account, across 13-14 different BAM leaders; Holm-corrected p < 0.001. Verdict: `fee`. Counted per leader instead of per run, 13 of 14 and 11 of 13 BAM leaders lean dear-first (exploratory, [data/LEADERS.md](data/LEADERS.md)).
- **Jito-Agave 4.3.2 (no BAM) shows no fee rule we could detect at a 0 ms gap** (9 of 16 independent, 18 of 25 shared account; verdict `undetermined`). With a 150 ms head start the cheap probe stayed first in 13 of 14 runs (`arrival`). That gap equals our re-send period through public RPCs, so we read it as "consistent with arrival order on the RPC path", not as a measurement at the leader's own port.
- **Firedancer 26.10.4 leans towards fee at a 0 ms gap** (13 of 17 and 12 of 15) but does not pass the planned Holm-corrected threshold: `undetermined`. Most of those runs come from one validator (`JUPiTERr`).
- **Plain Agave, 4.3.0, 26.10.3, 26.10.4 BAM and 4.5.0-alpha.2: too few observations to say anything.** We report them as `undetermined`, with counts.
- **Which fee? At BAM leaders, fee per requested compute unit.** Series 5 paired a 600 CU probe against a 60,000 CU one, at prices chosen so that CU price, total fee and Agave's reward / cost disagree. BAM put the small probe first in 87 of 104 runs (K1) and 73 of 87 (K2), over 51-61 leaders, even when it paid 1 lamport of priority fee against 120 and even when it left second. Under the pre-registered rules that reads as reward / cost. The small probe also had the smaller CU limit in both pairs, so a "small requests first" rule fits too. Jito-Agave, Firedancer and plain Agave got no key verdict; for Firedancer the result depended on which RPC carried the pair. Details: [REPORT.md](REPORT.md#series-5-which-fee-measure-does-the-scheduler-sort-by-planned-test-run-2026-11-01).

![Series 5: share of counted runs where the small-limit probe came first](docs/series5.svg)

### Per client class, series 4 at 0 ms gap (the planned test)

| client class | variant | dear first / runs | 95% CI | p (Holm) | leaders | verdict |
|---|---|---|---|---|---|---|
| 4.3.2 bam | independent | 21 / 23 | 0.73-0.98 | 0.0006 | 14 | **fee** |
| 4.3.2 bam | shared account | 25 / 29 | 0.69-0.95 | 0.0008 | 13 | **fee** |
| 4.3.2 jito | independent | 9 / 16 | 0.33-0.77 | 1.0 | 9 | undetermined |
| 4.3.2 jito | shared account | 18 / 25 | 0.52-0.86 | 0.26 | 16 | undetermined |
| 26.10.4 jito (Firedancer) | independent | 13 / 17 | 0.53-0.90 | 0.26 | 4 | undetermined |
| 26.10.4 jito (Firedancer) | shared account | 12 / 15 | 0.55-0.93 | 0.25 | 5 | undetermined |
| 4.3.2 plain | shared account | 3 / 7 | 0.16-0.75 | 1.0 | 2 | undetermined |

At 150 ms, with the cheap probe sent first: 4.3.2 jito kept arrival order in 13 of 14 runs (`arrival`). Every other cell at 150 ms has n < 10.

![Cheap probe sent first: share of runs where the dearer one still came first, by send gap](docs/series4_gap_curve.svg)

Per-validator counts for every leader with at least 3 observations: [data/RESULTS.md](data/RESULTS.md). The same data counted per leader: [data/LEADERS.md](data/LEADERS.md).

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

`scripts/series.sh` (series 2-3) and `scripts/series4.sh` (series 4) repeat this over a set of leaders, which is how we collected the data. `python -m itb.payers sweep --live` returns what is left on the payers to the main key.

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

Each probe is a 1-lamport transfer from a payer to itself, plus `SetComputeUnitLimit(600)` and `SetComputeUnitPrice`. The probes of one run use separate funded payers (`itb/payers.py`), so no two probes write-lock the same account and the scheduler can run them in parallel or in any order. That freedom could hide a fee rule, so series 4 also runs a `contended` variant: both probes transfer to one shared account (`--contended`), both write-lock it, and the scheduler has to put one after the other. The transfer amount is `1 + index`, which keeps signatures distinct. Probes differ only in priority fee, payer and send time. They use the same program and the same compute units (450 consumed), so the cost model gives them the same cost and the fee alone sets their priority.

### Competition inside the block

The 67 blocks of series 1 held 269 to 1,667 transactions. Ours are tiny, so we never compete for block space; we compete for position. We compare our probes only against each other, inside one block. `itb/blocks.py` adds context from everyone else's transactions in those 67 blocks (we did not fetch full blocks for later series): priority per cost unit (fee minus base fee, divided by `meta.costUnits`) against position, as a Spearman correlation. Since mainnet now carries v1 transactions that set the price in a `transactionConfig` field instead of a ComputeBudget instruction, we read what the ledger charged, not the instructions. This is supplementary. The claims rest on our own probes.

### Send order

Two designs, run in turn against the same leaders:

- Sequential (`asc`, `desc`, `random`): probes leave one after another, each to all endpoints before the next. The gap between consecutive probes is one RPC round trip, tens of milliseconds (recorded per probe as `sent_at`). In `asc` the cheapest goes first, so arrival order and fee order point in opposite directions: every pair that lands in one block discriminates between the two rules.
- Burst: all four probes go out in the same instant, to all endpoints in parallel. Arrival order at the leader is then down to network jitter. A leader that ranks by fee puts the dearer one first nearly every time; a leader that does not gives a coin flip.

Fees in the second series: 0, 100,000, 1,000,000 and 10,000,000 micro-lamports per CU, so 0, 60, 600 and 6,000 lamports of priority fee. The first series topped out at 60 lamports, small next to what the block's other transactions pay, so the second series covers the range where a fee-ranking scheduler has a reason to act.

Series 4 tests the gap directly. Each run sends two probes, CU price 0 and 10,000,000. A coin flip (seed from the clock, saved in the run file) picks which leaves first, and the second follows 0, 5, 20, 50 or 150 ms later. The first round goes to every endpoint without waiting for replies, so the gap is the gap we set (each probe's `sent_at` records it). At 0 ms arrival order is down to network jitter, so a systematic winner can only be the fee. At 150 ms with the cheap probe first, fee and arrival disagree. We wrote the decision rules in [ANALYSIS_PLAN.md](ANALYSIS_PLAN.md) and committed them before the first series 4 probe; the git history shows the order. We also had to extend the series after an interim look, because the planned volume could not reach the rules' n >= 10. The plan's addendum says so, and we kept the rules unchanged.

### Noise versus rule

`itb/report.py` counts, per leader and per client class:

- sequential pairs where arrival and fee disagree: how often arrival won, how often fee won, with an exact two-sided sign test;
- sequential pairs where arrival and fee agree: how often the block followed them, how often it broke both (a direct noise measure);
- burst pairs: dearer first versus cheaper first, with the same sign test.

Pairs from one run share a block, so they are not independent. For series 1-3 the tables also count one vote per block (the majority of its pairs), and the conclusions rest on that count. Series 4 sends two probes per run, so a counted run is one independent observation. Its verdicts follow the pre-registered rules: `fee` needs a dear-first share of at least 0.75 with a Holm-corrected sign test p < 0.05; `no fee rule` needs n >= 10 and a 95% interval that holds 0.5 but stays below 0.75; anything else is `undetermined`. "No rule" counts as a valid answer.

## What this design does NOT separate

- Arrival order at the leader. We know our send order, not the order in which packets reached the scheduler. A sequential pair with a fee win can mean the dearer probe overtook, or that the forwarders swapped them in transit.
- The Agave or Firedancer scheduler from the Jito or BAM layer on top of it. We tag leaders by Jito's list, which states intent. A BAM leader's own `bam_connection_rate` is below 1 for some, so a given slot may have been built without BAM.
- Scheduling batches. If the fee rule holds only among transactions that wait in the buffer together, a probe that arrives into an idle scheduler goes out at once. Series 4 varies the gap in five steps (0-150 ms), but only 0 and 150 ms have enough runs for a verdict, so we cannot place the crossover finer than "between 0 and 150 ms". Our gap is the gap at sending; the forwarders add their own jitter on the way to the leader.
- Slots within a window. We pool the 4 slots of a window, and a probe that arrives later in the window goes to a later slot.
- Validator-specific patches. Two leaders with the same version string can run different scheduler settings. Per-leader rows show this; we do not explain it.

## Raw data

- `data/runs/live_<target_slot>.json`: one file per run. Per probe: signature, payer, CU price, send rank, send time (unix), landed slot, index in that block, block size, producing leader. Per run: target leader, its version and Jito flags, order, blockhash, number of send calls, UTC time (`taken_at_unix`).
- `data/survey_<epoch>.json`: leader schedule with version, stake and Jito flags at measurement time. `data/jito_validators_2026-10-22.json`: the Jito list used to tag the first series.
- `data/blocks/<slot>.json`: every transaction of every block we landed in (signature, fee, cost units, priority per CU, tip and vote flags). `data/blocks_summary.json`: the per-block correlation.
- `data/summary.json`, `data/RESULTS.md`: generated by `python -m itb.report`, offline.
- `data/ledger.json`: lamports reserved under the spend cap.
- `data/collisions.json`: the 9 windows two parallel series both targeted (see REPORT.md, "What went wrong").
- `data/logs/`: the console logs of every series as they ran.
- Series 5: `data/runs5/` (run files, same fields plus `pair`, `target_class` and the CU limit of each probe), `data/survey5/` (its leader surveys), `data/SERIES5.md` and `data/series5_summary.json` (generated by `python -m itb.series5`). `python -m itb.verify --runs runs5` re-checks it against mainnet.

To check one claim by hand: take a signature and slot from a run file, call `getBlock(slot, {"transactionDetails": "signatures", "maxSupportedTransactionVersion": 1})` on an RPC that keeps old blocks (api.mainnet-beta.solana.com does; publicnode drops them after about ten days), and find the signature's index in the list.

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
| `scripts/series4.sh` | series 4: gap and shared-account runs |
| `ANALYSIS_PLAN.md` | series 4 decision rules, committed before the series |
| `scripts/series.sh` | the live series as we ran it |
| `itb/series5.py` | series 5 pairs, target classes, planned analysis, `data/SERIES5.md` |
| `itb/figures.py` | leader-level view of series 4 (`data/LEADERS.md`) and the SVG figures in `docs/` |
| `scripts/series5.sh` | series 5, one process per class |
| `scripts/memo_prereg.py` | writes a file's SHA-256 into a mainnet Memo |
| `PREREG_SERIES5.md` | series 5 decision rules, committed and hashed on chain before the series |

## Changes after submission

The repository as submitted on 2026-11-01 is tagged [`submitted-2026-11-01`](https://github.com/DmitriyTopka/inside-the-block/tree/submitted-2026-11-01). Everything below came later; series 1-4 data, rules and verdicts are unchanged.

- 2026-11-01: `PREREG_SERIES5.md` committed, then its SHA-256 written to mainnet in Memo transaction `4fZJtBxKx9MvTw56QAT81rd5LPWrMS6tnZVrXHJ4p9JDGByhMYuMZuXJ7U1Jc2iYb174VtBcLzYyK7KTGPackgmJ`, before any series 5 code or probe.
- 2026-11-01: the sender takes a CU limit per probe (it was a constant 600), targets a client class, and can send through one RPC picked by coin flip. Series 5 runs go to `data/runs5/` and its leader surveys to `data/survey5/`, so series 1-4 tables do not move when validators upgrade.
- 2026-11-01: leader-level re-count of series 4 and two figures (exploratory). The Jito 150 ms `arrival` verdict is now worded as what the RPC path delivers: it equals our re-send period.
- 2026-11-01: series 5 ran from 07:01 to 20:00 UTC, 800 runs, stopped at the pre-registered run count. Results in [data/SERIES5.md](data/SERIES5.md) and REPORT.md, under the rules exactly as committed. Payers swept back to the main key afterwards.
