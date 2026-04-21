# Stage Trace Comparison: 632933 vs 632934

## Top-line

| Run | Label | Accuracy | Hits/Total | MRR | Misses |
|---|---|---:|---:|---:|---:|
| 632933 | H_NO_RESCUE_LOCKED | 0.691667 | 83/120 | 0.692958 | 37 |
| 632934 | H_HELDOUT_TRAIN_RESCUE | 0.900000 | 108/120 | 0.854230 | 12 |

## Miss Attribution

| Run | GT present but not top-1 | GT absent from final ranking | Dominant absence stage |
|---|---:|---:|---|
| 632933 | 29 | 37 | unknown |
| 632934 | 12 | 12 | unknown |

## Delta

- Misses changed by 25 (positive means fewer misses in run 632934 vs 632933).
