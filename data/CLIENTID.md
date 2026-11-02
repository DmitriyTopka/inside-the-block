# Series 4 and 5 re-grouped by gossip clientId (exploratory, post-hoc, snapshot `clientid_2026-11-02.json`)

The clientId is today's, not the one at measurement time (2026-10-22/23 and 2026-11-01). Planned verdicts stay
in REPORT.md and data/SERIES5.md. Series 5 cells use the same rules as PREREG_SERIES5.md (99.375% leader
bootstrap, at least 40 counted runs and 5 leaders), applied here to groups we did not plan.

## Series 5: share of counted runs where A (600 CU) came first

| clientId | pair | A first / counted | share | interval | leaders | verdict | key |
|---|---|---|---|---|---|---|---|
| AgaveBam | K1 | 88 / 105 | 0.84 | 0.73-0.92 | 62 | A | reward/cost |
| AgaveBam | K2 | 73 / 87 | 0.84 | 0.72-0.93 | 51 | A |  |
| JitoLabs | K1 | 31 / 59 | 0.53 | 0.38-0.66 | 26 | no rule | - |
| JitoLabs | K2 | 33 / 56 | 0.59 | 0.43-0.80 | 25 | undetermined |  |
| HarmonicAgave | K1 | 31 / 44 | 0.70 | 0.49-0.92 | 21 | undetermined | - |
| HarmonicAgave | K2 | 50 / 64 | 0.78 | 0.65-0.91 | 31 | A |  |
| Agave | K1 | 16 / 24 | 0.67 | - | 11 | insufficient | - |
| Agave | K2 | 26 / 38 | 0.68 | - | 12 | insufficient |  |
| Rakurai | K1 | 1 / 1 | 1.00 | - | 1 | insufficient | - |
| Rakurai | K2 | 1 / 1 | 1.00 | - | 1 | insufficient |  |
| Firedancer | K1 | 25 / 32 | 0.78 | - | 11 | insufficient | - |
| Firedancer | K2 | 19 / 26 | 0.73 | - | 7 | insufficient |  |
| HarmonicFiredancer | K1 | 24 / 30 | 0.80 | - | 13 | insufficient | - |
| HarmonicFiredancer | K2 | 21 / 29 | 0.72 | - | 10 | insufficient |  |
| FireBAM | K1 | 5 / 6 | 0.83 | - | 5 | insufficient | - |
| FireBAM | K2 | 9 / 13 | 0.69 | - | 7 | insufficient |  |
| Unknown(57192) | K1 | 6 / 8 | 0.75 | - | 1 | insufficient | - |
| Unknown(57192) | K2 | 3 / 4 | 0.75 | - | 1 | insufficient |  |

### Series 5 by forwarding RPC (A first / counted)

| clientId | pair | api.mainnet-beta | publicnode |
|---|---|---|---|
| AgaveBam | K1 | 33 / 44 | 55 / 61 |
| AgaveBam | K2 | 35 / 46 | 38 / 41 |
| JitoLabs | K1 | 16 / 26 | 15 / 33 |
| JitoLabs | K2 | 11 / 19 | 22 / 37 |
| HarmonicAgave | K1 | 17 / 26 | 14 / 18 |
| HarmonicAgave | K2 | 21 / 32 | 29 / 32 |
| Agave | K1 | 8 / 10 | 8 / 14 |
| Agave | K2 | 11 / 14 | 15 / 24 |
| Rakurai | K1 | 0 / 0 | 1 / 1 |
| Rakurai | K2 | 0 / 0 | 1 / 1 |
| Firedancer | K1 | 8 / 12 | 17 / 20 |
| Firedancer | K2 | 6 / 13 | 13 / 13 |
| HarmonicFiredancer | K1 | 8 / 12 | 16 / 18 |
| HarmonicFiredancer | K2 | 5 / 11 | 16 / 18 |
| FireBAM | K1 | 1 / 2 | 4 / 4 |
| FireBAM | K2 | 4 / 7 | 5 / 6 |
| Unknown(57192) | K1 | 4 / 5 | 2 / 3 |
| Unknown(57192) | K2 | 2 / 2 | 1 / 2 |

## Series 4, 0 ms gap: dear probe first / runs (leaders)

| clientId | independent | shared account |
|---|---|---|
| AgaveBam | 21 / 22 (13) | 24 / 29 (13) |
| JitoLabs | 5 / 6 (4) | 8 / 10 (10) |
| HarmonicAgave | 6 / 12 (5) | 12 / 17 (8) |
| Agave | 3 / 8 (1) | 3 / 6 (1) |
| Rakurai | 1 / 1 (1) | - |
| Firedancer | 1 / 1 (1) | 0 / 1 (1) |
| HarmonicFiredancer | 9 / 14 (3) | 11 / 13 (3) |
| FireBAM | - | 1 / 1 (1) |

## How far today's clientId agrees with our own survey of 2026-11-01

Series 5 counted leaders only. A BAM flag from Jito's list against clientId AgaveBam or FireBAM, and so on.

| our class (survey 01.11) | clientId (snapshot) | leaders |
|---|---|---|
| 26.x | FireBAM | 10 |
| 26.x | Firedancer | 13 |
| 26.x | HarmonicFiredancer | 15 |
| bam | AgaveBam | 89 |
| jito | AgaveBam | 1 |
| jito | Firedancer | 1 |
| jito | HarmonicAgave | 34 |
| jito | JitoLabs | 36 |
| jito | Rakurai | 2 |
| plain | Agave | 14 |
| plain | Unknown(57192) | 1 |
