# Report: transaction ordering inside Solana blocks, mainnet, 2026-10-22

All runs took place on 2026-10-22 between 13:10 and __END__ UTC, one day after the Alpenglow activation (2026-10-21). We took no measurements before the upgrade. [data/RESULTS.md](data/RESULTS.md) lists every run with its UTC time, target leader, client class, send order, fees and the blocks its probes landed in.

## Answer in short

__SHORT__

## What we measured

| | count |
|---|---|
| live runs | __RUNS__ |
| probes sent / landed / landed in the targeted 4-slot window | __PROBES__ |
| leaders whose blocks hold two or more of our probes from one run | __LEADERS__ |
| client classes (version + Jito flavour) | __CLASSES__ |
| SOL reserved under the 0.05 cap | __SOL__ |

Series, in order:

1. 13:10-15:37 UTC, 30 runs. Targets chosen by version (4.3.2, 26.10.4, 4.3.0), sequential orders `asc`, `desc`, `random`, fees 0 / 1,000 / 10,000 / 100,000 micro-lamports per CU (0 to 60 lamports of priority fee). The first 9 runs predate the slot-clock fix (see below).
2. 16:15-__S2END__ UTC, __S2RUNS__ runs. Nine fixed leaders, one per client class: `Fd7btgyS` (4.3.2 jito), `DRpbCBMx` (4.3.2 bam), `7QQGNm3p` (4.3.2 plain), `JUPiTERr` (26.10.4 jito), `9jxgosAf` (26.10.4 bam), `9rkJMARq` (4.3.0 jito), `FBbqKvwL` (26.10.3 jito), `soLStaCk` (4.5.0-alpha.2 jito), `sce3TfT8` (4.5.0-alpha.2 plain). Burst and `asc` in turn, fees 0 / 100,000 / 1,000,000 / 10,000,000 (0 to 6,000 lamports).
3. 18:55-__S3END__ UTC, __S3RUNS__ runs. The seven frequent leaders of series 2, burst only, same fees. We added it because series 2 left too few burst blocks per class for a block-level test.

## Results

__RESULTS__

## What went wrong

- **We missed the window more often than we hit it.** Of __LANDED__ landed probes, __INWIN__ landed inside the 4 targeted slots. The rest landed 1 to 8 slots later, mostly with the next leader. The analysis follows each probe to the block it actually landed in, so these probes still count, just for a different leader than we aimed at. Some classes got fewer blocks than planned because of it.
- **A lagging RPC clock.** Our first runs timed the window off one RPC's `getSlot`. Publicnode trailed the cluster by 2 to 6 slots, once by 50, so probes went out after the window had passed. Two runs at 13:10 and 13:12 UTC landed nothing, and two more at 13:23-13:24 recorded zero successful sends. One run at 15:32, after the fix, also recorded zero sends; we did not establish why. We now anchor on the highest slot several endpoints report and interpolate between reads.
- **Expired signatures.** The first version signed the probes before waiting for the window. Windows of a given client can be minutes away, and a blockhash expires after about 150 slots, so the signed probes were dead on arrival. The sender now sleeps until 10 slots before the window and signs then.
- **Fees too small in series 1.** The top fee was 60 lamports, small next to what the other transactions in those blocks pay. An "arrival wins" result at that fee level could mean the scheduler ignores fees, or that our fees were too small to matter. Series 2 and 3 raised the top fee a hundredfold to 6,000 lamports.
- **Counting pairs overstated our confidence.** Four probes in one block give up to six pairs, and those pairs share one block's conditions. Our first tables counted pairs, and one class looked like it put cheaper transactions first, 13 pairs to 5. Those 18 pairs came from 3 blocks. The tables now also count one vote per block, and the conclusions above rest on that count.
- **Jito detection by tips failed.** We planned to identify Jito leaders by transfers to Jito tip accounts inside their blocks. Every block we fetched had such transfers, Firedancer blocks included. We switched to Jito's public validator list.
- **The v1 transaction format broke block parsing.** Mainnet blocks now carry v1 transactions (in one block: 233 v1, 159 v0, 98 legacy). `getBlock` with `maxSupportedTransactionVersion: 0` returns an error for such blocks, and v1 puts the priority fee in a `transactionConfig` field. We moved to version 1 and read the fee the ledger charged.
- **A dry-run bug.** Targeting by version picked the first candidate leader by its first slot, then took that leader's next qualifying window, which could be thousands of slots away (once 8,500). It now takes the earliest qualifying window over all candidates. Live runs in series 2 and 3 targeted one leader each and were not affected.
- **The first three runs (13:10-13:12 UTC) have no send counter.** We added it afterwards. Their probes and landing data are complete.

## Limits of these conclusions

__LIMITS__
