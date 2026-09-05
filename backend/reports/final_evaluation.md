# Final GNN Evaluation Report

## Evaluation scope

AtmoGraph uses a two-layer graph convolutional network, `RippleGCN`, to estimate node-level downstream impact scores. Current evidence measures performance on the committed synthetic dataset; it does not establish real-world forecasting accuracy.

## Dataset split

Scenarios, rather than individual rows, are shuffled with random seed 42 and divided into 70% training, 15% validation, and 15% test partitions. This prevents rows from the same scenario appearing in multiple partitions.

The test set contains 15 scenarios and produces 160 mapped node-level predictions on a canonical graph of 25 nodes and 25 relationships.

## Metrics

| Metric | RippleGCN | Training-target mean baseline | Improvement |
|---|---:|---:|---:|
| MAE | 0.009256 | 0.038189 | 75.76% |
| RMSE | 0.011282 | 0.050464 | 77.64% |
| R² | 0.948684 | Not applicable | — |

The baseline always predicts the training-split target mean (`0.276690`) and does not inspect test targets.

## Reproduction

```powershell
python -m backend.python.evaluate_gnn
```

This rewrites `gnn_test_metrics.json` and `gnn_test_predictions.csv` from the committed model and held-out split.

## Interpretation and limitations

The results show that the GNN follows the synthetic target function more closely than a constant baseline. They demonstrate internal pipeline consistency, not real commercial delay or cost forecasting. Production validation requires historical outcomes, temporal and geographical holdouts, non-graph baselines, uncertainty measurement, multiple random seeds, and much larger graphs.
