# Landing rate against fee (exploratory, added 2026-11-02)

## Series 1-4: landed / sent per CU price

| CU price (micro-lamports) | landed / sent | share | 95% CI |
|---|---|---|---|
| 0 | 541 / 613 | 0.88 | 0.85-0.91 |
| 1,000 | 25 / 30 | 0.83 | 0.66-0.93 |
| 10,000 | 25 / 30 | 0.83 | 0.66-0.93 |
| 100,000 | 123 / 136 | 0.90 | 0.84-0.94 |
| 1,000,000 | 98 / 106 | 0.92 | 0.86-0.96 |
| 10,000,000 | 516 / 583 | 0.89 | 0.86-0.91 |

Lowest against highest price, Fisher's exact test: p = 0.93.

## Series 5: landed / sent per probe

| pair | probe A (600 CU) | probe B (60,000 CU) |
|---|---|---|
| K1 | 372 / 400 | 372 / 400 |
| K2 | 385 / 400 | 385 / 400 |

Runs where exactly one of the two probes landed: 0. Both landed or neither did.
