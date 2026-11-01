# Series 5 pre-registration: which fee key does the scheduler sort by? (written 2026-11-01, before any series 5 code or probe)

This file is committed before we change the sender and before the first series 5 probe. Its SHA-256 goes into a mainnet Memo transaction from our measurement key, so the timestamp does not depend on git alone. The submission as it stood on 2026-11-01 is tagged `submitted-2026-11-01`; series 1-4 data, rules and verdicts stay exactly as they are.

## Why

Series 4 found that BAM leaders put the dearer of two simultaneous probes first. Both probes had the same compute-unit limit (600), so "dearer" was dearer by every measure at once: CU price, total fee, and the Agave scheduler's priority `reward / (cost + 1)`. Series 4 cannot tell which of the three the leader sorts by. Series 5 can.

## The three candidate keys

- **cu_price**: the `SetComputeUnitPrice` value, micro-lamports per CU.
- **total fee**: what the transaction pays, base fee plus priority fee.
- **reward/cost**: Agave's scheduler priority. We read it from Agave v4.3.2 source: `core/src/transaction_priority.rs`, `calculate_priority_and_cost`, takes the reward from `calculate_reward_and_burn_fee_details` (priority fee plus the unburned 50% of the 5,000-lamport base fee, so priority + 2,500) and divides by the cost from `CostModel::calculate_cost_for_executed_transaction` called with the *requested* CU limit and the requested loaded-accounts-data-size limit. We set no data-size limit, so every probe carries the default 64 MiB, which costs about 16,384 CU (2,048 pages of 32 KiB at 8 CU). Firedancer and BAM compute priority in their own code; we did not read it, and the test does not assume they follow Agave.

## Design

Every run sends two probes, A and B, into one leader window. Both credit one shared account, so both write-lock it and the scheduler has to put one after the other. They leave together (first-round gap 0 ms); a coin flip (seed saved in the run file) picks which is sent first. A second coin flip picks the single RPC endpoint the run sends through (also saved), so we can check that the result does not depend on the forwarding path.

| pair | probe A | probe B | cu_price picks | total fee picks | reward/cost picks |
|---|---|---|---|---|---|
| K1 | limit 600, price 10,000,000 (6,000 lamports priority) | limit 60,000, price 200,000 (12,000) | A | B | A |
| K2 | limit 600, price 1,000 (1 lamport) | limit 60,000, price 2,000 (120) | B | B | A |

Approximate Agave costs: signature 720 + two write locks 600 + requested CU + 16,384 for loaded data, so ~18,300 for A and ~77,700 for B. Priorities (reward / cost): K1 A 8,500 / 18,300 = 0.46 vs B 14,500 / 77,700 = 0.19; K2 A 2,501 / 18,300 = 0.14 vs B 2,620 / 77,700 = 0.034. In both pairs A's ratio is at least twice B's, so the prediction does not hinge on the exact cost constants.

Reading the two pairs together, per client class:

| K1 winner | K2 winner | key |
|---|---|---|
| A | A | reward/cost |
| A | B | cu_price |
| B | B | total fee |
| B | A | none of the three: reported as a contradiction |

If either pair is `no rule` or `insufficient`, the class gets no key verdict, and we say which pair failed.

## Targets

Four classes, by leader at measurement time (from `getClusterNodes` and Jito's validator list): **agave-bam** (Agave, running BAM), **agave-jito** (Agave, Jito, not BAM), **firedancer** (version 26.x, any flavour), **agave-plain** (Agave without Jito). The version string of every leader is recorded. Agave 4.3.2 and 4.4.0 are both on mainnet now; the class verdict pools them, and the per-version split is exploratory.

For each class we aim at the next window of any leader in that class, with at most 25 runs per leader, so a class rests on at least 8 different leaders. Probes that land with a different leader count for the leader that produced the block, as in series 1-4.

## Volume and spend

At most 800 runs: 200 per class, K1 and K2 alternating (100 each). Worst-case reserve per run under the ledger: K1 11,000 + 17,000 = 28,000 lamports; K2 5,001 + 5,120 = 10,121 lamports. 400 x 28,000 + 400 x 10,121 = 15.25 million lamports, plus payer funding transfers and this file's Memo. The ledger already holds 11,316,610 lamports from series 1-4; we run series 5 with `SPEND_CAP_SOL=0.0293`, so the whole project stays under 0.0293 SOL of the bounty's 0.05.

Stop at whichever comes first: 800 runs, a series 5 reservation of 0.018 SOL, or 2026-11-04 06:00 UTC. While the series runs we look only at landing rates and errors, not at who came first.

## What counts

A run counts if both probes landed in one block. One counted run is one observation: did A come first? The unit for inference is the **leader** that produced the block.

## Decision rules, per class and pair

Let p be the share of counted runs where A came first.

1. `insufficient` if a class x pair cell has fewer than 40 counted runs or fewer than 5 distinct leaders.
2. Otherwise we compute a 99.375% interval for p by a cluster bootstrap over leaders (10,000 resamples of leaders with replacement, seed 5). 99.375% is 95% with a Bonferroni correction over the 8 cells.
   - `A` if p >= 0.75 and the interval's lower end is above 0.5.
   - `B` if p <= 0.25 and the interval's upper end is below 0.5.
   - `no rule` if the interval contains 0.5 and lies inside [0.25, 0.75].
   - `undetermined` otherwise.
3. Path check (reported, does not change verdicts): per class and pair, Fisher's exact test of "A first" against the endpoint used. If p < 0.05 we say the forwarding path may matter for that cell.

## What we will not do

- No change to these rules after the first probe. Anything else we compute is labelled exploratory.
- No dropping of runs other than by the counting rule above.
- If a pair behaves in a way the table does not cover, or the result contradicts series 4, we publish it as it is in REPORT.md under "What went wrong" or "Limits", not as a finding.
- Series 1-4 tables and verdicts are not edited.
