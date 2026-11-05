# Series 6: series 5 pairs sent straight to the leader over QUIC

Runs 671, counted 578 (both probes in one block of the target leader).
Not counted: a probe did not land 80, different blocks 1, landed with another leader 12.
Counted pairs: median 3 transactions between the two probes, 280 of 578 adjacent (2 or fewer apart); median relative position of the first probe in its block 0.47.

| class | pair | A first / runs | leaders | 99.375% CI (leader bootstrap) | verdict | predicted |
|---|---|---|---|---|---|---|
| AgaveBam | K1 | 70 / 73 | 44 | 0.91-1.00 | **A** | A (A under reward/cost) |
| AgaveBam | K2 | 80 / 80 | 53 | 1.00-1.00 | **A** | A (A under reward/cost) |
| JitoLabs | K1 | 29 / 65 | 26 | 0.21-0.69 | **undetermined** | A (A under reward/cost) |
| JitoLabs | K2 | 29 / 59 | 17 | 0.24-0.78 | **undetermined** | A (A under reward/cost) |
| Firedancer | K1 | 56 / 68 | 19 | 0.59-0.98 | **A** | A (A under reward/cost) |
| Firedancer | K2 | 56 / 67 | 23 | 0.61-0.99 | **A** | A (A under reward/cost) |
| HarmonicAgave | K1 | 82 / 84 | 26 | 0.93-1.00 | **A** | A (A under reward/cost) |
| HarmonicAgave | K2 | 81 / 82 | 31 | 0.94-1.00 | **A** | A (A under reward/cost) |

| class | key, direct arm (series 6) | series 5 class it compares with |
|---|---|---|
| AgaveBam | **reward/cost** | agave-bam |
| JitoLabs | **none (K1 undetermined, K2 undetermined)** | agave-jito (Jito Labs builds) |
| Firedancer | **reward/cost** | firedancer |
| HarmonicAgave | **reward/cost** | agave-jito (Harmonic builds) |

## Per validator (every leader with a counted run)

| validator | class | A first / runs | K1 | K2 |
|---|---|---|---|---|
| `DRpbCBMx` | AgaveBam | 16 / 17 | 9 / 10 | 7 / 7 |
| `GzDfKKoZ` | AgaveBam | 7 / 7 | 4 / 4 | 3 / 3 |
| `Fc6NNdS2` | AgaveBam | 6 / 7 | 5 / 6 | 1 / 1 |
| `GBQ2GvTz` | AgaveBam | 4 / 4 | 2 / 2 | 2 / 2 |
| `HpcB5Qg8` | AgaveBam | 4 / 4 | 2 / 2 | 2 / 2 |
| `AWcCdYG7` | AgaveBam | 4 / 4 | 2 / 2 | 2 / 2 |
| `BSVckjdW` | AgaveBam | 3 / 4 | 2 / 3 | 1 / 1 |
| `HnfPZDrb` | AgaveBam | 4 / 4 | 2 / 2 | 2 / 2 |
| `FWwwP9tN` | AgaveBam | 4 / 4 | 2 / 2 | 2 / 2 |
| `2GUnfxZa` | AgaveBam | 3 / 3 | 0 / 0 | 3 / 3 |
| `5Cchr1XG` | AgaveBam | 3 / 3 | 2 / 2 | 1 / 1 |
| `GSTampk6` | AgaveBam | 3 / 3 | 3 / 3 | 0 / 0 |
| `9rkJMARq` | AgaveBam | 3 / 3 | 1 / 1 | 2 / 2 |
| `58KprHKF` | AgaveBam | 3 / 3 | 1 / 1 | 2 / 2 |
| `DUND26mE` | AgaveBam | 3 / 3 | 0 / 0 | 3 / 3 |
| `5EhGYUyQ` | AgaveBam | 2 / 2 | 2 / 2 | 0 / 0 |
| `CwyVpfmf` | AgaveBam | 2 / 2 | 1 / 1 | 1 / 1 |
| `Aw5wEMXh` | AgaveBam | 2 / 2 | 1 / 1 | 1 / 1 |
| `6qwYjs5v` | AgaveBam | 2 / 2 | 1 / 1 | 1 / 1 |
| `6y7V8dL6` | AgaveBam | 2 / 2 | 0 / 0 | 2 / 2 |
| `CfgRXmp1` | AgaveBam | 2 / 2 | 0 / 0 | 2 / 2 |
| `HbidP4hp` | AgaveBam | 2 / 2 | 0 / 0 | 2 / 2 |
| `GQzMeEMw` | AgaveBam | 2 / 2 | 0 / 0 | 2 / 2 |
| `9XhmwxwW` | AgaveBam | 2 / 2 | 0 / 0 | 2 / 2 |
| `ppppoqHc` | AgaveBam | 2 / 2 | 1 / 1 | 1 / 1 |
| `HaLanfo9` | AgaveBam | 2 / 2 | 1 / 1 | 1 / 1 |
| `3s97yjq2` | AgaveBam | 2 / 2 | 2 / 2 | 0 / 0 |
| `GEM1N1UE` | AgaveBam | 2 / 2 | 1 / 1 | 1 / 1 |
| `76rcGHdP` | AgaveBam | 2 / 2 | 1 / 1 | 1 / 1 |
| `22rU5yUm` | AgaveBam | 2 / 2 | 0 / 0 | 2 / 2 |
| `3JotfSFP` | AgaveBam | 2 / 2 | 0 / 0 | 2 / 2 |
| `bkpk9KVs` | AgaveBam | 2 / 2 | 1 / 1 | 1 / 1 |
| `Ninja1sp` | AgaveBam | 2 / 2 | 0 / 0 | 2 / 2 |
| `NordEHiw` | AgaveBam | 1 / 1 | 1 / 1 | 0 / 0 |
| `CMPSSdrT` | AgaveBam | 1 / 1 | 0 / 0 | 1 / 1 |
| `GREEDkga` | AgaveBam | 1 / 1 | 1 / 1 | 0 / 0 |
| `GwHH8ciF` | AgaveBam | 1 / 1 | 0 / 0 | 1 / 1 |
| `EN5F2BU5` | AgaveBam | 1 / 1 | 1 / 1 | 0 / 0 |
| `2X7WoaXX` | AgaveBam | 1 / 1 | 0 / 0 | 1 / 1 |
| `3RXKQBRv` | AgaveBam | 1 / 1 | 0 / 0 | 1 / 1 |
| `GWJyUxzc` | AgaveBam | 1 / 1 | 1 / 1 | 0 / 0 |
| `2mDrrmhS` | AgaveBam | 1 / 1 | 0 / 0 | 1 / 1 |
| `EdFUcP2f` | AgaveBam | 1 / 1 | 1 / 1 | 0 / 0 |
| `6WgdYhhG` | AgaveBam | 1 / 1 | 1 / 1 | 0 / 0 |
| `6k1YkmTK` | AgaveBam | 1 / 1 | 0 / 0 | 1 / 1 |
| `AiDoLWFK` | AgaveBam | 1 / 1 | 1 / 1 | 0 / 0 |
| `2X5yarNU` | AgaveBam | 1 / 1 | 1 / 1 | 0 / 0 |
| `vtav4QSd` | AgaveBam | 1 / 1 | 1 / 1 | 0 / 0 |
| `MBVyz9s7` | AgaveBam | 1 / 1 | 0 / 0 | 1 / 1 |
| `7EzbSahS` | AgaveBam | 1 / 1 | 0 / 0 | 1 / 1 |
| `DViARWAW` | AgaveBam | 1 / 1 | 0 / 0 | 1 / 1 |
| `HSDTxfgr` | AgaveBam | 1 / 1 | 1 / 1 | 0 / 0 |
| `AoB1wTR7` | AgaveBam | 1 / 1 | 1 / 1 | 0 / 0 |
| `PUmpKiNn` | AgaveBam | 1 / 1 | 0 / 0 | 1 / 1 |
| `7qGNnXKW` | AgaveBam | 1 / 1 | 0 / 0 | 1 / 1 |
| `PuRposE4` | AgaveBam | 1 / 1 | 0 / 0 | 1 / 1 |
| `2Mob8FJk` | AgaveBam | 1 / 1 | 1 / 1 | 0 / 0 |
| `6TkKqq15` | AgaveBam | 1 / 1 | 1 / 1 | 0 / 0 |
| `7MTjmteQ` | AgaveBam | 1 / 1 | 0 / 0 | 1 / 1 |
| `CjmXSapt` | AgaveBam | 1 / 1 | 1 / 1 | 0 / 0 |
| `BJvrWSfo` | AgaveBam | 1 / 1 | 0 / 0 | 1 / 1 |
| `simpRo1F` | AgaveBam | 1 / 1 | 1 / 1 | 0 / 0 |
| `LeapzTYn` | AgaveBam | 1 / 1 | 0 / 0 | 1 / 1 |
| `6aDs9tUm` | AgaveBam | 1 / 1 | 1 / 1 | 0 / 0 |
| `DeXsDvvZ` | AgaveBam | 1 / 1 | 0 / 0 | 1 / 1 |
| `HLnodbYk` | AgaveBam | 1 / 1 | 1 / 1 | 0 / 0 |
| `GmCxjmjK` | AgaveBam | 1 / 1 | 0 / 0 | 1 / 1 |
| `2VKu11f8` | AgaveBam | 1 / 1 | 0 / 0 | 1 / 1 |
| `8gDfqHXZ` | AgaveBam | 1 / 1 | 1 / 1 | 0 / 0 |
| `5ejbTALc` | AgaveBam | 1 / 1 | 0 / 0 | 1 / 1 |
| `bookoVmq` | AgaveBam | 1 / 1 | 1 / 1 | 0 / 0 |
| `23SUe5fz` | AgaveBam | 1 / 1 | 0 / 0 | 1 / 1 |
| `G2TBEh2a` | AgaveBam | 1 / 1 | 0 / 0 | 1 / 1 |
| `Hj2jzpAp` | AgaveBam | 1 / 1 | 1 / 1 | 0 / 0 |
| `AfZTWYoF` | AgaveBam | 1 / 1 | 0 / 0 | 1 / 1 |
| `jzDsimGW` | AgaveBam | 1 / 1 | 1 / 1 | 0 / 0 |
| `7GkMBmtr` | AgaveBam | 1 / 1 | 0 / 0 | 1 / 1 |
| `9eGrDohd` | Firedancer | 24 / 24 | 16 / 16 | 8 / 8 |
| `JD549Hsb` | Firedancer | 13 / 24 | 8 / 13 | 5 / 11 |
| `9jxgosAf` | Firedancer | 20 / 20 | 8 / 8 | 12 / 12 |
| `FBbqKvwL` | Firedancer | 13 / 13 | 5 / 5 | 8 / 8 |
| `DNVZMSqe` | Firedancer | 4 / 5 | 1 / 2 | 3 / 3 |
| `BFmqBsaG` | Firedancer | 5 / 5 | 2 / 2 | 3 / 3 |
| `Lake8NXD` | Firedancer | 2 / 4 | 0 / 2 | 2 / 2 |
| `ALp2GdA1` | Firedancer | 4 / 4 | 2 / 2 | 2 / 2 |
| `HW4zorvt` | Firedancer | 1 / 4 | 0 / 2 | 1 / 2 |
| `BbCQMWnf` | Firedancer | 2 / 4 | 2 / 3 | 0 / 1 |
| `VQwCCSfW` | Firedancer | 3 / 3 | 2 / 2 | 1 / 1 |
| `SSmBEooM` | Firedancer | 3 / 3 | 1 / 1 | 2 / 2 |
| `Tri1F8B6` | Firedancer | 2 / 2 | 1 / 1 | 1 / 1 |
| `8AkVj5aA` | Firedancer | 2 / 2 | 2 / 2 | 0 / 0 |
| `D2RV1q6F` | Firedancer | 1 / 2 | 1 / 1 | 0 / 1 |
| `Ey3DkEVb` | Firedancer | 2 / 2 | 1 / 1 | 1 / 1 |
| `PKdLMugp` | Firedancer | 1 / 2 | 0 / 0 | 1 / 2 |
| `2XmhZKHm` | Firedancer | 2 / 2 | 1 / 1 | 1 / 1 |
| `9WzPWqKS` | Firedancer | 1 / 2 | 1 / 2 | 0 / 0 |
| `Pid6HQnM` | Firedancer | 2 / 2 | 2 / 2 | 0 / 0 |
| `RNXnAJV1` | Firedancer | 1 / 1 | 0 / 0 | 1 / 1 |
| `AHZxzLeR` | Firedancer | 1 / 1 | 0 / 0 | 1 / 1 |
| `LA1NEzry` | Firedancer | 1 / 1 | 0 / 0 | 1 / 1 |
| `4VRs6A9z` | Firedancer | 1 / 1 | 0 / 0 | 1 / 1 |
| `puffinQS` | Firedancer | 0 / 1 | 0 / 0 | 0 / 1 |
| `DEU4agzd` | Firedancer | 1 / 1 | 0 / 0 | 1 / 1 |
| `Fd7btgyS` | HarmonicAgave | 24 / 24 | 12 / 12 | 12 / 12 |
| `2fBQ7AyQ` | HarmonicAgave | 19 / 19 | 11 / 11 | 8 / 8 |
| `A1vqhA2f` | HarmonicAgave | 11 / 12 | 8 / 9 | 3 / 3 |
| `FNKgX9dY` | HarmonicAgave | 12 / 12 | 8 / 8 | 4 / 4 |
| `shftkxns` | HarmonicAgave | 7 / 8 | 4 / 5 | 3 / 3 |
| `9UM8wQ8F` | HarmonicAgave | 7 / 7 | 4 / 4 | 3 / 3 |
| `5ZqveVff` | HarmonicAgave | 6 / 6 | 2 / 2 | 4 / 4 |
| `EkvdKhUL` | HarmonicAgave | 6 / 6 | 2 / 2 | 4 / 4 |
| `FBKFWadX` | HarmonicAgave | 6 / 6 | 5 / 5 | 1 / 1 |
| `GoeW4aFK` | HarmonicAgave | 5 / 5 | 3 / 3 | 2 / 2 |
| `BtsmiEEv` | HarmonicAgave | 4 / 4 | 1 / 1 | 3 / 3 |
| `3psxMyr7` | HarmonicAgave | 4 / 4 | 2 / 2 | 2 / 2 |
| `9W3QTgBh` | HarmonicAgave | 4 / 4 | 1 / 1 | 3 / 3 |
| `AMukCLCr` | HarmonicAgave | 4 / 4 | 2 / 2 | 2 / 2 |
| `FzQqaDSt` | HarmonicAgave | 4 / 4 | 1 / 1 | 3 / 3 |
| `5RvfTSow` | HarmonicAgave | 3 / 3 | 1 / 1 | 2 / 2 |
| `Hz5aLvpK` | HarmonicAgave | 3 / 3 | 1 / 1 | 2 / 2 |
| `CW9C7HBw` | HarmonicAgave | 3 / 3 | 2 / 2 | 1 / 1 |
| `4k6wgP5W` | HarmonicAgave | 3 / 3 | 1 / 1 | 2 / 2 |
| `fishfish` | HarmonicAgave | 3 / 3 | 2 / 2 | 1 / 1 |
| `XkCriyrN` | HarmonicAgave | 3 / 3 | 2 / 2 | 1 / 1 |
| `2m1A2WM1` | HarmonicAgave | 3 / 3 | 2 / 2 | 1 / 1 |
| `DcTPJqPN` | HarmonicAgave | 1 / 2 | 0 / 0 | 1 / 2 |
| `5zm9g3zg` | HarmonicAgave | 2 / 2 | 0 / 0 | 2 / 2 |
| `2DTXh3ru` | HarmonicAgave | 2 / 2 | 0 / 0 | 2 / 2 |
| `7y5VhV4f` | HarmonicAgave | 2 / 2 | 0 / 0 | 2 / 2 |
| `G3a3iYZK` | HarmonicAgave | 2 / 2 | 2 / 2 | 0 / 0 |
| `C1ocKDYM` | HarmonicAgave | 2 / 2 | 1 / 1 | 1 / 1 |
| `HTeRsa3g` | HarmonicAgave | 2 / 2 | 0 / 0 | 2 / 2 |
| `EXckihF3` | HarmonicAgave | 2 / 2 | 0 / 0 | 2 / 2 |
| `Ex1AxFCi` | HarmonicAgave | 1 / 1 | 1 / 1 | 0 / 0 |
| `3ytgyJXp` | HarmonicAgave | 1 / 1 | 1 / 1 | 0 / 0 |
| `9PRr9k87` | HarmonicAgave | 1 / 1 | 0 / 0 | 1 / 1 |
| `5MAGJ3zS` | HarmonicAgave | 1 / 1 | 0 / 0 | 1 / 1 |
| `E1r4Psq8` | JitoLabs | 12 / 24 | 7 / 11 | 5 / 13 |
| `HEL1USMZ` | JitoLabs | 11 / 23 | 4 / 11 | 7 / 12 |
| `C8Bey3LK` | JitoLabs | 0 / 17 | 0 / 10 | 0 / 7 |
| `ana2y2Yv` | JitoLabs | 6 / 9 | 2 / 3 | 4 / 6 |
| `bitHUmbK` | JitoLabs | 5 / 5 | 4 / 4 | 1 / 1 |
| `FbYX2uN5` | JitoLabs | 4 / 5 | 1 / 2 | 3 / 3 |
| `3SkE34PV` | JitoLabs | 1 / 4 | 0 / 0 | 1 / 4 |
| `BkoS26vB` | JitoLabs | 4 / 4 | 1 / 1 | 3 / 3 |
| `A9mvukTd` | JitoLabs | 2 / 3 | 1 / 2 | 1 / 1 |
| `9gMjDS6W` | JitoLabs | 1 / 2 | 0 / 1 | 1 / 1 |
| `Gv9gguvr` | JitoLabs | 0 / 2 | 0 / 1 | 0 / 1 |
| `Ha1iade1` | JitoLabs | 0 / 2 | 0 / 0 | 0 / 2 |
| `privaEdS` | JitoLabs | 1 / 2 | 0 / 1 | 1 / 1 |
| `HM19KBHD` | JitoLabs | 1 / 2 | 1 / 2 | 0 / 0 |
| `AEHqTB2R` | JitoLabs | 0 / 2 | 0 / 2 | 0 / 0 |
| `HrpWeJSY` | JitoLabs | 1 / 2 | 1 / 2 | 0 / 0 |
| `GHQsq6bA` | JitoLabs | 0 / 1 | 0 / 1 | 0 / 0 |
| `MARiKM3t` | JitoLabs | 0 / 1 | 0 / 1 | 0 / 0 |
| `zeroT6PT` | JitoLabs | 1 / 1 | 1 / 1 | 0 / 0 |
| `DDnAqxJV` | JitoLabs | 0 / 1 | 0 / 1 | 0 / 0 |
| `MargusJe` | JitoLabs | 0 / 1 | 0 / 1 | 0 / 0 |
| `HnwMGBAw` | JitoLabs | 1 / 1 | 1 / 1 | 0 / 0 |
| `UPSCQNqd` | JitoLabs | 1 / 1 | 0 / 0 | 1 / 1 |
| `Df16xM2X` | JitoLabs | 0 / 1 | 0 / 0 | 0 / 1 |
| `5VrW7YNB` | JitoLabs | 1 / 1 | 1 / 1 | 0 / 0 |
| `capyS1je` | JitoLabs | 1 / 1 | 1 / 1 | 0 / 0 |
| `EQhTjikb` | JitoLabs | 0 / 1 | 0 / 0 | 0 / 1 |
| `SyndicAg` | JitoLabs | 0 / 1 | 0 / 1 | 0 / 0 |
| `ANC1u9sY` | JitoLabs | 1 / 1 | 1 / 1 | 0 / 0 |
| `99rG5Ahk` | JitoLabs | 1 / 1 | 1 / 1 | 0 / 0 |
| `bxrAptB5` | JitoLabs | 1 / 1 | 0 / 0 | 1 / 1 |
| `rsbp8zMH` | JitoLabs | 1 / 1 | 1 / 1 | 0 / 0 |
