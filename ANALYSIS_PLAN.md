# Analysis plan for series 4 (written 2026-10-22 ~19:15 UTC, before series 4 started)

We wrote this file before sending a single series 4 probe, and committed it to the repository first, so the decision rules below cannot bend to the data. The git history shows the order.

## Why series 4

Series 1-3 sent probes either one after another, tens of milliseconds apart, or all at once. Two weaknesses remain:

1. In the sequential runs the gap between probes may exceed the time a scheduler waits before it picks the next batch. If so, "sent first, landed first" says the probes met in different batches. It tells nothing about whether the leader ranks by fee.
2. Each probe has its own fee payer, so no two probes write the same account. A scheduler may then run them on different threads in parallel, and the block order need not follow the fee even if the scheduler ranks by fee.

## Design

Each run sends two probes into one leader window: a cheap one (CU price 0) and a dear one (CU price 10,000,000 micro-lamports, 6,000 lamports of priority fee).

- **Gap**: the dear and the cheap probe leave `gap` ms apart, gap in {0, 5, 20, 50, 150}.
- **Who goes first**: a coin flip per run (seed from the clock, saved in the run file). Half the runs send the dear probe first, half the cheap one.
- **Variant `independent`**: each probe is a 1-lamport transfer from its own payer to itself, as before.
- **Variant `contended`**: both probes transfer 1 lamport to the same account, so both write-lock it and the scheduler must run them one after the other.
- **Leaders**: one per client class with frequent windows: `Fd7btgyS` (4.3.2 jito), `DRpbCBMx` (4.3.2 bam), `7QQGNm3p` (4.3.2 plain), `JUPiTERr` (26.10.4 jito, Firedancer). Probes that land with another leader count for that leader's class.
- **Volume**: per leader, 5 gaps x 2 variants x 4 repetitions = 40 runs, 160 in total. Spend ~16,000 lamports a run, ~0.0026 SOL in total, under the same 0.05 SOL cap.

## What counts as an observation

A run counts only if both probes landed in the same block. One run gives one observation: did the dear probe come first? The two probes of a run are the only pair, so observations are independent across runs, apart from sharing a leader.

## Decision rules, per client class and variant

Let `n` be the number of counted runs and `k` the number where the dear probe came first.

1. **Gap 0 decides fee versus no fee.** At gap 0 arrival order is a coin flip by design (who-first is randomized and the network jitters).
   - `fee` if k/n >= 0.75 and the two-sided sign test gives p < 0.05 after Holm correction over all class x variant cells at gap 0.
   - `no fee rule` if n >= 10 and the 95% interval for k/n contains 0.5 and excludes 0.75.
   - `undetermined (n=...)` otherwise.
2. **Gaps > 0 decide arrival versus fee.** Use only runs where the cheap probe left first (fee and arrival disagree).
   - `arrival` at that gap if the cheap probe landed first in >= 75% of them, p < 0.05.
   - The **crossover gap** is the smallest gap at which the class switches from `fee` to `arrival`. We report it as "between g1 and g2 ms" and no finer.
3. **Contended versus independent.** If a class shows `fee` only in the contended variant, we report that the scheduler ranks by fee only when transactions conflict.
4. We report the number of distinct leaders behind every cell. A cell resting on one leader is a statement about that validator, not about the class.

## What we will not do

- No new statistics after looking at series 4 data. If we add an exploratory view, we label it exploratory.
- Series 1-3 stay in the report as they are, under their own headings. Series 4 does not replace them.
- We do not drop runs, except those where fewer than two probes landed in one block. That rule is fixed above.
