# Stage Trace Comparison: 632922 vs 632923

## Top-line

| Run | Label | Accuracy | Hits/Total | MRR | Misses |
|---|---|---:|---:|---:|---:|
| 632922 | S1_BEST_TRACE | 0.566667 | 68/120 | 0.613690 | 52 |
| 632923 | P1_BEST_TRACE | 0.800000 | 96/120 | 0.822024 | 24 |

## Miss Attribution

| Run | GT present but not top-1 | GT absent from final ranking | Dominant absence stage |
|---|---:|---:|---|
| 632922 | 12 | 40 | filtered_by_domain_roots |
| 632923 | 6 | 18 | filtered_by_domain_roots |

## Delta

- Misses changed by 28 (positive means fewer misses in run 632923 vs 632922).
