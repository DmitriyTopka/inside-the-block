# Series 4 seen per leader (exploratory, added 2026-11-01; planned verdicts stay in REPORT.md)

Series 4 counted one run as one observation. Runs from one validator share its configuration, so this table
re-counts gap-0 runs with the leader as the unit. Classes here are the series 5 grouping: agave-bam, agave-jito,
firedancer (26.x), agave-plain. "Lean" counts leaders whose own majority went one way (ties excluded).

| class | variant | dear first / runs | run-level 95% CI | leaders | runs of busiest leader | leader-bootstrap 95% CI | leaders leaning dear / cheap |
|---|---|---|---|---|---|---|---|
| agave-bam | independent | 21 / 23 | 0.73-0.98 | 14 | 10 | 0.79-1.00 | 13 / 1 |
| agave-bam | contended | 25 / 29 | 0.69-0.95 | 13 | 17 | 0.69-1.00 | 11 / 2 |
| agave-jito | independent | 9 / 16 | 0.33-0.77 | 9 | 8 | 0.22-0.78 | 5 / 4 |
| agave-jito | contended | 18 / 25 | 0.52-0.86 | 16 | 10 | 0.56-0.88 | 12 / 4 |
| firedancer | independent | 13 / 17 | 0.53-0.90 | 4 | 12 | 0.50-1.00 | 3 / 1 |
| firedancer | contended | 13 / 16 | 0.57-0.93 | 6 | 11 | 0.33-0.94 | 4 / 2 |
| agave-plain | independent | 3 / 8 | 0.14-0.69 | 1 | 8 | - | 0 / 1 |
| agave-plain | contended | 3 / 7 | 0.16-0.75 | 2 | 6 | 0.00-0.50 | 0 / 1 |

## Who wins when the cheap probe leaves first (both variants pooled)

| class | 0 ms | 5 ms | 20 ms | 50 ms | 150 ms |
|---|---|---|---|---|---|
| agave-bam | 26/29 | 2/4 | 3/8 | 1/2 | 1/9 |
| agave-jito | 12/18 | 1/2 | 5/7 | 0/2 | 2/21 |
| firedancer | 12/14 | 0/2 | - | 1/2 | 0/7 |
| agave-plain | 2/7 | 2/3 | 0/1 | 0/1 | 0/7 |

Cells show runs where the dear probe still landed first / runs where the cheap one was sent first.
