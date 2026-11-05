# Series 6 pre-registration: the same pairs, sent straight to the leader (written 2026-11-05, before any counted series 6 probe)

This file is committed before the first counted series 6 probe. Its SHA-256 goes into a mainnet Memo transaction from our measurement key, as for series 5. The submission as it stood before this work is tagged `submission-82f96af`.

## Why

Series 1-5 sent every probe through public RPC `sendTransaction`. Our own numbers show what that path does to a pair: in series 5 the median probe sat in the middle of its block (relative position 0.51, only 14% in the first tenth), the two probes of a pair landed in one slot in 627 of 757 runs but with a median of 8 other transactions between them (adjacent, 2 or fewer apart, in only 132), and most probes landed 3-5 slots after the window opened. So for most runs the two probes did not wait in the leader's queue together, and "no rule" (Jito Labs) or "no key" (Firedancer) may describe the RPC path rather than the scheduler.

Series 6 asks one question: **when the RPC is removed, does the series 5 result change?** Series 5 is the RPC arm and stays exactly as published. Series 6 is the direct arm.

## What changes and what does not

- **Changes:** delivery. Each run opens its own unstaked QUIC connection to the `tpuQuic` address the target leader advertises in gossip (`getClusterNodes`), two slots before the window, and writes both probes back to back (send gap 0 ms, order by coin flip) half a slot before the window, then re-writes the same bytes every 100 ms until 3 slots into the window ([itb/tpu.py](itb/tpu.py), `sender._send_tpu`). No RPC is in the delivery path.
- **Same as series 5:** pairs K1 and K2 (alternating), the shared write-locked account, the coin flips, the CU limits and prices, the analysis rules (A-first share, leader-cluster bootstrap at 99.375%, the verdict thresholds, MIN_RUNS 40 and MIN_LEADERS 5 per cell, the K1+K2 key table). Both prices in both pairs are non-zero.
- **Classes:** by the leader's gossip `clientId` at run time, recorded in each run file: `JitoLabs`, `AgaveBam`, `Firedancer` (clientId Firedancer or FireBAM), `HarmonicAgave`. Harmonic validators advertise a shared ingress address; in our debug probes it forwarded to other leaders, so that cell may stay `insufficient`.

## What counts

A run counts only if **both probes landed in one block produced by the target leader** (the leader we connected to). Probes that land with another leader are reported, not counted. This is stricter than series 5, where any common block counted.

## Prediction (written before data)

- AgaveBam: same as series 5, reward/cost (A in K1 and K2).
- JitoLabs: series 5 was `no rule`. If the RPC path caused it, the direct arm shows A in both pairs (reward/cost). If it stays near 50%, the coin flip belongs to the client, not to our path.
- Firedancer: series 5 had no key. Prediction: A in both pairs (Firedancer's pack sorts by reward over cost).
- HarmonicAgave: no prediction if the cell stays `insufficient`.

Each class gets one line in the comparison: series 5 (RPC arm) verdict next to series 6 (direct arm) verdict.

## Debug probes, excluded

Before this file, 6 single probes were sent on 2026-11-05 between 08:10 and 08:40 UTC to check that a direct probe can land at all (2 landed with the target leader: JitoLabs and AgaveBam; 2 sent to Harmonic ingress addresses landed 10-12 slots later with other leaders; 2 sent with a connection closed right after the write and a slot clock read from one RPC did not land). They used the main key, one probe each, and are not in the analysis.

## Budget and stop

- Spend cap for series 6: 0.015 SOL on top of what the ledger already holds (0.02667 SOL reserved by series 1-5), enforced by the same ledger.
- Targets: 50 runs per class and pair (200 per class), stop at 2026-11-05 17:00 UTC whatever the counts. A cell below MIN_RUNS or MIN_LEADERS is reported as `insufficient` with its counts; the prediction is not withdrawn.
- If fewer than 60% of the first 15 runs have both probes in one block of the target leader, the series stops and is reported as a pilot.

## What this design still does not separate

- Our send time is our clock, not the leader's arrival time. Two probes written back to back on one QUIC connection arrive microseconds apart; we cannot see the order the leader's ingress read them.
- Unstaked QUIC gets the smallest share of a leader's stream budget. A leader under load may drop one probe of a pair; such runs do not count.
- A BAM leader's block is assembled by an outside node; we still cannot say which component did the sorting.
